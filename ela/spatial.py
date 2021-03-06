import rasterio
import numpy as np
import pandas as pd

from ela.textproc import EASTING_COL, NORTHING_COL, DEPTH_FROM_AHD_COL, DEPTH_FROM_COL, DEPTH_TO_AHD_COL, DEPTH_TO_COL


def read_raster_value(dem,band_1,easting,northing):
    """Read a value in a raster grid given easting/northing
    
    Args:
        dem (rasterio dataset): dem
    
    """
    if (np.isnan(easting) or np.isnan(northing)):
        raise Exception("Easting and northing must not be NaN")
    row, col = dem.index(easting,northing)
    # dem.index seems to return floats and this causes a but to index its numpy array. 
    # something used to work (who knows which package version soup) and does not anymore. At runtime. Dynamic typing...
    row = int(row)
    col = int(col)
    if (row < 0 or row >= band_1.shape[0] or col < 0 or col >= band_1.shape[1]):
        return np.nan
    else:
        return band_1[row,col]

def raster_drill(row,dem, raster_grid):
    easting=row[EASTING_COL]
    northing=row[NORTHING_COL]
    return read_raster_value(dem,raster_grid,easting,northing)

def raster_drill_df(df, dem, raster_grid):
    return df.apply (lambda row: raster_drill(row,dem, raster_grid),axis=1)

def add_ahd(lithology_df, data_raster, drop_na=False):
    df = lithology_df.copy(deep=True)
    data_grid = data_raster.read(1)
    nd = data_raster.nodata
    ahd = raster_drill_df(df, data_raster, data_grid)
    ahd[ahd==nd] = np.nan
    df[DEPTH_FROM_AHD_COL]=ahd-df[DEPTH_FROM_COL]
    df[DEPTH_TO_AHD_COL]=ahd-df[DEPTH_TO_COL]
    if drop_na:
        df = df[pd.notna(df[DEPTH_TO_AHD_COL])]
    return df

def get_coords_from_gpd_shape(shp, colname='geometry'):
    p = shp[[colname]]
    pts = p.values.flatten()
    c = [(pt.x, pt.y) for pt in pts]
    return pd.DataFrame(c, columns=["x","y"])

def get_unique_coordinates(easting, northing):
    grid_coords = np.empty( (len(easting), 2) )
    grid_coords[:,0] = easting
    grid_coords[:,1] = northing
    b = np.unique(grid_coords[:,0] + 1j * grid_coords[:,1])
    points = np.column_stack((b.real, b.imag))
    return points

class HeightDatumConverter:
    """
    Attributes:
        crs (str, dict, or CRS): The coordinate reference system.
        transform (Affine instance): Affine transformation mapping the pixel space to geographic space.
    """
    def __init__(self, dem_raster):
        """Initialize this with a coordinate reference system object and an affine transform. See rasterio.
        
        Args:
        """
        self.dem_raster = dem_raster
        self.data_grid = self.dem_raster.read(1)

    def _raster_drill(self, row, easting_col, northing_col):
        easting=row[easting_col]
        northing=row[northing_col]

    def _raster_drill_df(self, df, easting_col, northing_col):
        x = df[easting_col].values
        y = df[northing_col].values
        v = np.empty_like(x, dtype=self.data_grid.dtype) # Try to fix https://github.com/jmp75/pyela/issues/2
        for i in range(len(x)):
            v[i] = read_raster_value(self.dem_raster, self.data_grid, x[i], y[i])
        return v

    def add_height(self, lithology_df, 
        depth_from_col=DEPTH_FROM_COL, depth_to_col=DEPTH_TO_COL, 
        depth_from_ahd_col=DEPTH_FROM_AHD_COL, depth_to_ahd_col=DEPTH_TO_AHD_COL, 
        easting_col=EASTING_COL, northing_col=NORTHING_COL,
        drop_na=False):
        df = lithology_df.copy(deep=True)
        nd = np.float32(self.dem_raster.nodata) # Try to fix https://github.com/jmp75/pyela/issues/2
        ahd = self._raster_drill_df(df, easting_col, northing_col)
        ahd[ahd==nd] = np.nan
        df[depth_from_ahd_col]=ahd-df[depth_from_col]
        df[depth_to_ahd_col]=ahd-df[depth_to_col]
        if drop_na:
            df = df[pd.notna(df[depth_to_ahd_col])]
        return df

    def raster_value_at(self, easting, northing):
        return read_raster_value(self.dem_raster, self.data_grid, easting, northing)

