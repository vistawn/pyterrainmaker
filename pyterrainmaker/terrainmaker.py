
from __future__ import print_function
import sys
import os
import getopt

from TileScheme import TileScheme

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
        if ov_count is 0:
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
        -o, --out_dir <dir>     specifiy the output directory for terrains
    ''')


def main(argv):

    out_loc = '.'
    try:
        opts, args = getopt.getopt(argv, "hvo:", ['help=', 'version=', 'out_dir='])
    except getopt.GetoptError:
        print_usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print_usage()
            sys.exit()
        elif opt in ('-o', '--out_dir'):
            out_loc = arg
        elif opt in ('-v', '--verion'):
            print('1.0.0')
            sys.exit()

    if len(args) < 1:
        print('Error: The GDAL_DATASOURCE must be specified.')
        print('')
        print_usage()
        sys.exit(2)

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

    ts = TileScheme(in_tif)
    ts.out_no_data = 0
    ts.generate_scheme(False)
    ts.make_bundles(out_loc)
    print(" done")


if __name__ == '__main__':
    main(sys.argv[1:])
