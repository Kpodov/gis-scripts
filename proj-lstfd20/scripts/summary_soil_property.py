import glob
import os
import gdal
import osr
import pandas as pd

# Paths
script_dir = os.getcwd()
parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir))
layers_dir = parent_dir + '/layers/'
country_dir = layers_dir + 'country/'
globe_dir = layers_dir + 'globe/*.tif'
globe_dir = glob.glob(globe_dir)
soilp_dir = layers_dir + 'soilproperties/'
bds_dir = soilp_dir + 'bulkdensity/THA/*.tif'
cla_dir = soilp_dir + 'clay/THA/*.tif'
org_dir = soilp_dir + 'organicsoil/THA/*.tif'
san_dir = soilp_dir + 'sandfraction/THA/*.tif'


class CountrySoilProperty(object):

    def __init__(self, fname):
        """

        :param fname: a GTif file
        """

        self.raster = gdal.Open(fname)
        spatial_ref = osr.SpatialReference(self.raster.GetProjection())

        # retrieve get the WGS84 spatial reference
        wgs_ref = osr.SpatialReference()
        wgs_ref.ImportFromEPSG(4326)

        # Do a coordinate transform
        self.coord_transf = osr.CoordinateTransformation(wgs_ref, spatial_ref)

        # Apply geo-transformation and its inverse
        self.raster_gt = self.raster.GetGeoTransform()
        self.raster_inv_gt = gdal.InvGeoTransform(self.raster_gt)

        # Handle error from Inverse function
        if gdal.VersionInfo()[0] == '1':
            if self.raster_inv_gt[0] == 1:
                self.raster_inv_gt = self.raster_inv_gt[1]
            else:
                raise RuntimeError('Inverse geotransform failed')
        elif self.raster_inv_gt is None:
            raise RuntimeError('Inverse geotransform failed')

    def get_px_coord(self, lon, lat):
        """
        Convert lon-lat into x-y coordinates of pixel
        :param lon: longitude
        :param lat: latitude
        :return: tuple of pixel coordinates
        """
        offsets_coord = gdal.ApplyGeoTransform(self.raster_inv_gt, lon, lat)
        px_x, px_y = map(int, offsets_coord)

        return px_x, px_y

    def get_band_array(self):
        """

        :return: 2D array of the rater file
        """
        return self.raster.GetRasterBand(1).ReadAsArray()

    def get_band_value(self, lon, lat):
        """
        Extract the pixel value at a given position
        :param lon: lon
        :param lat: lat
        :return: int - pixel value
        """
        px_x, px_y = self.get_px_coord(lon, lat)

        return self.get_band_array()[px_y, px_x]

    def average_by_window(self, lon, lat, window_size=3):
        """
        This function slice a big array based on a given window size
        :param data: a 2D numpy array
        :param lon: longitude
        :param lat: latitude
        :param window_size: int - height and width of window. e.g. 3 means 3 by 3. Must be odd
        :return: float value, the average or mean of the array or -99 if invalid
        """
        array = self.slice_by_window(lon, lat, window_size)
        if array is None:
            return -99
        return round(array.mean(), 2)

    def slice_by_window(self, lon, lat, window_size):
        """
        This function slice a big array based on a given window size
        :param data: a 2D numpy array
        :param lon: longitude
        :param lat: latitude
        :param window_size: int - height and width of window. e.g. 3 means 3 by 3. Must be odd
        :return: a 2D array or None
        """
        px_x, px_y = self.get_px_coord(lon, lat)

        if window_size % 2 == 0:  # degrade to lower odd number. eg. 4 => 3
            window_size -= 1
            if window_size < 3:
                window_size = 3

        step = (window_size - 1) // 2
        row_start = px_x - step
        row_stop = px_x + step + 1
        col_start = px_y - step
        col_stop = px_y + step + 1
        data = self.get_band_array()
        res = data[row_start:row_stop, col_start:col_stop]
        if res.shape[0] * res.shape[1] != window_size * window_size:
            return
        return res


def average_per_layer(dir_path, lon, lat, window_size):
    """

    :param dir_path:
    :param lon:
    :param lat:
    :param window_size:
    :return:
    """
    list_avg = []
    dir_path = glob.glob(dir_path)

    for tf in dir_path:
        co = CountrySoilProperty(tf)
        avg = co.average_by_window(lon, lat, window_size)
        list_avg.append(avg)

    return list_avg


def average_per_type(dir_path, lon, lat, window_size):
    """

    :param dir_path:
    :param lon:
    :param lat:
    :param window_size:
    :return:
    """
    dict_avg = {}
    for path in dir_path:
        key = path.split('/')[-3]
        list_avg = average_per_layer(path, lon, lat, window_size)

        if key not in dict_avg:
            dict_avg[key] = list_avg

    return dict_avg


def dict_to_df(dict_name):
    """

    :param dict_name:
    :return:
    """
    return pd.DataFrame.from_dict(dict_name)


def df_to_asc(dfname, outname):
    """

    :param dfname:
    :return:
    """
    dfname.to_csv(outname, sep='\t', encoding='utf-8', index=False)

# Main
dir_types = [bds_dir, cla_dir, org_dir, san_dir]

# you could change the lat long in the following:
dict_summary = average_per_type(dir_types, 102.765, 13.369, 3)

# make a dataframe
df_summary = dict_to_df(dict_summary)

# rename the indexes
row_names = ['0cm', '10cm', '30cm', '60cm', '100cm', '200cm']
df_summary.index = row_names

# divide current bulk density values by 100
df_summary['bulkdensity'] = round(df_summary['bulkdensity'] / 100, 2)
df_summary = round(df_summary, 2)

# export dataframe as csv
ascfile = 'sample_asc.csv'
df_to_asc(df_summary, ascfile)

print(df_summary)