class DepthsRounding:

    def __init__(self, depth_from_col=DEPTH_FROM_COL, depth_to_col=DEPTH_TO_COL):
        self.depth_from_col = depth_from_col
        self.depth_to_col = depth_to_col

    def round_to_metre_depths(self, df, func=np.round, remove_collapsed=False):
        depth_from_rounded =df[self.depth_from_col].apply(func)
        depth_to_rounded =df[self.depth_to_col].apply(func)
        df_1 = df.copy(deep=True)
        df_1[self.depth_from_col] = depth_from_rounded
        df_1[self.depth_to_col] = depth_to_rounded
        collapsed = (df_1[self.depth_from_col] == df_1[self.depth_to_col])
        if remove_collapsed:
            df_1 = df_1[~collapsed]
        return df_1

    def assess_num_collapsed(self, df, func=np.round):
        tmp = self.round_to_metre_depths(df, func)
        collapsed = (tmp[self.depth_from_col] == tmp[self.depth_to_col])
        return collapsed.sum()

# Remove if indeed redundant/superseded
# def slice_above(lithology_df, lower_bound_raster, drop_na=True):
#     df = lithology_df.copy(deep=True)
#     data_grid = lower_bound_raster.read(1)
#     lower_bound_values = raster_drill_df(df, lower_bound_raster, data_grid)
#     if drop_na:
#         df = df[pd.notna(lower_bound_values)]
#         lower_bound_values = lower_bound_values[pd.notna(lower_bound_values)]
#     df_slice=df.loc[(df[DEPTH_FROM_AHD_COL] >= lower_bound_values) & (df[DEPTH_TO_AHD_COL] >= lower_bound_values)]
#     return df_slice

def z_index_for_ahd_functor(a=1, b=50):
    def z_index_for_ahd(ahd):
        return a * ahd + b
    return z_index_for_ahd

def average_slices(slices):
    """Gets the average values over numeric slices
    
    Args:
        slices (list of 2D np arrays): slices to average
    
    """

    # TODO there are ways to make this more efficient, e.g. if we get a volume instead of a list of slices
    # my_volume
    # my_sub_volume = my_volume[:,:,from:to:by] or something like that
    # the_average = np.average(my_sub_volume, axis=2).shape
    # for now:
    if len(slices) < 1:
        raise ZeroDivisionError("There must be at least one slice to average over")
    summed = np.empty(slices[0].shape)
    summed = 0.0
    for i in range(len(slices)):
        summed = summed + slices[i]
    return summed / len(slices)


def burn_volume_func(func_below, func_above, volume, surface_raster, height_to_z, below=False, ignore_nan=False, inclusive=False):
    """
    Reusable function, not for end user. Process parts of a xyz volume given a surface, below or above the intersection of the volume with the surface
    """
    dim_x,dim_y,dim_z=volume.shape
    z_index_max = dim_z-1
    # TODO if surface_raster.shape[0] != dim_x or surface_raster.shape[1] != dim_y 
    for x in np.arange(0,dim_x,1):
        for y in np.arange(0,dim_y,1):
            # From the original code I had retrieved something I cannot understand (why 30??)
            # erode_until=-(surface_raster.astype(int)-30)[x,y] 
            dem_height = surface_raster[x,y]
            if np.isnan(dem_height):
                if not ignore_nan:
                    volume[x,y,:]=np.nan
            else:
                z_height = height_to_z(dem_height) 
                z_height = min(z_index_max, max(0.0, z_height))
                z_height = int(round(z_height))
                zh_nan = z_height
                if below:
                    if inclusive:
                        zh_nan = zh_nan + 1
                        zh_nan = min(z_index_max, max(0.0, zh_nan))
                    func_below(volume, x, y, zh_nan)
                else:
                    if not inclusive:
                        zh_nan = zh_nan + 1
                        zh_nan = min(z_index_max, max(0.0, zh_nan))
                    func_above(volume, x, y, zh_nan)

def drill_volume(volume, slice_surface, height_to_z, x, y):
    dim_z=volume.shape[2]
    z_index_max = dim_z-1
    slice_height = slice_surface[x,y]
    def to_int(x):  # may be custom later
        return int(np.floor(x))
    if np.isnan(slice_height):
        return np.nan
    else:
        z_height = to_int(height_to_z(slice_height))
        if z_height < 0:
            return np.nan
        elif z_height > z_index_max:
            return np.nan
        else:
            z = z_height
            return volume[x,y,z]

