import numpy as np
import struct
import os
import gzip


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

    def encode(self, in_buddle_array, decodetype='heightmap'):
        self.source_array = in_buddle_array
        self.decode_type = decodetype
        self.array = self.source_array[self.y_offset:self.y_offset + 65, self.x_offset:self.x_offset + 65]

        if self.fake:
            if decodetype == 'heightmap':
                return self.encode_fake_heightmap()
            else:
                return self.encode_fake_mesh()

        if self.decode_type == 'heightmap':
            return self.encode_heightmap()
        else:
            return self.encode_mesh()

    def encode_heightmap(self):
        encode_array = (self.array + 1000) * 5
        encode_array_int = encode_array.astype(np.int16)
        encode_array_int = encode_array_int.flatten()

        encode_bytes = encode_array_int.tobytes(order='C')
        child_water_bytes = struct.pack('<BB', self.child_flag, self.water_mask)
        encode_bytes += child_water_bytes

        return encode_bytes

    def encode_fake_heightmap(self):
        self.array = np.zeros(4225).reshape(65, 65)
        encode_array = (self.array + 1000) * 5
        encode_array_int = encode_array.astype(np.int16)
        encode_array_int = encode_array_int.flatten()
        encode_bytes = encode_array_int.tobytes(order='C')
        child_water_bytes = struct.pack('<BB', self.child_flag, self.water_mask)
        encode_bytes += child_water_bytes
        return encode_bytes

    def encode_mesh(self):
        pass

    def encode_fake_mesh(self):
        pass

    def encode_and_save(self, in_buddle_array, location, decodetype='heightmap'):
        encoded_bytes = self.encode(in_buddle_array, decodetype)
        if encoded_bytes is not None:
            # save
            terrain_x_loc = os.path.join(location, str(self.x))
            if os.path.isdir(terrain_x_loc) is False:
                os.mkdir(terrain_x_loc)
            terrain_file_name = terrain_x_loc + '/' + str(self.y) + '.terrain'
            with gzip.open(terrain_file_name, 'wb+') as f:
                f.write(encoded_bytes)

        del encoded_bytes


