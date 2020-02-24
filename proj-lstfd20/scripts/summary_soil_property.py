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

    def slice_by_window(self, data, px_x, px_y, window_size=3):
        """
        This function slice a big array based on a given window size
        :param data: a 2D numpy array
        :param px_x: int - X-coord of a pixel value or band
        :param px_y: int - Y-coord of a pixel value or band
        :param window_size: int - height and width of window. e.g. 3 means 3 by 3. Must be odd
        :return: a 2D array or None
        """
        if window_size % 2 == 0:  # degrade to lower odd number. eg. 4 => 3
            window_size -= 1
            if window_size < 3:
                window_size = 3

        step = (window_size - 1) // 2
        row_start = px_x - step
        row_stop = px_x + step + 1
        col_start = px_y - step
        col_stop = px_y + step + 1

        res = data[row_start:row_stop, col_start:col_stop]
        if res.shape[0] * res.shape[1] != window_size * window_size:
            return
        return res


url = "/home/eusoj/tmp/test.tif"

tha = CountrySoilProperty(url)
print("offset: ", tha.get_px_coord(104.05, 12.69))