def slice_volume(volume, slice_surface, height_to_z):
    dim_x,dim_y,dim_z=volume.shape
    # TODO if surface_raster.shape[0] != dim_x or surface_raster.shape[1] != dim_y 
    result = np.empty((dim_x,dim_y))
    for x in np.arange(0,dim_x,1):
        for y in np.arange(0,dim_y,1):
            result[x,y] = drill_volume(volume, slice_surface, height_to_z, x, y)
    return result

class SliceOperation:
    """
    Attributes:
        crs (str, dict, or CRS): The coordinate reference system.
        transform (Affine instance): Affine transformation mapping the pixel space to geographic space.
    """
    def __init__(self, dem_array_zeroes_infill, z_index_for_ahd):
        """initialize this with a coordinate reference system object and an affine transform. See rasterio.
        
        Args:
        """
        self.dem_array_zeroes_infill = dem_array_zeroes_infill
        self.z_index_for_ahd = z_index_for_ahd

    @staticmethod
    def arithmetic_average(slices):
        k_average = np.empty(slices[0].shape)
        k_average = 0.0
        for i in range(len(slices)):
            k_average = k_average + slices[i]
        k_average = k_average / len(slices)
        return k_average

    @staticmethod
    def arithmetic_average_int(slices):
        return np.round(SliceOperation.arithmetic_average(slices))

    def reduce_slices_at_depths(self, volume, from_depth, to_depth, reduce_func):
        slices = [slice_volume(volume, self.dem_array_zeroes_infill - depth, self.z_index_for_ahd) for depth in range(from_depth, to_depth+1)]
        return reduce_func(slices)

    def from_ahd_to_depth_below_ground_level(self, volume, from_depth, to_depth):
        # Note: may not be the most computationally efficient, but deal later.
        depths = range(from_depth, to_depth+1)
        slices = [slice_volume(volume, self.dem_array_zeroes_infill - depth, self.z_index_for_ahd) for depth in depths]
        nx, ny, _ = volume.shape
        nz = len(depths)
        result = np.empty([nx, ny, nz])
        for i in range(nz):
            ii = (nz-1) - i 
            result[:,:,i] = slices[ii]
        return result


def burn_volume(volume, surface_raster, height_to_z, below=False, ignore_nan=False, inclusive=False):
    """
    "burn out" parts of a xyz volume given a surface, below or above the intersection of the volume with the surface

    :volume: volume to modify
    :type: 3D numpy
    
    :surface_raster: AHD coordinate at which to slice the data frame for lithology observations 
    :type: 2D numpy
    
    :height_to_z: Number of neighbors to pass to KNeighborsClassifier
    :type: a function to convert the surface raster value (height for a DEM) to a corresponding z-index in the volume.
    
    :below: should the part below or above be burnt out
    :type: bool    

    :ignore_nan: If the surface to burn from has NaNs, should it mask out the whole corresponding cells in the volume
    :type: bool    

    :inclusive: is the cell in the volume cut by the surface included in the burning out (i.e. set to NaN) or its value kept?
    :type: bool    
    """
    def nan_below_z(volume, x, y, z):
        volume[x, y,0:z]=np.nan

    def nan_above_z(volume, x, y, z):
        volume[x, y,z:]=np.nan

    burn_volume_func(nan_below_z, nan_above_z, volume, surface_raster, height_to_z, below, ignore_nan, inclusive)


def set_at_surface_boundary(volume, surface_raster, height_to_z, value=0.0, ignore_nan=False):
    """
    "burn out" parts of a xyz volume given a surface, below or above the intersection of the volume with the surface

    :volume: volume to modify
    :type: 3D numpy
    
    :surface_raster: AHD coordinate at which to slice the data frame for lithology observations 
    :type: 2D numpy
    
    :height_to_z: Number of neighbors to pass to KNeighborsClassifier
    :type: a function to convert the surface raster value (height for a DEM) to a corresponding z-index in the volume.
    
    :below: should the part below or above be burnt out
    :type: bool    

    :ignore_nan: If the surface to burn from has NaNs, should it mask out the whole corresponding cells in the volume
    :type: bool    

    :inclusive: is the cell in the volume cut by the surface included in the burning out (i.e. set to NaN) or its value kept?
    :type: bool    
    """
    def set_at_z(volume, x, y, z):
        volume[x, y,z]=value

    burn_volume_func(set_at_z, set_at_z, volume, surface_raster, height_to_z, below=False, ignore_nan=ignore_nan, inclusive=False)


