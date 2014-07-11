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

'''
Defines the grids using pytesmo.grid.grids

Created on Jun 3, 2014

@author: Thomas Mistelbauer Thomas.Mistelbauer@geo.tuwien.ac.at
'''

import pytesmo.grid.grids as grids
import numpy as np
import pandas as pd
import math
from shapely.geometry import Polygon, Point
from poets.grid.shapes import Shape
from poets.settings import Settings


class HundredthDegGrid(grids.BasicGrid):
    """
    Regular 0.1 degree grid with grid middle points at
    (-179.95,-89.95), (-179.85,-89.95) etc.
    """
    def __init__(self, **kwargs):

        londim = np.arange(-179.995, 180, 0.01)
        latdim = np.arange(-89.995, 90, 0.01)
        lon, lat = np.meshgrid(londim, latdim)
        super(HundredthDegGrid, self).__init__(lon.flatten(), lat.flatten(),
                                         shape=lon.shape, **kwargs)


class TenthDegGrid(grids.BasicGrid):
    """
    Regular 0.1 degree grid with grid middle points at
    (-179.95,-89.95), (-179.85,-89.95) etc.
    """
    def __init__(self, **kwargs):

        londim = np.arange(-179.95, 180, 0.1)
        latdim = np.arange(-89.95, 90, 0.1)
        lon, lat = np.meshgrid(londim, latdim)
        super(TenthDegGrid, self).__init__(lon.flatten(), lat.flatten(),
                                         shape=lon.shape, **kwargs)


class QuarterDegGrid(grids.BasicGrid):
    """
    Regular 0.25 degree grid with grid middle points at
    (-179.875,-89.875), (-179.875,-89.875) etc.
    """
    def __init__(self, **kwargs):

        londim = np.arange(-179.875, 180, 0.25)
        latdim = np.arange(-89.875, 90, 0.25)
        lon, lat = np.meshgrid(londim, latdim)
        super(QuarterDegGrid, self).__init__(lon.flatten(), lat.flatten(),
                                             shape=lon.shape, **kwargs)


class OneDegGrid(grids.BasicGrid):
    """
    Regular 0.1 degree grid with grid middle points at
    (-179.5,-89.5), (-179.5,-89.5) etc.
    """
    def __init__(self, **kwargs):

        londim = np.arange(-179.5, 180, 1)
        latdim = np.arange(-89.5, 90, 1)
        lon, lat = np.meshgrid(londim, latdim)
        super(OneDegGrid, self).__init__(lon.flatten(), lat.flatten(),
                                         shape=lon.shape, **kwargs)


class CountryGrid(grids.BasicGrid):
    """
    Regular grid for spedific country, that just has lat,lon coordinates and 
    can find the nearest neighbour. It can also yield the gpi, lat, lon
    information in order.

    Parameters
    ----------
    lon : numpy.array
        longitudes of the points in the grid
    lat : numpy.array
        latitudes of the points in the grid
    gpis : numpy.array, optional
        if the gpi numbers are in a different order than the
        lon and lat arrays an array containing the gpi numbers
        can be given
        if no array is given here the lon lat arrays are given
        gpi numbers starting at 0
    subset : numpy.array, optional
        if the active part of the array is only a subset of
        all the points then the subset array which is a index
        into lon and lat can be given here
    setup_kdTree : boolean, optional
        if set (default) then the kdTree for nearest neighbour
        search will be built on initialization
    shape : tuple, optional
        if given the grid can be reshaped into the given shape
        this indicates that it is a regular grid and fills the
        attributes self.londim and self.latdim which
        define the grid only be the meridian coordinates(self.londim) and
        the coordinates of the circles of latitude(self.latdim).
        The shape has to be given as (latdim, londim)
        It it is not given the shape is set to the length of the input
        lon and lat arrays.
    country : str
        optional; FIPS country code:
        https://en.wikipedia.org/wiki/FIPS_country_code
    resolution : float
        optional; spatial resolution of the grid

    Attributes
    ----------
    arrlon : numpy.array
        array of all longitudes of the grid
    arrlat : numpy.array
        array of all latitudes of the grid
    n_gpi : int
        number of gpis in the grid
    gpidirect : boolean
        if true the gpi number is equal to the index
        of arrlon and arrlat
    gpis : numpy.array
        gpi number for elements in arrlon and arrlat
        gpi[i] is located at arrlon[i],arrlat[i]
    subset : numpy.array
        if given then this contains the indices of a subset of
        the grid. This can be used if only a part of a grid is
        interesting for a application. e.g. land points, or only
        a specific country
    allpoints : boolean
        if False only a subset of the grid is active
    activearrlon : numpy.array
        array of longitudes that are active, is defined by
        arrlon[subset] if a subset is given otherwise equal to
        arrlon
    activearrlat : numpy.array
        array of latitudes that are active, is defined by
        arrlat[subset] if a subset is given otherwise equal to
        arrlat
    activegpis : numpy.array
        array of gpis that are active, is defined by
        gpis[subset] if a subset is given otherwise equal to
        gpis
    issplit : boolean
        if True then the array was split in n parts with
        the self.split function
    kdTree : object
        grid.nearest_neighbor.findGeoNN object for
        nearest neighbor search
    shape : tuple, optional
        if given during initialization then this is
        the shape the grid can be reshaped to
        this only makes sense for regular lat,lon grids
    latdim : numpy.array, optional
        if shape is given this attribute has contains
        all latitudes that make up the regular lat,lon grid
    londim : numpy.array, optional
        if shape is given this attribute has contains
        all longitudes that make up the regular lat,lon grid
    country : str
        FIPS country code:
        https://en.wikipedia.org/wiki/FIPS_country_code
    resolution : float
        spatial resolution of the grid
    shp : poets.grid.shapes.Country
        Information about the country/region shape
    """

    def __init__(self, country, resolution=Settings.sp_res):

        self.country = country

        self.shp = Shape(country)

        lonmin, lonmax = _minmaxcoord(self.shp.bbox[0], self.shp.bbox[2])
        latmin, latmax = _minmaxcoord(self.shp.bbox[1], self.shp.bbox[3])

        lons = np.arange(lonmin, lonmax + Settings.sp_res, Settings.sp_res)
        lats = np.arange(latmin, latmax + Settings.sp_res, Settings.sp_res)

        lon_new, lat_new = _remove_blank_frame(country, lons, lats)

        lon, lat = np.meshgrid(lon_new, lat_new)

        super(CountryGrid, self).__init__(lon.flatten(), lat.flatten(),
                                          shape=lon.shape)

    def get_country_gridpoints(self):
        """
        Gets all points within a country shape. Removes all gridpoints that are
        within country bounding box, but outside of the country itself.

        Returns
        -------
        points : pd.DataFrame
            GPI as index, lat and lon as columns
        """

        box = self.get_bbox_grid_points(self.shp.bbox[1], self.shp.bbox[3],
                                        self.shp.bbox[0], self.shp.bbox[2])
        poly = Polygon(self.shp.polygon)

        lons = []
        lats = []
        pts = []

        for gpi in box:
            lon, lat = self.gpi2lonlat(gpi)
            if poly.contains(Point(lon, lat)):
                pts.append(gpi)
                lons.append(lon)
                lats.append(lat)

        points = pd.DataFrame({'lon': lons, 'lat': lats}, pts)

        return points


