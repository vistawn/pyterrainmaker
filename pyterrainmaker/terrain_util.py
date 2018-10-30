#!/usr/bin/env python
from __future__ import print_function
import argparse
import gzip
import numpy
import struct
import sys
import os
from osgeo import gdal
from osgeo import gdalconst
from osgeo import osr

from GlobalGeodetic import GlobalGeodetic


try:
    from osgeo import gdal
except:
    print('gdal module is not found.')
    sys.exit(1)


class Terrain_Util(object):

    def __init__(self):
        parser = argparse.ArgumentParser(
            description='utils for terrain file',
            usage='''terrain_util.py <command> [<args>]

The most commonly used commands are:
   dt     decode terrain file to GeoTiff
   da     decode terrain file to ASCII
   ex     explode a bundle file to single terrain files
''')
        parser.add_argument('command', help='Subcommand to run')
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            print('Unrecognized command')
            parser.print_help()
            exit(1)
        getattr(self, args.command)()

    def dt(self):
        """decode as tif file"""
        parser = argparse.ArgumentParser(
            description='decode a terrain file to GeoTiff')
        parser.add_argument('z', action='store', type=int)
        parser.add_argument('x', action='store', type=int)
        parser.add_argument('y', action='store', type=int)
        parser.add_argument('in_file')
        parser.add_argument('out_loc', nargs='?', default='.')

        args = parser.parse_args(sys.argv[2:])
        in_file = args.in_file
        out_loc = args.out_loc
        x = args.x
        y = args.y
        level = args.z

        with gzip.open(in_file, 'rb') as in_zip:
            terrain_buffer = in_zip.read()
            grid = self.decode_buffer(terrain_buffer)
            self.write_grid_to_tif(grid, out_loc, x, y, level)

    def da(self):
        """decode as ascii file"""
        parser = argparse.ArgumentParser(
            description='decode a terrain file to ASCII')
        parser.add_argument('in_terrain')
        parser.add_argument('out_ascii')

        args = parser.parse_args(sys.argv[2:])
        in_file = args.in_terrain
        out_file = args.out_ascii

        with gzip.open(in_file, 'rb') as in_zip:
            terrain_buffer = in_zip.read()
            grid = self.decode_buffer(terrain_buffer)
            numpy.savetxt(out_file, grid, '%.1f')

    def ex(self):
        """explode a bundle file to single terrain files"""
        parser = argparse.ArgumentParser(
            description='explode a bundle file to single terrain files')
        parser.add_argument('in_bundle')
        parser.add_argument('-out_loc', help='output terrain files location', default='.')

        args = parser.parse_args(sys.argv[2:])
        bundle_file = args.in_bundle
        out_loc = args.out_loc
        with open(bundle_file, 'rb') as b_f:
            header = b_f.read(12)
            while header:
                (tile_x, tile_y, tile_len) = struct.unpack('<3i', header)
                print('writing ', tile_x, tile_y)
                t_b = b_f.read(tile_len)
                filename = '{0}_{1}.terrain'.format(tile_x, tile_y)
                with open(os.path.join(out_loc, filename), 'wb') as t_f:
                    t_f.write(t_b)
                header = b_f.read(12)

    def write_grid_to_tif(self, in_grid, out_loc, x, y, level):
        mem_drv = gdal.GetDriverByName('GTiff')
        out_tif_path = out_loc + '/' + str(x) + '_' + str(y) + '_' + str(level) + '.tif'
        out_ds = mem_drv.Create(out_tif_path, 65, 65, 1, gdalconst.GDT_Float32)
        out_band = out_ds.GetRasterBand(1)
        out_band.WriteArray(in_grid, 0, 0)
        trans = self.get_transfrom(x, y, level)
        out_ds.SetGeoTransform(trans)

        sr_84 = osr.SpatialReference()
        sr_84.ImportFromEPSG(4326)
        out_ds.SetProjection(sr_84.ExportToWkt())
        out_ds = None

    def get_transfrom(self, tile_x, tile_y, level):
        gg = GlobalGeodetic(True, 64)
        (t_min_y, t_min_x, t_max_y, t_max_x) = gg.TileLatLonBounds(tile_x, tile_y, level)
        res = (t_max_x - t_min_x) / 64
        return t_min_x, res, 0.0, t_max_y, 0.0, -res

    def decode_buffer(self, terrain_buffer):
        n = numpy.frombuffer(terrain_buffer, dtype=numpy.int16)
        n1 = numpy.split(n, [4225])
        des = n1[0].reshape(65, 65)
        des = (des / 5) - 1000
        return des


if __name__ == '__main__':
    Terrain_Util()