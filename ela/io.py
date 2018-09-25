import numpy as np
import rasterio
from ela.visual import to_color_image, get_color_component, to_carto

# note on generic slicing: something like the following. For now assume some things in the rgba mapping to image interms of dims
# https://stackoverflow.com/a/37729566/2752565
def simple_slice(arr, inds, axis):
    # this does the same as np.take() except only supports simple slicing, not
    # advanced indexing, and thus is much faster
    sl = [slice(None)] * arr.ndim
    sl[axis] = inds
    return arr[sl]

class GeotiffExporter:
    """Helper class to save matrices into georeferenced, GeoTiff images

    Attributes:
        crs (str, dict, or CRS): The coordinate reference system.
        transform (Affine instance): Affine transformation mapping the pixel space to geographic space.
    """
    def __init__(self, crs, transform):
        """initialize this with a coordinate reference system object and an affine transform. See rasterio.
        
        Args:
            crs (str, dict, or CRS): The coordinate reference system.
            transform (Affine instance): Affine transformation mapping the pixel space to geographic space.
        """
        self.crs = crs
        self.transform = transform

    def export_rgb_geotiff(self, matrix, full_filename, classes_cmap):
        """Save a matrix of numeric classes to an image, using a color to convert numeric values to colors

        Args:
            matrix (ndarray): numpy array, 2 dims
            full_filename (str): Full file name to save the GeoTiff image to.
            classes_cmap (dict): color map with keys as zero based numeric integers and values RGBA tuples.

        """
        n_bands = 3
        x_dataset = rasterio.open(full_filename, 'w', driver='GTiff',
                                height=matrix.shape[0], width=matrix.shape[1],
                                count=n_bands, dtype= 'uint8',
                                crs=self.crs, transform=self.transform)
        colors_array = to_color_image(matrix, classes_cmap)
        r = get_color_component(colors_array, 0)
        g = get_color_component(colors_array, 1)
        b = get_color_component(colors_array, 2)
        x_dataset.write(r, 1)
        x_dataset.write(g, 2)
        x_dataset.write(b, 3)
        x_dataset.close()