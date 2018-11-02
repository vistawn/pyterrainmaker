
import math
import numpy as np
import struct

import ecef

wgs84_rX = 6378137.0
wgs84_rY = 6378137.0
wgs84_rZ = 6356752.3142451793

def encode_terrain_mesh(terrain_grid, bounds):
    t_min_y, t_min_x, t_max_y, t_max_x = bounds
    center_x = t_min_x + (t_max_x - t_min_x) / 2
    center_y = t_min_y + (t_max_y - t_min_y) / 2
    center_h = 0
    py_width, px_width = terrain_grid.shape
    resolution = (t_max_x - t_min_x + 0.0) / px_width
    if terrain_grid.shape[0] == 65:
        center_h = terrain_grid[32][32]

    center_x, center_y, center_h = ecef.LLH2ECEF(center_x, center_y, center_h)

    result_buffer = struct.pack('<ddd', center_x, center_y, center_h)

    min_height = terrain_grid.min()
    max_height = terrain_grid.max()
    result_buffer += struct.pack('<ff', min_height, max_height)

    geo_vertexs = []
    ecef_vertexs = []
    v_array = []
    u_array = []
    h_array = []
    col = 0
    for px in xrange(0, px_width):
        row = 0
        for py in xrange(0, py_width):
            height = terrain_grid[py][px]
            geo_x = t_min_x + px * resolution
            geo_y = t_max_y - py * resolution
            geo_vertexs.append([geo_x, geo_y, height])
            ecef_vertexs.append(ecef.LLH2ECEF(geo_x, geo_y, height))
            u = zigzag_encode(int(col * 32767 / 64))
            v = zigzag_encode(int(row * 32767 / 64))
            h = zigzag_encode(int(32767 * ((height - min_height) / (max_height - min_height))))
            u_array.append(u)
            v_array.append(v)
            h_array.append(h)

            row += 1
        col += 1

    b_center, b_r = calc_boundingshpere(ecef_vertexs)
    result_buffer += struct.pack('<dddd', b_center[0], b_center[1], b_center[2], b_r)

    occ = calc_horizon_occlusion(ecef_vertexs, b_center)
    result_buffer += struct.pack('<ddd', occ[0], occ[1], occ[2])

    vertex_count = len(geo_vertexs)
    result_buffer += struct.pack('<I', vertex_count)

    for i in xrange(0, vertex_count):
        result_buffer += struct.pack('<H', u_array[i])

    for i in xrange(0, vertex_count):
        result_buffer += struct.pack('<H', v_array[i])

    for i in xrange(0, vertex_count):
        result_buffer += struct.pack('<H', h_array[i])



def calc_magnitude(point, sphere_center):
    mag_sq = v_mag_sq(point)
    mag = math.sqrt(mag_sq)
    direction = v_multi(point, 1.0 / mag)

    mag_sq = max(1.0, mag_sq)
    mag = max(1.0, mag)

    cos_alpha = v_multi(direction, sphere_center)
    sin_alpha = v_mag(v_corss(direction, sphere_center))
    cos_beta = 1.0 / mag
    sin_beta = math.sqrt(mag_sq - 1.0) * cos_beta
    return 1.0 / (cos_alpha * cos_beta - sin_alpha * sin_beta)


def calc_horizon_occlusion(vertexs, center):
    scaled_vertexs = list(map(scale_coordinate, vertexs))
    scale_center = scale_coordinate(center)  # geo

    mags = []
    for point in scaled_vertexs:
        mag = calc_magnitude(point, center)
        mags.append(mag)

    return v_multi(scale_center, max(mags))


def scale_coordinate(point):
    return [point[0] * wgs84_rX, point[1] * wgs84_rY, point[2] * wgs84_rZ]


def calc_boundingshpere(vertexs):
    MAX = float('infinity')
    MIN = float('-infinity')
    v_min_x = [MAX, MAX, MAX]
    v_min_y = [MAX, MAX, MAX]
    v_min_z = [MAX, MAX, MAX]
    v_max_x = [MIN, MIN, MIN]
    v_max_y = [MIN, MIN, MIN]
    v_max_z = [MIN, MIN, MIN]

    for i in xrange(0, len(vertexs)):
        p = [p_x, p_y, p_z] = vertexs[i]
        if p_x < v_min_x[0]:
            v_min_x = p
        if p_y < v_min_y[1]:
            v_min_y = p
        if p_z < v_min_z[2]:
            v_min_z = p

        if p_x > v_max_x[0]:
            v_max_x = p
        if p_y > v_max_y[1]:
            v_max_y = p
        if p_z > v_max_z[2]:
            v_max_z = p

    x_span = v_sq_distance(v_max_x, v_min_x)
    y_span = v_sq_distance(v_max_y, v_min_z)
    z_span = v_sq_distance(v_max_z, v_min_z)

    dia1 = v_min_x
    dia2 = v_max_x

    max_span = x_span
    if y_span > max_span:
        max_span = y_span
        dia1 = v_min_y
        dia2 = v_max_y

    if z_span > max_span:
        dia1 = v_min_z
        dia2 = v_max_z

    center = v_multi(v_add(dia1, dia2), 0.5)
    r_sq = v_sq_distance(dia2, center)
    r = math.sqrt(r_sq)

    for i in xrange(0, len(vertexs)):
        p = vertexs[i]
        old_to_p_sq = v_sq_distance(p, center)
        if old_to_p_sq > r_sq:
            old_to_p = old_to_p_sq ** 0.5
            r = (r + old_to_p) / 2.0
            r_sq = r ** 2
            old_to_new = old_to_p - r
            center = v_div(v_add(v_multi(center, r), v_multi(p, old_to_new)), old_to_p)

    return center, r


def v_add(v1, v2):
    x = v1[0] + v2[0]
    y = v1[1] + v2[1]
    z = v1[2] + v2[2]
    return [x, y, z]


def v_sub(v1, v2):
    x = v1[0] - v2[0]
    y = v1[1] - v2[1]
    z = v1[2] - v2[2]
    return [x, y, z]


def v_multi(v1, value):
    x = v1[0] * value
    y = v1[1] * value
    z = v1[2] * value
    return [x, y, z]


def v_corss(v1, v2):
    x = v1[1] * v2[2] - v1[2] * v2[1]
    y = v1[2] * v2[0] - v1[0] * v2[2]
    z = v1[0] * v2[1] - v1[1] * v2[0]
    return [x, y, z]


def v_div(v1, value):
    x = v1[0] / value
    y = v1[1] / value
    z = v1[2] / value
    return [x, y, z]


def v_mag_sq(v1):
    return v1[0] ** 2 + v1[1] ** 2 + v1[2] ** 2


def v_mag(v1):
    return math.sqrt(v_mag_sq(v1))


def v_sq_distance(v1, v2):
    dx = v1[0] - v2[0]
    dy = v1[1] - v2[1]
    dz = v1[2] - v2[2]
    return dx ** 2 + dy ** 2 + dz ** 2


def zigzag_decode(encoded_value):
    return (encoded_value >> 1) ^ (-(encoded_value & 1))


def zigzag_encode(n):
    return (n << 1) ^ (n >> 31)

