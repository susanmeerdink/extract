`extract` is a python module that builds off of `rasterio` functionality
to allow the extraction of image pixels in areas corresponding to
polygon geometries.

It will probably be superseded over time by core `rasterio` functionality,
but for now is useful for quick-and-dirty shape extraction.

## Usage

Input takes shapely geometries and (optional) crs mapping for shape
spatial reference.

```python
>>> syrtis_tm = {
    'a': 3396190,
    'b': 3376200,
    'k': 0.9996,
    'lat_0': 17,
    'lon_0': 76.5,
    'no_defs': True,
    'proj': u'tmerc',
    'units': u'm',
    'x_0': 0,
    'y_0': 0}

>>> repr(landing_ellipse)
<shapely.geometry.polygon.Polygon at 0x10fc6c810>
```

Then you can extract the shape from a `rasterio` dataset.

```python
>>> import rasterio
>>> from extract import extract_area

>>> with rasterio.open(hrsc_mosaic) as dem:
        array = extract_area(dem,
            landing_ellipse,
            feature_crs=syrtis_tm)

>>> array.min(), array.max()
(-2441, -2094)
```

The output array is 3-dimensional `numpy` `MaskedArray` (masked by the shape boundaries)
with a first dimension corresponding to the number of bands extracted.

```python
>>> array.shape
(1, 281, 332)
```

It also has an attached `offset` property that contains its (y,x)-indexed distance
from the image origin.

```python
>>> array.offset
(17949, 3484)
```

## Installation

For now, this can be installed as a standalone module:

```
~ pip install git+https://github.com/davenquinn/extract.git
```

## Todo

- Punch out inner rings of polygons
- Test
- Get rid of `PIL` dependency; I think there's some `rasterio`
  functions that can be used to mask the image instead.
- Extract points and lines with same interface (possibly with linear interpolation). I
  already have some code for this but I'm not sure how to integrate
it currently...

I'd like to see this functionality integrated into `rasterio` itself;
stay tuned!

