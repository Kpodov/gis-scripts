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
dir_types = [bds_dir, cla_dir, org_dir, san_dir]


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


def compute_pwp_row(col):
    """

    :param col: pandas col
    :return:
    """
    clay_val = col['clay']
    oc_val = col['organicsoil']
    sand_val = col['sandfraction']

    return compute_pwp(clay_val, oc_val, sand_val)


def compute_pwp(clay_val, oc_val, sand_val):
    """
    Calculate permanent wilting point based on Clay, Organic Matter and sand value
    :param clay_val: percentage of clay
    :param oc_val: percentage of organic carbon
    :param sand_val: percentage of sand
    :return: a float value representing PWP
    """

    # Step #1 - convert OC to OM
    om_val = 2 * oc_val
    om_val /= 1000
    clay_val /= 100
    sand_val /= 100

    # Step #2 - compute theta_1500_t
    theta_1500_t = 0.031 - (0.024 * sand_val) + (0.487 * clay_val) + (0.006 * om_val) \
                   + (0.005 * sand_val * om_val) - (0.013 * clay_val * om_val) + (0.068 * sand_val * clay_val)

    # Step #3 - finally compute theta_1500
    theta_1500 = (1.14 * theta_1500_t) - 0.02

    return round(theta_1500, 2)


def compute_fc_row(col):
    """

    :param col: pandas col
    :return:
    """
    clay_val = col['clay']
    oc_val = col['organicsoil']
    sand_val = col['sandfraction']

    return compute_field_capacity(clay_val, oc_val, sand_val)


def compute_field_capacity(clay_val, oc_val, sand_val):
    """
    Calculate Field Capacity based on Clay, Organic Matter and sand value
    :param clay_val: percentage of clay
    :param oc_val: percentage of organic carbon
    :param sand_val: percentage of sand
    :return: a float value representing FC
    """

    # Step #1 - convert OC to OM
    om_val = 2 * oc_val
    om_val /= 1000
    clay_val /= 100
    sand_val /= 100

    # Step #2 - compute theta_33_t
    theta_33_t = 0.299 - (0.251 * sand_val) + (0.195 * clay_val) + (0.011 * om_val) \
                 + (0.006 * sand_val * om_val) - (0.027 * clay_val * om_val) + (0.452 * sand_val * clay_val)

    # Step #3 - compute actual F.C: theta_33
    theta_33 = theta_33_t + ((1.283 * theta_33_t * theta_33_t) - (0.374 * theta_33_t) - 0.015)

    return round(theta_33, 2)


def compute_taw(fc, pwp, depth):
    """
    Compute total available water
    :param fc: Field capacity
    :param pwp: permanent wilting point
    :param depth: depth of soil in mm
    :return: a float value for TAW
    """

    return depth * (fc - pwp)


def setup(lat, lon, window, depth=0):
    """

    :param lat: latitude
    :param lon: longitude
    :param window: window size. e.g. 3 means 3 by 3
    :param depth: depth of soil in mm
    :return: pandas dataframe
    """
    global dir_types

    depth_values = [10, 90, 200, 300, 400, 1000]

    if depth != 0:
        depth_possible = [abs(x - 500) for x in depth_values]
        min_diff = min(depth_possible)
        min_index = depth_possible.index(min_diff)
        depth = depth_values[min_index]

    else:
        depth = depth_values[0]

    # you could change the lat long in the following:
    dict_summary = average_per_type(dir_types, lat, lon, window)

    # make a dataframe
    df_summary = dict_to_df(dict_summary)

    # rename the indexes
    row_names = ['10mm', '100mm', '300mm', '600mm', '1000cm', '2000mm']
    df_summary.index = row_names

    # divide current bulk density values by 100
    df_summary['bulkdensity'] = round(df_summary['bulkdensity'] / 100, 2)
    df_summary = round(df_summary, 2)

    # df_calc = pd.DataFrame(columns=['FC', 'PWP', 'TAW'], index=row_names)
    # df_summary = df_summary.join(df_calc)

    df_summary['FC'] = df_summary.apply(compute_fc_row, axis=1)
    df_summary['PWP'] = df_summary.apply(compute_pwp_row, axis=1)

    # export dataframe as csv
    # ascfile = 'sample_asc.csv'
    # df_to_asc(df_summary, ascfile)

    print(df_summary)
    print(depth)


def main():
    setup(102.765, 13.369, 3, 200)


if __name__ == '__main__':
    main()
