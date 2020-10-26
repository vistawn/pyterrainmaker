# pyterrainmaker

A pure Python library for making  [heightmap-1.0 terrain format](http://cesiumjs.org/data-and-assets/terrain/formats/heightmap-1.0.html) terrains for use with [CesiumJs](http://cesiumjs.org)
like [Cesium Terrain Builder](https://github.com/geo-data/cesium-terrain-builder).

Fully compatible with [Cesium Terrain Server](https://github.com/geo-data/cesium-terrain-server) 

## Command Line Tools

### `python terrainmaker.py -o ./terrain_tiles dem.tif`  

```
Usage: python terrainmaker.py [options] GDAL_DATASOURCE
Options:
    -v, --version           output program version
    -h, --help              output help information
    -o, --out_dir <dir>     specify the output directory for terrains
    -m, --mode <mode>      specify the output storage mode: compact/single, default is single
```
#### Recommendations

* Input GDAL_DATASOURCE elevation data should have only one band or elevation band is the first band.
* Input GDAL_DATASOURCE band must create overviews if band's X-Size or Y-Size greater than 2000 pixel.

### terrain_util
```shell
    python terrain_util.py 
```




## Dependency
* GDAL
* numpy

## Advantages compared to Cesium Terrain Builder

* Implements with Pure Python. easy to install & use.
* Lower IO usage and faster especially process big data.
* NO MORE GDAL error thrown when processing big data.

## TODO

* Bundle mode terrains for better storage and management.
* Support for [quantized-mesh-1.0 terrain format](https://cesiumjs.org/data-and-assets/terrain/formats/quantized-mesh-1.0/)
* Multi-threading support



