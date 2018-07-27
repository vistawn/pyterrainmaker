# -*- coding: utf-8 -*-

#
# TileScheme
# Generate tiling scheme
#

from __future__ import print_function
import os
import sys
from osgeo import gdal
import multiprocessing

import GlobalGeodetic
from TerrainBundle import TerrainBundle

if sys.version_info >= (3, 0):
    xrange = range


class TileScheme(object):

    def __init__(self, input_tif):
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
        self.is_compact = False

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

    def __find_source_band(self, in_res):
        find_band_index = 0
        while find_band_index + 1 in self.__resolutions and self.__resolutions[find_band_index] < in_res:
            find_band_index += 1
        return self.__source_bands[find_band_index]

    def __write_config(self, loc):
        with open(os.path.join(loc, 'layer.json'), 'w') as f:
            f.write(
                """{
                  "tilejson": "2.1.0",
                  "format": "heightmap-1.0",
                  "version": "1.0.0",
                  "scheme": "tms",
                  "tiles": ["{z}/{x}/{y}.terrain"]
                }""")

    def generate_scheme(self, is_compact):
        self.is_compact = is_compact
        has_child = False
        for level in sorted(self.__levels.keys(), reverse=True):
            self.generate_bundles_by_level(level, has_child)
            has_child = True

    def generate_bundles_by_level(self, level, has_child):
        res = self.__levels[level]
        gg = GlobalGeodetic.GlobalGeodetic(True, 64)
        left_tx, top_ty = gg.LonLatToTile(self.__minx, self.__maxy, level)
        right_tx, bottom_ty = gg.LonLatToTile(self.__maxx, self.__miny, level)
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

    def make_bundles(self, out_loc, thread_count=multiprocessing.cpu_count()):
        self.__write_config(out_loc)
        sys.stdout.write("0")
        sys.stdout.flush()
        sum = len(self.bundles) + 0.0
        while len(self.bundles) > 0:
            bundle = self.bundles.pop(0)
            bundle.write_tiles(out_loc)
            del bundle
            sys.stdout.write('...{0:.0f}'.format((1.0 - len(self.bundles)/sum)*100))
            sys.stdout.flush()



