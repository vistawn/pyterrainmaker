
import os
import gzip
import numpy
import struct

def decode(in_file, out_file):
    with gzip.open(in_file, 'rb') as in_zip:
        terrain_obj = in_zip.read()
        decode_buffer(terrain_obj, out_file)


def decode_buffer(terrain_buffer, out_file):
    n = numpy.frombuffer(terrain_buffer, dtype=numpy.int16)
    n1 = numpy.split(n,[4225])
    des = n1[0].reshape(65,65)
    des = (des / 5) - 1000
    numpy.savetxt(out_file, des, '%d')


level_dir = '/Users/jack/dev/opensource/pyterrainmaker/pyterrainmaker/tmp/out/18/'

dirs = os.listdir(level_dir)

for d in dirs:
    sub_d = level_dir + d 
    terrain_files = os.listdir(sub_d)
    for t_f in terrain_files:
        out_f = d + '_' + t_f.replace('.terrain','.asc')
        decode(sub_d + '/' + t_f,  'tmp/asc_18/' + out_f)

#decode('/Users/jack/dev/opensource/pyterrainmaker/pyterrainmaker/tmp/out/18/425020/170371.terrain', 'aaa.asc')





