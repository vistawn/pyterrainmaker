
from TileScheme import TileScheme


ts = TileScheme('tmp/dsm.tif')
ts.repalce_no_data = 0
ts.generate_scheme(False)
ts.make_bundles('tmp/out/')
