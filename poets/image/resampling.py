# Copyright (c) 2014, Vienna University of Technology (TU Wien), Department
# of Geodesy and Geoinformation (GEO).
# All rights reserved.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL VIENNA UNIVERSITY OF TECHNOLOGY,
# DEPARTMENT OF GEODESY AND GEOINFORMATION BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# Author: Thomas Mistelbauer Thomas.Mistelbauer@geo.tuwien.ac.at
# Creation date: 2014-06-13

import numpy as np
import pandas as pd
import pyresample as pr
import poets.grid.grids as gr
import poets.image.netcdf as nc
from poets.grid.shapes import Shape
from poets.settings import Settings
from pytesmo.grid import resample
from shapely.geometry import Polygon, Point


def _create_grid():
    """
    Generates regular grid based on spatial resolution set in constants.py

    Returns
    -------
    grid : grids.BasicGrid
        regular grid
    """

    if Settings.sp_res == 0.01:
        grid = gr.HundredthDegGrid(setup_kdTree=False)
    elif Settings.sp_res == 0.1:
        grid = gr.TenthDegGrid(setup_kdTree=False)
    elif Settings.sp_res == 0.25:
        grid = gr.TenthDegGrid(setup_kdTree=False)
    elif Settings.sp_res == 1:
        grid = gr.OneDegGrid(setup_kdTree=False)

    return grid


def resample_to_shape(source_file, country, prefix=None):
    """
    Resamples images and clips country boundaries

    Parameters
    ----------
    source_file : str
        path to source file
    country : str
        FIPS country code (https://en.wikipedia.org/wiki/FIPS_country_code)

    Returns
    -------
    data : dict of numpy.arrays
        resampled image
    lons : numpy.array
        longitudes of the points in the resampled image
    lats : numpy.array
        latgitudes of the points in the resampled image
    gpis : numpy.array
        grid point indices
    timestamp : datetime.date
        date of the image
    """

    if prefix is not None:
        prefix += '_'

    shp = Shape(country)

    data, src_lon, src_lat, timestamp = nc.clip_bbox(source_file,
                                                     shp.bbox[0],
                                                     shp.bbox[1],
                                                     shp.bbox[2],
                                                     shp.bbox[3],
                                                     country=country)

    src_lon, src_lat = np.meshgrid(src_lon, src_lat)
    grid = gr.CountryGrid(country)

    dest_lon, dest_lat = np.meshgrid(np.unique(grid.arrlon),
                                     np.unique(grid.arrlat)[::-1])

    gpis = grid.get_bbox_grid_points(grid.arrlat.min(), grid.arrlat.max(),
                                     grid.arrlon.min(), grid.arrlon.max())

    data = resample.resample_to_grid(data, src_lon, src_lat, dest_lon,
                                     dest_lat)

    mask = np.zeros(shape=grid.shape, dtype=np.bool)

    poly = Polygon(shp.polygon)

    for i in range(0, grid.shape[0]):
        for j in range(0, grid.shape[1]):
            p = Point(dest_lon[i][j], dest_lat[i][j])
            if p.within(poly) == False:
                mask[i][j] = True
            if data[data.keys()[0]].mask[i][j] == True:
                mask[i][j] = True

    for key in data.keys():
        var = prefix + key
        data[var] = np.ma.masked_array(data[key], mask=mask, fill_value=-99)
        dat = np.copy(data[var].data)
        dat[data[var].mask == True] = -99
        data[var] = np.ma.masked_array(dat, mask=mask, fill_falue=-99)
        del data[key]

    return data, dest_lon, dest_lat, gpis, timestamp


def resample_to_gridpoints(source_file, country):
    """
    resamples image to the predefined grid

    Parameters
    ----------
    source_file : str
        path to source file
    country : str
        latitudes of source image

    Returns
    -------
    dframe : pandas.DataFrame
        resampled data with gridpoints as index
    """

    grid = _create_grid()

    gridpoints = gr.getCountryPoints(grid, country)
    shp = Shape(country)

    data, lon, lat = nc.clip_bbox(source_file, shp.bbox[0], shp.bbox[1],
                                  shp.bbox[2], shp.bbox[3])

    lon, lat = np.meshgrid(lon, lat)

    src_grid = pr.geometry.GridDefinition(lon, lat)
    des_swath = pr.geometry.SwathDefinition(gridpoints['lon'].values,
                                            gridpoints['lat'].values)

    dframe = pd.DataFrame(index=gridpoints.index)
    dframe['lon'] = gridpoints.lon
    dframe['lat'] = gridpoints.lat

    # resampling to country gridpoints
    for var in data.keys():
        dframe[var] = pr.kd_tree.resample_nearest(src_grid, data[var],
                                                  des_swath, 20000)

    return dframe
