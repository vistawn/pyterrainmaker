# -*- coding: utf-8 -*-

#
# TileScheme
# Generate tiling scheme
#

from __future__ import print_function
import os
import sys
import shutil
from osgeo import gdal
import multiprocessing
import json

import GlobalGeodetic
from TerrainBundle import TerrainBundle

if sys.version_info >= (3, 0):
    xrange = range


class TileScheme(object):

    def __init__(self, input_tif, is_storage_compact):
        """
        create tiling scheme
        :param input_tif: input GeoTiff file
        """

        self.bundles = []
        self.__ds = gdal.Open(input_tif)
        if self.__ds is None:
            raise Exception('Open input TIFF file failed')

        # one bundle has 128*128 tiles
        self.bundle_size = 128

        # bundle mode
        # explode: save each tile as single .terrain file
        # compact: save all tiles in one bundle as .bundle file
        self.is_compact = is_storage_compact

        self.__tile_source_bands = {}
        # data extent
        self.__minx = self.__maxy = self.__maxx = self.__miny = None

        self.source_no_data = None
        self.out_no_data = None

        # input Tif file's resolution and bands
        self.__resolutions = {}
        self.__source_bands = {}

        # TMS levels
        self.__levels = {}

        self.__avaliables = {}

        self.__get_tif_info()
        self.__compute_levels()

    def __get_tif_info(self):
        cols = self.__ds.RasterXSize
        rows = self.__ds.RasterYSize
        trans = self.__ds.GetGeoTransform()
        self.__minx = trans[0]
        self.__maxy = trans[3]
        ori_resolution = trans[1]
        self.__resolutions[0] = ori_resolution
        self.__maxx = self.__minx + cols * ori_resolution
        self.__miny = self.__maxy - rows * ori_resolution

        band = self.__ds.GetRasterBand(1)
        self.__source_bands[0] = band
        self.source_no_data = band.GetNoDataValue()
        band_count = band.GetOverviewCount()
        for x in xrange(0, band_count):
            band_ov = band.GetOverview(x)
            self.__source_bands[x + 1] = band_ov
            self.__resolutions[x + 1] = ori_resolution * cols / band_ov.XSize

    def __compute_levels(self):
        next_res = 180.0 / 64
        next_level = 0
        self.__levels[next_level] = next_res
        while next_res > self.__resolutions[0]:
            next_res = next_res / 2
            next_level += 1
            self.__levels[next_level] = next_res
        self.__max_level = next_level

    def __find_source_band(self, in_res):
        find_band_index = 0
        while find_band_index + 1 in self.__resolutions and self.__resolutions[find_band_index] < in_res:
            find_band_index += 1
        return self.__source_bands[find_band_index]

    def __write_bundle_info(self, loc):
        with open(os.path.join(loc, 'bundle.json'), 'w') as f:
            extent = {
                'x_min': self.__minx,
                'x_max': self.__maxx,
                'y_min': self.__miny,
                'y_max': self.__maxy
            }
            info = {
                'width': 128,
                'height': 128,
                'extent': extent
            }
            json.dump(info, f)

    def __gen_avaliables(self):
        avaliables = []
        for x in xrange(0, self.__max_level + 1):
            if x == 0:
                avaliables.append([{"startX": 0, "endX": 1, "startY": 0, "endY": 0}])
            else:
                avaliables.append(self.__avaliables[x])
        return avaliables

    def __write_config(self, loc, decode_type):
        layer_json = {
            "tilejson": "2.1.0",
            "version": "1.0.0",
            "scheme": "tms",
            "tiles": ["{z}/{x}/{y}.terrain"],
            "bounds": [self.__minx, self.__miny, self.__maxx, self.__maxy],
            "available": self.__gen_avaliables(),
            "minzoom": 0,
            "maxzoom": self.__max_level
        }
        if decode_type == 'heightmap':
            layer_json["format"] = "heightmap-1.0"
        else:
            layer_json["format"] = "quantized-mesh-1.0"
            layer_json["extensions"] = ["watermask", "octvertexnormals"]

        self.write_layer_json(loc, layer_json)

    @staticmethod
    def write_layer_json(loc, layer_json):
        with open(os.path.join(loc, 'layer.json'), 'w') as f:
            f.write(json.dumps(layer_json, indent=4))

    def generate_scheme(self):
        has_child = False
        for level in sorted(self.__levels.keys(), reverse=True):
            self.generate_bundles_by_level(level, has_child)
            has_child = True

    def generate_bundles_by_level(self, level, has_child):
        res = self.__levels[level]
        gg = GlobalGeodetic.GlobalGeodetic(True, 64)
        left_tx, top_ty = gg.LonLatToTile(self.__minx, self.__maxy, level)
        right_tx, bottom_ty = gg.LonLatToTile(self.__maxx, self.__miny, level)
        self.__avaliables[level] = [{"startX": left_tx, "endX": right_tx, "startY": bottom_ty, "endY": top_ty}]
        source_band = self.__find_source_band(res)
        top_ty1 = top_ty
        while left_tx <= right_tx:
            while top_ty >= bottom_ty:
                g_bundle = TerrainBundle(source_band, self.bundle_size, self.is_compact)
                g_bundle.level = level
                g_bundle.resolution = res
                g_bundle.from_tile = (left_tx, top_ty)
                g_bundle.no_data = self.source_no_data
                g_bundle.out_no_data = self.out_no_data
                g_bundle.has_next_level = has_child
                g_bundle.data_band = source_band
                g_bundle.source_range = (self.__minx, self.__miny, self.__maxx, self.__maxy)
                self.bundles.append(g_bundle)
                top_ty -= self.bundle_size
            top_ty = top_ty1
            left_tx += self.bundle_size

    @staticmethod
    def fill_zero_level(out_loc, decode_type):
        base_path = os.path.join(out_loc, '0')
        first_path = os.path.join(base_path, '0')
        second_path = os.path.join(base_path, '1')
        first_t = os.path.join(base_path, '0', '0.terrain')
        second_t = os.path.join(base_path, '1', '0.terrain')

        module_dir = os.path.abspath(os.path.join(__file__, '..'))

        temp_0 = os.path.join(module_dir, 'data', 'mesh000.terrain')
        temp_1 = os.path.join(module_dir, 'data', 'mesh010.terrain')
        if decode_type == 'heightmap':
            temp_0 = os.path.join(module_dir, 'data', 'blank_heightmap.terrain')
            temp_1 = os.path.join(module_dir, 'data', 'blank_heightmap.terrain')
        if not os.path.exists(first_t):
            if not os.path.exists(first_path):
                os.mkdir(first_path)
            shutil.copyfile(temp_0, first_t)
        if not os.path.exists(second_t):
            if not os.path.exists(second_path):
                os.mkdir(second_path)
            shutil.copyfile(temp_1, second_t)

    def make_bundles(self, out_loc, decode_type='heightmap', thread_count=multiprocessing.cpu_count()):
        self.__write_config(out_loc, decode_type)
        if self.is_compact:
            self.__write_bundle_info(out_loc)

        print('Start generating tiles...')
        total = len(self.bundles)
        while len(self.bundles) > 0:
            bundle = self.bundles.pop(0)
            bundle.write_tiles(out_loc, decode_type)
            del bundle
            sys.stdout.flush()
            remains = len(self.bundles) + 0.0
            print('  {0:.0f}/{1} ({2:.0f}%)'.format(total - remains, total, (1.0 - remains/total)*100), end='\r')

        self.fill_zero_level(out_loc, decode_type)



