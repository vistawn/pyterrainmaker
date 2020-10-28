
#
# TerrainBundle Class
# multiple terrain tiles as processing unit.
# default is 128 * 128
#

import os
import numpy as np
from osgeo import gdalconst
from osgeo import gdal
import struct

from GlobalGeodetic import GlobalGeodetic
from TerrainTile import TerrainTile

import sys
if sys.version_info >= (3, 0):
    xrange = range


def make_child_flags(N, S, E, W):
    # Cesium format neighbor tiles flags
    HAS_SW = 0x01
    HAS_SE = 0x02
    HAS_NW = 0x04
    HAS_NE = 0x08

    NB_FLAGS = 0x00

    if N & W:
        NB_FLAGS = NB_FLAGS | HAS_NW
    if N & E:
        NB_FLAGS = NB_FLAGS | HAS_NE
    if S & W:
        NB_FLAGS = NB_FLAGS | HAS_SW
    if S & E:
        NB_FLAGS = NB_FLAGS | HAS_SE

    return NB_FLAGS


class TerrainBundle(object):

    def __init__(self, in_source_band, bundle_size, is_compact):
        self.bundle_size = bundle_size
        self.data_band = in_source_band
        self.is_compact = is_compact
        self.__tiles = []
        self.has_next_level = True
        self.level = 0
        self.resolution = None
        self.from_tile = None
        self.source_range = None
        self.data_band = None
        self.no_data = None
        self.out_no_data = None
        self.bundle_array = None
        self.fill_raster = None

    def calculate_tiles(self):
        cols = self.data_band.XSize
        rows = self.data_band.YSize
        (data_min_x, data_min_y, data_max_x, data_max_y) = self.source_range
        band_res = (data_max_x - data_min_x) / cols
        gg = GlobalGeodetic(True, 64)
        tile_x = self.from_tile[0]
        tile_y = self.from_tile[1]
        tile_max_x = tile_x
        tile_min_y = tile_y
        (t_min_y, t_min_x, t_max_y, t_max_x) = gg.TileLatLonBounds(tile_x, tile_y, self.level)

        for index_x in xrange(0, self.bundle_size):
            tile_x = self.from_tile[0] + index_x
            for index_y in xrange(0, self.bundle_size):
                tile_y = self.from_tile[1] - index_y
                tile_range = (t_min_y, t_min_x, t_max_y, t_max_x) = gg.TileLatLonBounds(tile_x, tile_y, self.level)

                if self.is_in_source_range(t_min_x, t_min_y, t_max_x, t_max_y):
                    tile_max_x = max(tile_max_x, tile_x)
                    tile_min_y = min(tile_min_y, tile_y)
                    if self.has_next_level:
                        flag = self.calc_tile_flag(tile_range)
                    else:
                        flag = 0x00
                    tile = TerrainTile(index_x * 64, index_y*64, flag, (t_min_x, t_min_y, t_max_x, t_max_y), self.resolution)
                    tile.x = tile_x
                    tile.y = tile_y

                    if self.level < 6:
                        tile.fake = True

                    self.__tiles.append(tile)

        if self.level < 6:
            return

        bundle_tiles_x = tile_max_x - self.from_tile[0] + 1
        bundle_tiles_y = self.from_tile[1] - tile_min_y + 1
        bundle_px_width = bundle_tiles_x * 64 + 1
        bundle_px_height = bundle_tiles_y * 64 + 1

        # first range
        (f_min_y, f_min_x, f_max_y, f_max_x) = gg.TileLatLonBounds(self.from_tile[0], self.from_tile[1], self.level)
        # bundle_range
        (b_min_y, b_min_x, b_max_y, b_max_x) = (
            f_min_y - (f_max_y - f_min_y) * (bundle_tiles_y - 1),
            f_min_x,
            f_max_y,
            f_max_x + (f_max_x - f_min_x) * (bundle_tiles_x - 1)
        )

        b_px_min_x = int((b_min_x - data_min_x) / band_res)
        b_px_max_x = int((b_max_x - data_min_x) / band_res) + 1
        b_px_min_y = int((data_max_y - b_max_y) / band_res)
        b_px_max_y = int((data_max_y - b_min_y) / band_res) + 1

        shift_left = shift_right = shift_top = shift_bottom = 0
        if b_px_min_x < 0:
            shift_left = abs(b_px_min_x)
            b_px_min_x = 0
        if b_px_max_x >= cols:
            shift_right = b_px_max_x - cols
            b_px_max_x = cols
        if b_px_min_y < 0:
            shift_top = abs(b_px_min_y)
            b_px_min_y = 0
        if b_px_max_y >= rows:
            shift_bottom = b_px_max_y - rows
            b_px_max_y = rows
        w_x = b_px_max_x - b_px_min_x
        w_y = b_px_max_y - b_px_min_y

        tile_array = self.data_band.ReadAsArray(b_px_min_x, b_px_min_y, w_x, w_y)

        fill_blank_value = self.out_no_data
        if self.out_no_data is not None and self.no_data is not None:
            fill_blank_value = self.out_no_data
            np.place(tile_array, tile_array == self.no_data, self.out_no_data)

        shift_obj = (shift_obj_v, shift_obj_h) = ((shift_top, shift_bottom), (shift_left, shift_right))

        if shift_obj != ((0, 0), (0, 0)):
            tile_array = np.lib.pad(tile_array, shift_obj, 'constant', constant_values=[fill_blank_value])

        if self.fill_raster and self.level >= 6:
            zero_rows, zero_cols = np.where(tile_array == 0)
            for i in xrange(len(zero_cols)):
                cell_row = zero_rows[i]
                cell_col = zero_cols[i]
                lon = band_res * cell_col + b_min_x
                lat = b_max_y - band_res * cell_row
                fill_value = self.fill_raster.get_height(lon, lat)
                tile_array[cell_row][cell_col] = fill_value

        (m_rows, m_cols) = tile_array.shape

        mem_drv = gdal.GetDriverByName('MEM')

        dst_bundle_ds = mem_drv.Create('', bundle_px_width, bundle_px_height, 1, gdalconst.GDT_Float32)

        if m_cols == bundle_px_width and m_rows == bundle_px_height:
            dst_bundle_ds.WriteRaster(0, 0, m_cols, m_rows, np.frombuffer(tile_array, tile_array.dtype).tostring())
            self.bundle_array = np.array(dst_bundle_ds.GetRasterBand(1).ReadAsArray(0, 0, bundle_px_width, bundle_px_height))
        else:
            prj_ds = mem_drv.Create('', m_cols, m_rows, 1, gdalconst.GDT_Float32)
            prj_band = prj_ds.GetRasterBand(1)
            prj_band.WriteArray(tile_array, 0, 0)
            dst_bundle_ds.SetGeoTransform((0.0, 1.0, 0.0, 0.0, 0.0, 1.0))
            prj_ds.SetGeoTransform(
                (0.0, bundle_px_width / float(m_cols), 0.0, 0.0, 0.0, bundle_px_height / float(m_rows)))
            res = gdal.ReprojectImage(prj_ds, dst_bundle_ds, None, None, eResampleAlg=gdalconst.GRIORA_NearestNeighbour)
            if res != 0:
                self.error("ReprojectImage() failed on %s, error %d" % ('aa', res))
            else:
                self.bundle_array = np.array(dst_bundle_ds.GetRasterBand(1).ReadAsArray(0, 0, bundle_px_width, bundle_px_height))
            
            del prj_ds

        del tile_array
        del dst_bundle_ds

    def calc_tile_flag(self, bound):
        (t_min_y, t_min_x, t_max_y, t_max_x) = bound
        N = S = W = E = False
        mid_x = (t_min_x + t_max_x) / 2
        mid_y = (t_min_y + t_max_y) / 2
        s_min_x, s_min_y, s_max_x, s_max_y = self.source_range
        if s_min_x <= mid_x and s_max_x >= t_min_x:
            W = True
        if s_min_x <= t_max_x and s_max_x >= mid_x:
            E = True
        if s_min_y <= t_max_y and s_max_y >= mid_y:
            N = True
        if s_min_y <= mid_y and s_max_y >= t_min_y:
            S = True

        return make_child_flags(N, S, E, W)

    def is_in_source_range(self, min_x, min_y, max_x, max_y):
        s_min_x, s_min_y, s_max_x, s_max_y = self.source_range
        if min_x > s_max_x or max_x < s_min_x or min_y > s_max_y or max_y < s_min_y:
            return False
        return True

    def write_tiles(self, location, decode_type, mesh_max_error):
        self.calculate_tiles()
        terrain_level_loc = os.path.join(location, str(self.level))
        if os.path.isdir(terrain_level_loc) is False:
            os.mkdir(terrain_level_loc)

        if self.is_compact is True:
            bundle_name = '{0}_{1}.bundle'.format(self.from_tile[0], self.from_tile[1])
            bundle_file_path = os.path.join(terrain_level_loc, bundle_name)
            bundle_f = open(bundle_file_path, 'wb')
            while len(self.__tiles) > 0:
                tile = self.__tiles.pop(0)
                tile.encode(self.bundle_array, decode_type, mesh_max_error)
                header = struct.pack('<3i', tile.x, tile.y, len(tile.binary))
                bundle_f.write(header)
                bundle_f.write(tile.binary)
                del tile
            bundle_f.close()
        else:
            while len(self.__tiles) > 0:
                tile = self.__tiles.pop(0)
                tile.encode_and_save(self.bundle_array, terrain_level_loc, decode_type, mesh_max_error)
                del tile
