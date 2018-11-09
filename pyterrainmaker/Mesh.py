
import quantized_mesh_tile


def encode_terrain_mesh(terrain_grid, bounds):
    t_min_y, t_min_x, t_max_y, t_max_x = bounds
    width, height = terrain_grid.shape
    res = (t_max_x - t_min_x) / (width-1)

    geometries = []
    for col in xrange(0, width - 1):
        for row in xrange(0, width - 1):
            v1_x = t_min_x + col * res
            v1_y = t_max_y - (row * res)
            h1 = terrain_grid[row][col]
            v2_x = t_min_x + col * res
            v2_y = t_max_y - (row + 1) * res
            h2 = terrain_grid[row + 1][col]
            v3_x = t_min_x + (col + 1) * res
            v3_y = t_max_y - (row * res)
            h3 = terrain_grid[row][col + 1]
            v4_x = t_min_x + (col + 1) * res
            v4_y = t_max_y - (row + 1) * res
            h4 = terrain_grid[row + 1][col + 1]

            # print t_min_x, t_max_y, v4_x, v4_y
            poly1 = make_triangle(v1_x, v1_y, h1, v2_x, v2_y, h2, v3_x, v3_y, h3)
            poly2 = make_triangle(v2_x, v2_y, h2, v4_x, v4_y, h4, v3_x, v3_y, h3)
            geometries.append(poly1)
            geometries.append(poly2)

    tile = quantized_mesh_tile.encode(geometries, bounds=[t_min_x, t_min_y, t_max_x, t_max_y])
    tile_bytes = tile.toBytesIO(gzipped=True)
    return tile_bytes.read()


def make_triangle(x1, y1, h1, x2, y2, h2, x3, y3, h3):
    trangle_geom = 'POLYGON Z (({0} {1} {2}, {3} {4} {5}, {6} {7} {8}, {0} {1} {2}))'.format(
        x1, y1, h1, x2, y2, h2, x3, y3, h3
    )
    return trangle_geom

