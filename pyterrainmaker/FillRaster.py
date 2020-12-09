from osgeo import gdal, gdalconst
import numpy as np
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
    
    
    def get_array(self, extent, out_x_count, out_y_count):

        file_ds = self.ds

        file_band = file_ds.GetRasterBand(1)
        ov_count = file_band.GetOverviewCount()

        file_trans = file_ds.GetGeoTransform()
        min_ori_x = file_trans[0]
        max_ori_y = file_trans[3]

        file_ori_res = file_trans[1]
        file_ori_x_size = file_band.XSize
        
        (b_real_min_x, b_real_min_y, b_real_max_x, b_real_max_y) = extent
        out_res = (extent[2] - extent[0]) / out_x_count

        read_band = file_band
        read_res = file_ori_res

        for r_i in range(ov_count):
            ov_band = file_band.GetOverview(r_i)
            ov_x_size = ov_band.XSize
            ov_res = (file_ori_x_size / ov_x_size) * file_ori_res
            
            if ov_res > out_res:
                break
            else:
                read_band = ov_band
                read_res = ov_res
        
        ## read array by extent
        read_min_px = int((b_real_min_x - min_ori_x) / read_res)
        read_max_px = int((b_real_max_x - min_ori_x) / read_res)
        read_min_py = int((max_ori_y - b_real_max_y) / read_res)
        read_max_py = int((max_ori_y - b_real_min_y) / read_res)

        read_x_count = read_max_px - read_min_px
        read_y_count = read_max_py - read_min_py

        read_array = read_band.ReadAsArray(read_min_px, read_min_py, read_x_count, read_y_count)
        if read_array is None:
            return None
        read_array = read_array.astype(np.float32)

        if read_x_count == out_x_count and read_y_count == out_y_count:
            return read_array
        else:
            mem_drv = gdal.GetDriverByName('MEM')
            prj_ds = mem_drv.Create('', read_x_count, read_y_count, 1, gdalconst.GDT_Float32)
            prj_band = prj_ds.GetRasterBand(1)
            prj_band.WriteArray(read_array, 0, 0)

            dst_ds = mem_drv.Create('', out_x_count, out_y_count, 1, gdalconst.GDT_Float32)
            dst_ds.SetGeoTransform((0.0, 1.0, 0.0, 0.0, 0.0, 1.0))
            prj_ds.SetGeoTransform(
            (0.0, out_x_count / float(read_x_count), 0.0, 0.0, 0.0, out_y_count / float(read_y_count)))
            res = gdal.ReprojectImage(prj_ds, dst_ds, None, None, eResampleAlg=gdalconst.GRIORA_NearestNeighbour)
            if res != 0:
                del prj_ds
                del dst_ds
                self.error("ReprojectImage() failed on %s, error %d" % ('aa', res))
            else:
                result = np.array(dst_ds.GetRasterBand(1).ReadAsArray(0, 0, out_x_count, out_y_count))
                del prj_ds
                del dst_ds
                return result

