"""
Several methods for computing windowed spectra of a CRISM image given a series of numerical masks.
"""
import rasterio
import numpy as N
from PIL import Image, ImageDraw

def create_pixel_transform(dataset, snap=False):
    """ Returns a function that transforms map coordinates to pixel coordinates"""
    geomatrix = dataset.get_transform()
    def project_coord(x,y,z=None):
        x = (x - geomatrix[0])/geomatrix[1]
        y = (y - geomatrix[3])/geomatrix[5]
        if snap:
            x,y = map(int,(x,y))
        if z is None:
            return x,y
        return x,y,z
    return project_coord

def create_mask(dataset, geometry):
    """ Returns a boolean array that is `true` where a geometry exists
        and `false` otherwise. Note: doesn't punch out interior rings yet."""
    height, width = dataset.shape
    pixels = geometry.exterior.coords
    # PIL regrettably works in the reverse coordinate order
    # But shapely shapes (and other geo-things) are already x-first
    img = Image.new('L', (width, height), 0)
    ImageDraw.Draw(img).polygon(pixels, outline=1, fill=1)
    arr =  N.array(img, dtype=bool)
    assert arr.shape == dataset.shape
    return arr

def offset_mask(mask):
    """ Returns a mask shrunk to the 'minimum bounding rectangle' of the
        nonzero portion of the previous mask, and its offset from the original.
        Useful to find the smallest rectangular section of the image that can be
        extracted to include the entire geometry. Conforms to the y-first
        expectations of numpy arrays rather than x-first (geodata).
    """
    def axis_data(axis):
        """Gets the bounds of a masked area along a certain axis"""
        x = mask.sum(axis)
        trimmed_front = N.trim_zeros(x,"f")
        offset = len(x)-len(trimmed_front)
        size = len(N.trim_zeros(trimmed_front,"b"))
        return offset,size

    xo,xs = axis_data(0)
    yo,ys = axis_data(1)

    array = mask[yo:yo+ys,xo:xo+xs]
    offset = (yo,xo)
    return array, offset

def mask_shape(mask,axis=0):
    x = mask.sum(axis)
    xi = N.trim_zeros(x,"f")
    xo = len(x)-len(xi)
    xs = len(N.trim_zeros(xi,"b"))
    return xo,xs

class OffsetArray(N.ma.MaskedArray): pass

def extract_area(dataset, geometry, indexes=1, **kwargs):
    """
    Compute a spectrum using the basic GDAL driver to read a single band of the spectrum.
    This is faster than the rasterio version and is the default.
    """
    mask = create_mask(dataset,geometry)
    trimmed_mask, offset = offset_mask(mask)
    yo,xo = offset
    ys,xs = trimmed_mask.shape
    for i in (0,1):
        assert N.allclose(trimmed_mask.sum(axis=i), N.trim_zeros(mask.sum(axis=i)))

    #maskt = maskt.transpose() # Conform to GDAL's fascist X-first expectations
    try:
        nbands = len(indexes)
    except TypeError:
        nbands = 1

    # Expand mask to fill all bands
    expanded_mask = N.repeat(
        N.expand_dims(trimmed_mask,0),
        nbands,
        axis=0)

    arr = dataset.read(
        window=((yo,yo+ys),(xo,xo+xs)),
        masked=True,
        **kwargs)
    arr[expanded_mask==False] = N.ma.masked
    arr = arr.view(OffsetArray)
    arr.offset = offset
    return arr
