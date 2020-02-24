import xarray as xr


def slice_by_window(data, px_x, px_y, window_size=3):
    """
    This function slice a big array based on a given window size
    :param data: a 2D numpy array
    :param px_x: int - X-coord of a pixel value or band
    :param px_y: int - Y-coord of a pixel value or band
    :param window_size: int - height and width of window. e.g. 3 means 3 by 3. Must be odd
    :return: a 2D array or None
    """
    if window_size % 2 == 0: # degrade to lower odd number. eg. 4 => 3
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
