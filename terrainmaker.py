
import sys
import os
import getopt

from pyterrainmaker.TileScheme import TileScheme

try:
    from osgeo import gdal
except:
    print('gdal module is not found.')
    sys.exit(1)


def check_tif(in_tif):
    if os.path.exists(in_tif) is False:
        return False, 'is not found.'

    in_ds = gdal.Open(in_tif, gdal.GA_ReadOnly)
    if in_ds.RasterXSize > 2000 or in_ds.RasterYSize > 2000:
        band = in_ds.GetRasterBand(1)
        ov_count = band.GetOverviewCount()
        if ov_count == 0:
            del band, in_ds
            return False, ' do not have any overview. '
    del in_ds
    return True, None


def check_loc(loc):
    if os.path.isdir(loc):
        if os.access(loc, os.W_OK):
            return True, None
        else:
            return False, ': no write permission'
    else:
        return False, 'is not a valid directory'


def print_usage():

    print('''
    Usage: python terrainmaker.py [options] GDAL_DATASOURCE
    
    Options:
        -v, --version           output program version
        -h, --help              output help information
        -l, --fill <raster>     fill nodata by another raster
        -o, --out_dir <dir>     output directory for terrains
        -f, --format <format>   terrain format: heightmap/mesh, default is heightmap
        -e, --max_error <float> maximum triangulation error (float [=0.001])
        -m, --mode <mode>       output storage mode: compact/single, default is single
    ''')


def main(argv):

    try:
        opts, args = getopt.getopt(argv, "hvl:o:f:e:m:", ['help=', 'version=', 'fill=', 'out_dir=', 'format=', 'max_error=','mode='])
    except getopt.GetoptError:
        print_usage()
        sys.exit(2)

    out_loc = '.'
    storage_mode = 'single'
    terrain_format = 'heightmap'
    fill_raster = None
    max_error = 0.01
    for opt, arg in opts:
        if opt == '-h':
            print_usage()
            sys.exit()
        elif opt in ('-o', '--out_dir'):
            out_loc = arg
        elif opt in ('-e', '--max_error'):
            max_error = arg
        elif opt in ('-v', '--verion'):
            print('1.0.0')
            sys.exit()
        elif opt in ('-l', '--fill'):
            status, msg = check_tif(arg)
            if status is False:
                print(arg, msg)
                print_usage()
                sys.exit()
            else:
                fill_raster = arg
        elif opt in ('-f', '--format'):
            if arg not in ['heightmap', 'mesh']:
                print('-f parameter is invalid.')
                print_usage()
                sys.exit()
            terrain_format = arg
        elif opt in ('-m', '--mode'):
            if arg not in ['single','compact']:
                print('-m parameter is invalid.')
                print_usage()
                sys.exit()
            storage_mode = arg

    if len(args) < 1:
        print('Error: The GDAL_DATASOURCE must be specified.')
        print('')
        print_usage()
        sys.exit(2)
    
    try:
        max_error = float(max_error)
    except Exception as identifier:
        print('max_error must be float type. [0 - 1]')
        sys.exit()

    in_tif = args[0]
    status, msg = check_tif(in_tif)
    if status is False:
        print(in_tif, msg)
        print_usage()
        sys.exit()

    status, msg = check_loc(out_loc)
    if status is False:
        print(out_loc, msg)
        print_usage()
        sys.exit()

    is_compact = True if storage_mode == 'compact' else False

    ts = TileScheme(in_tif, is_compact)
    ts.out_no_data = 0
    if fill_raster:
        ts.set_fill_raster(fill_raster)
    ts.generate_scheme()

    ts.make_bundles(out_loc, decode_type=terrain_format, mesh_max_error=max_error)
    print("\r\n   done")


if __name__ == '__main__':
    main(sys.argv[1:])