def get_bbox(geo_pd):
    return (geo_pd.total_bounds[0], geo_pd.total_bounds[1], geo_pd.total_bounds[2], geo_pd.total_bounds[3])

def create_meshgrid_cartesian(x_min, x_max, y_min, y_max, grid_res):
    """Create a 2D meshgrid to be used with numpy for vectorized operations and Mayavi visualisation.
    
    Args:
        x_min (numeric): lower x coordinate
        x_max (numeric): upper x coordinate
        y_min (numeric): lower y coordinate
        y_max (numeric): upper y coordinate
        grid_res (numeric): x and y resolution of the grid we create

    Return:
        (list of 2 2dim numpy.ndarray): 2-D coordinate arrays for vectorized evaluations of 2-D scalar/vector fields. 
            The arrays are ordered such that the first dimension relates to the X coordinate and the second the Y coordinate. This is done such that 
            the 2D coordinate arrays work as-is with visualisation with Mayavi without unnecessary transpose operations. 
    """
    # The use of indexing='ij' deserves an explanation, as it is counter intuitive. The nupmy doc states
    # https://docs.scipy.org/doc/numpy/reference/generated/numpy.meshgrid.html
    # In the 2D case with inputs of length M and N, the outputs are of shame N, M for 'xy' indexing and M, N for 'ij' indexing
    # We want an output that preserves the order of x then y coordinates, so we have to use indexing='ij'  instead of indexing='xy' otherwise the dim order is swapped, and 
    # later on for mayavi visualizations we need to swap them back, which leads to confusions.
    return np.meshgrid(np.arange(x_min, x_max, grid_res),np.arange(y_min, y_max, grid_res), indexing='ij')

def create_meshgrid(geo_pd, grid_res):
    """Create a 2D meshgrid to be used with numpy for vectorized operations and Mayavi visualisation.
    
    Args:
        geo_pd (geopandas): shape from which we can get the bounding box as a basis for the extend of the meshgrid
        grid_res (numeric): x and y resolution of the grid we create

    Return:
        (list of 2 2dim numpy.ndarray): 2-D coordinate arrays for vectorized evaluations of 2-D scalar/vector fields. 
            The arrays are ordered such that the first dimension relates to the X coordinate and the second the Y coordinate. This is done such that 
            the 2D coordinate arrays work as-is with visualisation with Mayavi without unnecessary transpose operations. 
    """
    x_min, y_min, x_max, y_max = get_bbox(geo_pd)
    return create_meshgrid_cartesian(x_min, x_max, y_min, y_max, grid_res)

def vstacked_points(xx, yy):
    g = (xx, yy)
    m = [np.ravel(pt) for pt in g]
    points = np.vstack(m)
    return points

def surface_array(raster, x_min, y_min, x_max, y_max, grid_res):
    xx, yy = create_meshgrid_cartesian(x_min, x_max, y_min, y_max, grid_res)
    points = vstacked_points(xx, yy)
    num_points=points.shape[1]
    band_1 = raster.read(1)
    z = []
    nd = np.float32(raster.nodata)
    for point in np.arange(0,num_points):
        x=points[0,point]
        y=points[1,point]
        nrow, ncol = band_1.shape
        # return band_1.shape
        row, col = raster.index(x,y)
        # July 2018: Change of behavior with (package versions??). At runtime. 
        # Python dynamic typing SNAFU...
        row = int(row)
        col = int(col)
        if (row < nrow and col < ncol and row >= 0 and col >= 0):
            result=band_1[row,col]
            if (result == nd):
                result = np.nan
        else:
            result = np.nan
        z=np.append(z,result)
    # z=z.clip(0) This was probably for the DEM assuming all is above sea level?
    #return (z.shape, xx.shape, num_points)
    dem_array=z.reshape(xx.shape)
    return dem_array



# class_value = 3.0
# color_name = 'yellow'
# single_litho = extract_single_lithology_class_3d(test, class_value)
# mlab.figure(size=(800, 800))
# # s = np.flip(np.flip(test,axis=2), axis=0)
# s = flip(flip(single_litho,axis=2), axis=0)
# vol = mlab.contour3d(s, contours=[class_value-0.5], color=to_rgb(color_name))
# dem_surf = mlab.surf(xx.T, yy.T, np.flipud(dem_array), warp_scale=10, colormap='terrain')
# mlab.ylabel(EASTING_COL)
# mlab.xlabel(NORTHING_COL)
# mlab.zlabel('mAHD')

# mlab.outline()
# mlab.show()

