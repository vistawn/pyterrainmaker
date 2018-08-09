
import os
import gzip
import numpy
import struct
from osgeo import gdal, gdalconst
from osgeo import osr

from GlobalGeodetic import GlobalGeodetic


def decode_as_tif(in_file, out_loc, x, y, level):
    with gzip.open(in_file, 'rb') as in_zip:
        terrain_buffer = in_zip.read()
        grid = decode_buffer(terrain_buffer)
        write_grid_to_tif(grid, out_loc, x, y, level)


def write_grid_to_tif(in_grid, out_loc, x, y, level):
    mem_drv = gdal.GetDriverByName('GTiff')
    out_tif_path = out_loc + '/' + str(x) + '_' + str(y) + '_' + str(level) + '.tif'
    out_ds = mem_drv.Create(out_tif_path, 65, 65, 1, gdalconst.GDT_Float32)
    out_band = out_ds.GetRasterBand(1)
    out_band.WriteArray(in_grid, 0, 0)
    trans = get_transfrom(x, y, level)
    out_ds.SetGeoTransform(trans)

    sr_84 = osr.SpatialReference()
    sr_84.ImportFromEPSG(4326)
    out_ds.SetProjection(sr_84.ExportToWkt())
    out_ds = None


def get_transfrom(tile_x, tile_y, level):
    gg = GlobalGeodetic(True, 64)
    (t_min_y, t_min_x, t_max_y, t_max_x) = gg.TileLatLonBounds(tile_x, tile_y, level)
    res = (t_max_x - t_min_x) / 65
    return (t_min_x, res, 0.0, t_max_y, 0.0, -res)


def decode_as_txt(in_file, out_file):
    with gzip.open(in_file, 'rb') as in_zip:
        terrain_buffer = in_zip.read()
        grid = decode_buffer(terrain_buffer)
        numpy.savetxt(out_file, grid, '%.1f')


def decode_buffer(terrain_buffer):
    n = numpy.frombuffer(terrain_buffer, dtype=numpy.int16)
    n1 = numpy.split(n,[4225])
    des = n1[0].reshape(65,65)
    des = (des / 5) - 1000
    return des

#decode_as_txt('tmp/out/18/425059/170336.terrain', 'tmp/a.asc')
#decode_as_tif('tmp/out/18/425059/170336.terrain', 'tmp/', 425059, 170336, 18)