def _remove_blank_frame(country, lons, lats):
    """
    Removes longitutes and latitudes without points in country shape

    Parameters
    ----------
    country : str
        FIPS country code (https://en.wikipedia.org/wiki/FIPS_country_code)
    lons : numpy.ndarray
        Array with longitudes
    lats : numpy.ndarray
        Array with latitudes

    Retrurns
    --------
    lon_new : list of floats
        updated list of longitudes
    lat_new : list of floats
        updated list of latitudes
    """

    shp = Shape(country)

    poly = Polygon(shp.polygon)

    del_lons = []
    del_lats = []

    # left boundary check
    for i, x in enumerate(lons[:(lons.size / 2)]):
        checksum = 0
        for y in lats:
            p = Point(x, y)
            if p.within(poly) == False:
                checksum += 1
        if checksum == lats.size:
            del_lons.append(i)
        else:
            break

    # right boundary check
    for i, x in enumerate(lons[::-1][:(lons.size / 2)]):
        checksum = 0
        for y in lats:
            p = Point(x, y)
            if p.within(poly) == False:
                checksum += 1
        if checksum == lats.size:
            del_lons.append(lons.size - 1 - i)
        else:
            break

    # bottom boundary check
    for i, y in enumerate(lats[:(lats.size / 2)]):
        checksum = 0
        for x in lons:
            p = Point(x, y)
            if p.within(poly) == False:
                checksum += 1
        if checksum == lons.size:
            del_lats.append(i)
        else:
            break

    # top boundary check
    for i, y in enumerate(lats[::-1][:(lats.size / 2)]):
        checksum = 0
        for x in lons:
            p = Point(x, y)
            if p.within(poly) == False:
                checksum += 1
        if checksum == lons.size:
            del_lats.append(lats.size - 1 - i)
        else:
            break

    lon_new = lons.tolist()
    lat_new = lats.tolist()

    for i in del_lons:
        if lons[i] in lon_new:
            lon_new.remove(lons[i])

    for i in del_lats:
        if lats[i] in lat_new:
            lat_new.remove(lats[i])

    return lon_new, lat_new


def _minmaxcoord(min_threshold, max_threshold):
    """
    Gets min and max coordinates of a specific grid, based on the frame of a
    global grid.

    Parameters
    ----------
    min_threshold : float
        minimum value of coordinate
    max_threshold : float
        maximum value of coordinate

    Returns
    -------
    minval : float
        updated minimum coordinate
    maxval : float
        updated maximum coordinate
    """

    res = float(Settings.sp_res)

    minval = int(math.ceil(min_threshold / res)) * res
    maxval = int(math.floor(max_threshold / res)) * res

    if minval - (res / 2) < min_threshold:
        minval += res / 2
    else:
        minval -= res / 2

    if maxval + (res / 2) > max_threshold:
        maxval -= res / 2
    else:
        maxval += res / 2

    return minval, maxval