# cython: cdivision=True
# cython: profile=True
from libc.math cimport sin, cos, asin, atan2, M_PI, sqrt, INFINITY
import numpy as np
cimport numpy as np
from subpopulations import Load_populations




#cdef class Nearest:

def _buffer_line(double current_lat, double current_lon, int d = 5):
    """
    Defines the upper and lower limits of lat and lon coordinates in order slice osm_nodes table
    May need to speed this up in Cython
    """


    cdef:
        double R = 6378.1 #Radius of the Earth
        double lat1
        double lon1
        double lat2_rad
        double lon2_rad
        double lat2
        double lon2
        double coord_list[4][2]
        double *br_list = [0, 1.57, 3.142, 4.712]

    lat1 = (current_lat * M_PI / 180.0) #Current lat point converted to radians
    lon1 = (current_lon * M_PI / 180.0) #Current long point converted to radians

    for i in range(4):

        lat2_rad = asin( sin(lat1) * cos(d/R) + cos(lat1) * sin(d/R) * cos(br_list[i]))

        lon2_rad = lon1 + atan2(sin(br_list[i]) * sin(d/R) * cos(lat1), cos(d/R) - sin(lat1) * sin(lat2_rad))

        lat2 = lat2_rad * 180.0 / M_PI
        lon2 = lon2_rad * 180.0 / M_PI

        coord_list[i] = [lat2, lon2]

    return coord_list


cpdef double _points_distance(double start_lat, double start_lon, double stop_lat, double stop_lon):

    cdef:
        double R = 6378.1 #Radius of the Earth
        double dlat
        double dlon
        double v_a
        double v_c

    dlat = stop_lat - start_lat # difference in lat direction
    dlon = stop_lon - start_lon # difference in lon direction
    dlat *= (M_PI / 180.0) # convert to radians
    dlon *= (M_PI / 180.0) # convert to radians
    start_lat *= (M_PI / 180.0) # convert to radians
    stop_lat *= (M_PI / 180.0) # convert to radians


    v_a = sin(dlat/2) * sin(dlat/2) + cos(start_lat) * cos(stop_lat) * sin(dlon/2) * sin(dlon/2)

    v_c = 2 * atan2(sqrt(v_a),sqrt(1-v_a))

    return R * v_c



cpdef _nearest(double lat, double lon, arr):

    cdef:
        int idx
        int arr_max = arr.shape[0]
    coord_list = np.zeros((arr.shape[0]))

    for i in range(arr_max):
        coord_list[i] = _points_distance(lat, lon, arr['lat'][i], arr['lon'][i])
    idx = np.argmin(coord_list)
    return arr['lat'][idx], arr['lon'][idx]



DTYPE = np.float64

ctypedef np.float64_t DTYPE_t

cpdef c_nearest(double lat, double lon, double[:, :] arr):
# cdef c_nearest(double lat, double lon, np.ndarray[DTYPE_t, ndim=2] arr):


    cdef:
        int idx
        double lat_nearest
        double lon_nearest
        int arr_max = arr.shape[0]
        np.ndarray[DTYPE_t, ndim=1] coord_arr = np.zeros(arr_max, dtype=DTYPE)
        double[:] coord_arr_view = coord_arr


    for i in range(arr_max):
        coord_arr_view[i] = _points_distance(lat, lon, arr[i][2], arr[i][1])
    idx = np.argmin(coord_arr)

    lat_nearest, lon_nearest =  arr[idx][2], arr[idx][1]

    return lat_nearest, lon_nearest

cpdef c_nearest_v2(double lat, double lon, double[:, :] arr):


    cdef:
        int idx
        double lat_nearest
        double lon_nearest
        int arr_max = arr.shape[0]
        double shortest = INFINITY



    for i in range(arr_max):
        dist = _points_distance(lat, lon, arr[i][2], arr[i][1])
        if dist < shortest:
            shortest = dist
            osm_ways_id, lat_nearest, lon_nearest = arr[i][0], arr[i][2], arr[i][1]

    return osm_ways_id, lat_nearest, lon_nearest


def run_nearest(double lat, double lon, arr):
    print(arr.shape)
    lat_nearest, lon_nearest = c_nearest(lat, lon, arr)
    return lat_nearest, lon_nearest













    # def slice_array(self, start_lat, start_lon, array_in = None, tag = "supermarket"):
    #         """
    #         Slice relevant rows relating to area bounding box from osm_nodes table

    #         """
    #         # default sql table is the osm_nodes table
    #         if array_in is None:
    #             array_in = self.osm_nodes_np_arr

    #         bounds = self._buffer_line(start_lat, start_lon)

    #         self.sliced_array = array_in[(array_in['tags'] == tag) & ((array_in['lon'] > bounds[3][1]) & (array_in['lon'] < bounds[1][1])) & ((array_in['lat'] > bounds[2][0]) & (array_in['lat'] < bounds[0][0]))]

    # def _nearest(self, start_lat, start_lon, arr):

    #     tup_candidates = arr[['lat', 'lon']]
    #     # print(tup_candidates.shape)
    #     # print(tup_candidates.shape[0])
    #     start_up = [(start_lat, start_lon)] * tup_candidates.shape[0]
    #     # print(start_up)
    #     dt=np.dtype('float,float')
    #     start_arr = np.array(start_up, dtype=dt)
    #     # print(start_arr.shape)
    #     # print(start_arr)
    #     # vectorise distance function for ease of readability
    #     vect_dist_func = np.vectorize(geopy.distance.vincenty)
    #     vals = vect_dist_func(start_arr, tup_candidates)
    #     # find index of nearest amenity
    #     val = np.argmin(np.array([dist.km for dist in vals]))
    #     lat, lon = arr['lat'][val], arr['lon'][val]
    #     # Convert node coordinate to ways coordinate
    #     self.xy2osm(lat = lat, lon = lon)

    # def _find_nearest(self, lat = None, lon = None, amenity = None):

    #     amenity = amenity.split('=')[1]
    #     # slice relevant part of array
    #     self.slice_array(lat, lon, tag = amenity)

    #     self._nearest(lat, lon, self.sliced_array)