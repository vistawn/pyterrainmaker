
import numpy as np
import struct

import ecef

import TerrainTile

def encode_mesh_terrain(terrain_grid, bounds):
    # (t_min_y, t_min_x, t_max_y, t_max_x)
    t_min_y, t_min_x, t_max_y, t_max_x = bounds
    center_x = t_min_x + (t_max_x - t_min_x) / 2
    center_y = t_min_y + (t_max_y - t_min_y) / 2
    center_h = terrain_grid[32][32]

    center_x, center_y, center_h = ecef.LLH2ECEF(center_x, center_y, center_h)

    result_buffer = struct.pack('<ddd', center_x, center_y, center_h)

    min_height = terrain_grid.min()
    max_height = terrain_grid.max()

    result_buffer += struct.pack('<ff', min_height, max_height)


def decode_terrain(terrain_buffer, z, x, y):
    pos = 0
    c_x, c_y, c_z = struct.unpack('<ddd', terrain_buffer[pos:pos + 24])
    pos += 24
    c_x, c_y, c_z = ecef.ECEF2LLH(c_x, c_y, c_z)

    min_h, max_h = struct.unpack('<ff', terrain_buffer[pos:pos + 8])
    pos += 8

    # bounding sphere center coordinates ecef
    bsc_x, bsc_y, bsc_z, bsc_r = struct.unpack('<dddd', terrain_buffer[pos: pos+32])
    pos += 32

    # horizon point coordinates (ecef)
    hop_x, hop_y, hop_z = struct.unpack('<ddd', terrain_buffer[pos:pos + 24])
    pos += 24

    # vectexdata
    v_count, = struct.unpack('<I', terrain_buffer[pos: pos + 4])
    pos += 4
    vec_bytes_length = 2 * v_count
    u_list = struct.unpack('<' + 'H'*v_count, terrain_buffer[pos: pos + vec_bytes_length])
    pos += vec_bytes_length
    v_list= struct.unpack('<' + 'H'*v_count, terrain_buffer[pos: pos + vec_bytes_length])
    pos += vec_bytes_length
    height_list = struct.unpack('<' + 'H'*v_count, terrain_buffer[pos: pos + vec_bytes_length])
    pos += vec_bytes_length

    u_list_decode = map(zigzag_decode, u_list)
    v_list_decode = map(zigzag_decode, v_list)


def zigzag_decode(encoded_value):
    return (encoded_value >> 1) ^ (-(encoded_value & 1))


f = open('/Users/jack/data/13_12691_5479.terrain', 'rb')
#f = open('/Users/jack/data/1472.terrain', 'rb')
decode_terrain(f.read(), 13, 12691, 5479)


