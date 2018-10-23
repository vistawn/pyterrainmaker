import numpy as np
import struct
import os
import zlib


class TerrainTile(object):

    def __init__(self, offset_x, offset_y, flag_child):
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

    def encode(self, in_buddle_array, decodetype='heightmap'):
        self.source_array = in_buddle_array
        self.decode_type = decodetype
        
        if self.fake:
            if decodetype == 'heightmap':
                self.encode_fake_heightmap()
            else:
                self.encode_fake_mesh()
        else:
            self.array = self.source_array[self.y_offset:self.y_offset + 65, self.x_offset:self.x_offset + 65]
            if self.decode_type == 'heightmap':
                self.encode_heightmap()
            else:
                self.encode_mesh()

    def encode_heightmap(self):
        encode_array = (self.array + 1000) * 5
        encode_array_int = encode_array.astype(np.int16)
        encode_array_int = encode_array_int.flatten()

        encode_bytes = encode_array_int.tobytes(order='C')
        child_water_bytes = struct.pack('<BB', self.child_flag, self.water_mask)
        encode_bytes += child_water_bytes
        self.binary = self.compress_gz(encode_bytes)

    def compress_gz(self, bytes):
        gzip_compress = zlib.compressobj(9, zlib.DEFLATED, zlib.MAX_WBITS | 16)
        gzip_data = gzip_compress.compress(bytes) + gzip_compress.flush()
        return gzip_data

    def encode_fake_heightmap(self):
        self.array = np.zeros(4225).reshape(65, 65)
        encode_array = (self.array + 1000) * 5
        encode_array_int = encode_array.astype(np.int16)
        encode_array_int = encode_array_int.flatten()
        encode_bytes = encode_array_int.tobytes(order='C')
        child_water_bytes = struct.pack('<BB', self.child_flag, self.water_mask)
        encode_bytes += child_water_bytes
        self.binary = self.compress_gz(encode_bytes)

    def encode_mesh(self):
        self.binary = None

    def encode_fake_mesh(self):
        self.binary = None

    def encode_and_save(self, in_buddle_array, location, decodetype='heightmap'):
        self.encode(in_buddle_array, decodetype)
        if self.binary is not None:
            # save
            terrain_x_loc = os.path.join(location, str(self.x))
            if os.path.isdir(terrain_x_loc) is False:
                os.mkdir(terrain_x_loc)
            terrain_file_name = terrain_x_loc + '/' + str(self.y) + '.terrain'
            with open(terrain_file_name, 'wb+') as f:
                f.write(self.binary)

            self.binary = None


