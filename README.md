# pyterrainmaker

A pure Python library for making [heightmap](https://github.com/CesiumGS/cesium/wiki/heightmap-1.0) and [quantized-mesh](https://github.com/CesiumGS/quantized-mesh) terrains for [CesiumJs](http://cesiumjs.org).

Fully compatible with [Cesium Terrain Server](https://github.com/geo-data/cesium-terrain-server).


## Command Line Tools

### `python3 terrainmaker.py -o ./terrain_tiles dem.tif`  

```
Usage: python3 terrainmaker.py [options] GDAL_DATASOURCE
Options:
    -v, --version           output program version
        -h, --help              output help information
        -l, --fill <raster>     fill nodata by another raster
        -o, --out_dir <dir>     output directory for terrains
        -f, --format <format>   terrain format: heightmap/mesh, default is heightmap
        -e, --max_error <float> maximum triangulation error (float [=0.001])
        -m, --mode <mode>       output storage mode: compact/single, default is single
```
#### Recommendations

* Input GDAL_DATASOURCE elevation data should have only one band or elevation band is the first band.
* Input GDAL_DATASOURCE band must create overviews if band's X-Size or Y-Size greater than 2000 pixel.

### terrain_util
```shell
    python3 terrain_util.py 
```




## Dependency
* GDAL
* numpy
* quantized_mesh_encoder
* pydelatin


## TODO

* Bundle mode terrains for better storage and management.
* Multi-threading support



