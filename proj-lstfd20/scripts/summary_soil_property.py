import gdal
import osr


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
        :return: int value, the average or mean of the array or -99 if invalid
        """
        array = self.slice_by_window(lon, lat, window_size)
        if array is None:
            return -99
        return int(array.mean())

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


url = "/home/eusoj/tmp/test.tif"

tha = CountrySoilProperty(url)
print("Value: \n", tha.average_by_window(103.460, 12.420, 7))
