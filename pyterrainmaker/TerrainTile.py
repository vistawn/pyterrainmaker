import numpy as np
import struct
import os
import zlib
from io import BytesIO

import quantized_mesh_encoder
from pydelatin import Delatin
from pydelatin.util import rescale_positions


class TerrainTile(object):

    def __init__(self, offset_x, offset_y, flag_child, tile_bounds, tile_resolution):
        self.child_flag = flag_child
        self.x_offset = offset_x
        self.y_offset = offset_y
        self.x = None
        self.y = None
        self.water_mask = 0x00
        self.source_array = None
        self.decode_type = 'heightmap'
        self.array = None
        self.fake = False
        self.binary = None
        # bounds: (minx, miny, maxx, maxy)
        self.bounds = tile_bounds
        self.resolution = tile_resolution

    def encode(self, in_buddle_array, decodetype='heightmap', mesh_max_error=0.01):
        self.source_array = in_buddle_array
        self.decode_type = decodetype
        
        if self.fake:
            if decodetype == 'heightmap':
                self.encode_fake_heightmap()
            else:
                self.encode_fake_mesh(mesh_max_error)
        else:
            self.array = self.source_array[self.y_offset:self.y_offset + 65, self.x_offset:self.x_offset + 65]
            if self.decode_type == 'heightmap':
                self.encode_heightmap()
            else:
                self.encode_mesh(mesh_max_error)

    def encode_heightmap(self):
        encode_array = (self.array + 1000) * 5
        encode_array_int = encode_array.astype(np.int16)
        encode_array_int = encode_array_int.flatten()

        encode_bytes = encode_array_int.tobytes(order='C')
        child_water_bytes = struct.pack('<BB', self.child_flag, self.water_mask)
        encode_bytes += child_water_bytes
        self.binary = self.compress_gz(encode_bytes)

    @staticmethod
    def compress_gz(in_bytes):
        gzip_compress = zlib.compressobj(9, zlib.DEFLATED, zlib.MAX_WBITS | 16)
        gzip_data = gzip_compress.compress(in_bytes) + gzip_compress.flush()
        return gzip_data

    def encode_fake_heightmap(self):
        self.array = np.zeros(4225).reshape(65, 65)
        self.encode_heightmap()


    def encode_mesh(self, mesh_max_error):
        tin = Delatin(self.array, max_error=mesh_max_error)
        vertices = tin.vertices
        triangles = tin.triangles
        rescaled = rescale_positions(vertices, self.bounds)
        buf = BytesIO()
        quantized_mesh_encoder.encode(buf, rescaled, triangles)
        buf.seek(0)
        self.binary = self.compress_gz(buf.read())

    def encode_fake_mesh(self, mesh_max_error):
        self.array = np.zeros(64).reshape(8, 8)
        self.encode_mesh(mesh_max_error)

    def encode_and_save(self, in_buddle_array, location, decodetype='heightmap', mesh_max_error=0.01):
        self.encode(in_buddle_array, decodetype, mesh_max_error)
        if self.binary is not None:
            # save
            terrain_x_loc = os.path.join(location, str(self.x))
            if os.path.isdir(terrain_x_loc) is False:
                os.mkdir(terrain_x_loc)
            terrain_file_name = terrain_x_loc + '/' + str(self.y) + '.terrain'
            with open(terrain_file_name, 'wb+') as f:
                f.write(self.binary)

            self.binary = None


