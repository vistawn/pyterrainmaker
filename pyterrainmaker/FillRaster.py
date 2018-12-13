from osgeo import gdal
import struct


class FillRaster(object):

    def __init__(self, raster_loc):
        self.ds = gdal.Open(raster_loc, 0)
        transf = self.ds.GetGeoTransform()
        self.cols =  self.ds.RasterXSize
        self.rows =  self.ds.RasterYSize
        self.left_x = transf[0]
        self.top_y = transf[3]
        self.res_x = transf[1]
        self.res_y = abs(transf[5])
        self.right_x = self.left_x + self.cols * self.res_x
        self.bottom_y = self.top_y - self.rows * self.res_y
        self.band =  self.ds.GetRasterBand(1)

    def get_height(self, lon, lat):

        if not self.left_x < lon < self.right_x or not self.bottom_y < lat < self.top_y:
            return 0

        query_x = int((lon - self.left_x) / self.res_x)
        query_y = int((self.top_y - lat) / self.res_y)
        val = self.band.ReadRaster(query_x, query_y, 1, 1, buf_type=self.band.DataType)

        if val is None:
            return 0
        else:
            intval = struct.unpack('h', val)
            ele = intval[0]
            if ele == -32767:
                return 0
            else:
                return ele
