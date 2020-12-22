import numpy as np
import overpy
import psycopg2
from subpopulations import Load_populations

from shapely import geometry, ops, wkb
from shapely.geometry import Point, LineString, shape
import pyproj
import math
import geopy.distance
import time
from buffer import _buffer_line, _points_distance, _nearest, run_nearest, c_nearest, c_nearest_v2
from osm_tables import osm_nodes_np_arr, osm_waysvertex_np_arr
import random
from utils import _closest_point_on_way





class Tracker():

    def __init__(self, Load_populations_instance, agent_instance, clock_instance = None, *args, **kwargs):

        """
        dict_current_events : dictionary of event instances attached to agent
        home_location_y : lat of home location obtained from Agent.lat
        home_location_x : long of home location obtained from Agent.long
        Load_populations : Instantiated Load_populations class
        self.route_matrix is a numpy array with following columns:
            0 : current view of array (current row being processed) 1 = current view otherwise 0
            1 : Event start time
            2 : self.route index
            3 : distance travelled
            4 : Journey in progress 1 = in progress 0 = complete
            5 : Time at event location
            6 : Index of event added from self.sorted_events_list (-100 if no event added eg rows which relate to deafult behavour of the agent returning home)

        """

        self.sorted_events_list = []
        self.agent = agent_instance
        self.route = []
        # initialise list of waypoints for entire trip chaining all agents events.
        # Initialise list with agent's home location
        self.waypoint_list = [(self.start_lat, self.start_lon)]

        self.projectlon_lat_2_utm = pyproj.Proj(proj='utm', zone=30, ellps='WGS84', preserve_units=True)

        # Load_populations.database.cursor.execute("select osm_id, attributes -> 'lon' as lon, attributes -> 'lat' as lat, svals(slice(tags, ARRAY['leisure','shop'])) from osm_nodes where tags -> 'shop' = 'supermarket' or tags -> 'leisure' = 'park';")

        # load osm_nodes table into memory
        self.osm_nodes_np_arr = osm_nodes_np_arr
        self.osm_waysvertex_np_arr = osm_waysvertex_np_arr

        # initialise subpopulation numpy array relating to loaded agents
        self.config = Load_populations_instance

        # defines how the events in current_events are joined options are "default", "sequence"
        self.join_events = "default"
        # Clock Instance contains info on current time of run
        self.clock_instance = clock_instance


    # Allows agent and load_population instance varaibles to be accesed insided tracker instance useing the same variable calls
    def __getattr__(self, attr):
        if attr == "__setstate__":
            raise AttributeError(attr)
        if hasattr(self.agent, attr):
            return getattr(self.agent, attr)
        else:
            return getattr(self.config, attr)



    def latlon_2_yx(self, lat=None, lon=None):

        """
        Converts WGS84 lat lon values to UTM
        """
        # Project lon lat coordinates into UTM scale
        return self.projectlon_lat_2_utm(lat, lon)


    def yx_2_latlon(self, y,x):
        """
        Converts y,x UTM values to WGS84 lat, lon
        """
        # Project UTM y, x values to lon lat
        return self.projectlon_lat_2_utm(lat, lon, inverse=True)




    def _buffer_line(self, current_lat, current_lon, br_list = [0, 1.57, 3.142, 4.712], d = 5):
        """
        Defines the upper and lower limits of lat and lon coordinates in order slice osm_nodes table
        May need to speed this up in Cython
        """
        R = 6378.1 #Radius of the Earth
        # br_list is 0, 90, 180, 270 degrees converted to radians.

        lat1 = math.radians(current_lat) #Current lat point converted to radians
        lon1 = math.radians(current_lon) #Current long point converted to radians
        # d = 15 #Distance in km
        coord_list =[]
        for br in br_list:
            lat2 = math.asin( math.sin(lat1)*math.cos(d/R) +
             math.cos(lat1)*math.sin(d/R)*math.cos(br))

            lon2 = lon1 + math.atan2(math.sin(br)*math.sin(d/R)*math.cos(lat1),
                     math.cos(d/R)-math.sin(lat1)*math.sin(lat2))

            lat2 = math.degrees(lat2)
            lon2 = math.degrees(lon2)
            coord_list.append((lat2, lon2))
        return coord_list

    def slice_array(self, start_lat, start_lon, array_in = None, tag = "supermarket"):
        """
        Slice relevant rows relating to area bounding box from osm_nodes table

        """
        # default sql table is the osm_nodes table
        if array_in is None:
            array_in = self.osm_nodes_np_arr
        # t1 = time.time()
        bounds = _buffer_line(start_lat, start_lon)
        # t2 = time.time()
        # total = t2 - t1
        # print("_buffer_line total", total)

        self.sliced_array = array_in[(array_in['tags'] == tag) & ((array_in['lon'] > bounds[3][1]) & (array_in['lon'] < bounds[1][1])) & ((array_in['lat'] > bounds[2][0]) & (array_in['lat'] < bounds[0][0]))]

    # def _nearest(self, start_lat, start_lon, arr):

    #     tup_candidates = arr[['lat', 'lon']]
    #     # print("tupshape",tup_candidates.shape)
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
    #     # 51.656011, -0.203959 Waitrose Barnet
    #     # 51.655425, -0.195505 Home

    #     d = _points_distance(51.655425, -0.195505, 51.656011, -0.203959)
    #     print("distance from _points_distance", d)
    #     self.xy2osm(lat = lat, lon = lon)


    def _find_nearest_v2(self, lat = None, lon = None, amenity = None):
        """

        Find nearest point to amenity returning nearest osm_ways_id, lat and lon
        Returns a Generator object
        """

        amenity = amenity.strip()
        amenity = amenity.replace(" ","")
        amenity_key = amenity.split('=')[0]
        amenity_value = amenity.split('=')[1]
        print("find_nearest inputs", lat, lon, amenity)
        # SELECT ST_AsText(ST_ClosestPoint(line,pt)) As cp_line_pt FROM (SELECT 'POINT(-0.1687473308241547 51.66176239080847)'::geography::geometry As pt, (select the_geom from osm_ways where osm_id = (select ow.osm_id from osm_ways ow where ow.tags -> 'leisure' = 'park' order by ow.the_geom <-> (SELECT 'SRID=4326;POINT(-0.1687473308241547 51.66176239080847)'::geometry) limit 1)) As line) As foo;
        # query = f"SELECT ST_X(ST_ClosestPoint(aline,pt)), ST_Y(ST_ClosestPoint(aline,pt)) As cp_line_pt FROM (SELECT 'POINT({lon} {lat})'::geography::geometry As pt, (select the_geom from osm_ways where osm_id = (select ow.osm_id from osm_ways ow where ow.tags -> '{amenity_key}' = '{amenity_value}' order by ow.the_geom <-> (SELECT 'SRID=4326;POINT({lon} {lat})'::geometry) limit 1)) As aline) As output;"

        query = f"select ow.osm_id from osm_ways ow where ow.tags -> '{amenity_key}' = '{amenity_value}' order by ow.the_geom <-> (SELECT 'SRID=4326;POINT({lon} {lat})'::geometry);"
        # Generate fresh cursor that will not be overwritten by cursor used in _calculate_route function
        nearest_curs = Load_populations.database.connection.cursor()
        nearest_curs.execute(query)
        # results contains osm_ids of closest ways to the inputted amenities. Each id can be accessed using next()
        results = nearest_curs

        print(type(results), results)
        for result in results:
            # Find closest point for entered way osm_id - can't combine with query above as I need perform this query per single osm_id entry
            # Generate a second database cursor so as not to overwrite the query defined in results variable in this for loop
            subcurs = Load_populations.database.connection.cursor()
            # retrive closet point on a defined way geometry and assign to Event class attributes self.lon, self.lat
            lon, lat = _closest_point_on_way(data_base_cursor = subcurs, osm_id = result[0], lon = lon, lat = lat)

            # return  corrdinate of nearest vertex and osm way id
            osm_way_id, source_node_osm_way_id, target_node_osm_way_id = self.xy2osm(lon = lon, lat = lat)
            # Return closest point on retrieved road from way table (way table only contains road networrk whereas osm_ways also contains unconnected ways around buildings/ features etc.)
            lon, lat = _closest_point_on_way(data_base_cursor = subcurs, osm_id = osm_way_id, lon = lon, lat = lat)
            yield osm_way_id, source_node_osm_way_id, target_node_osm_way_id, lon, lat

        # results = list(Load_populations.database.cursor)[0]
        # nearest_lon, nearest_lat = results[0], results[1]
        # print("nearest_lon", nearest_lon, "nearest_lat", nearest_lat)
        # # return  corrdinate of nearest vertex and osm way id
        # osm_ways_id, lon, lat = self.xy2osm(lat = nearest_lat, lon = nearest_lon)
        # return osm_ways_id, lon, lat


    def _find_nearest(self, lat = None, lon = None, amenity = None):

        """
        Find nearest point to amenity returning nearest osm_ways_id, lat and lon
        """

        # Find coordinate of amenity nearest to inputted lat and lon
        amenity = amenity.split('=')[1]
        # slice relevant part of array
        self.slice_array(lat, lon, tag = amenity)
        # t1 = time.time()
        # self._nearest(lat, lon, self.sliced_array)

        lat_nearest, lon_nearest = _nearest(lat, lon, self.sliced_array) # coordinate of nearest amenity

        # find nearest way vertex to location
        bounds_test = _buffer_line(lat_nearest, lon_nearest) # find bounds to slice vertex array
        slice_osm_waysvertex_np_arr = self.osm_waysvertex_np_arr[((self.osm_waysvertex_np_arr[:,1]> bounds_test[3][1]) & (self.osm_waysvertex_np_arr[:,1]< bounds_test[1][1]) & (self.osm_waysvertex_np_arr[:,2]> bounds_test[2][0]) & (self.osm_waysvertex_np_arr[:,2]< bounds_test[0][0]))]
        self.osm_way_id, self.lat, self.lon = c_nearest_v2(lat_nearest, lon_nearest, self.osm_waysvertex_np_arr)





    def sort_eventtimes(self):
        """
        Filter out events which are not due to occur then
        sort event instance for agent by starttime
        """
        # For any startimes that are not defined then default to current time
        for item in self.current_events.items():
            if item[1].starttime == None:
                item[1].starttime = self.clock_instance.current_time

        filter_events = {item[0]: item[1] for item in self.current_events.items() if item[1].time_before_event_repeat >= 0}
        self.sorted_events_list = [v for k, v in sorted(filter_events.items(), key=lambda item: item[1].starttime)]





    def join_event_routes(self, start_event = "home", start_lat = None, start_lon = None, dest_event_instance = "home", route_matrix_row = 0):
        """
        Input
        start_event = None (if starting from non-event location), "home" (if starting from home location of agent) or an event_instance which contains as associated osm_ways_id
        dest_event_instance :  a destination event instance object containing a event_OSM_search_term attribute
        """
        # Define start location
        if start_event is None:
            # Determine osm_ways id for starting location
            start_osm_way_id, start_source_node_osm_way_id, start_target_node_osm_way_id = self.xy2osm(lat = self.current_lat, lon = self.current_lon)
            # Calculate nearest point on way object as defined by osm_way_id
            start_lon, start_lat = _closest_point_on_way(data_base_cursor = Load_populations.database.cursor, osm_id = start_osm_way_id, lon = self.current_lon, lat = self.current_lat)
            # convert lon at to utm coordinate system
            start_utmx, start_utmy = self.projectlon_lat_2_utm(start_lon, start_lat)
            print("start_osm_way_id, start_utmx, start_utmy", start_osm_way_id, start_utmx, start_utmy)

        elif start_event == "home":
            # Set home location for attached agent
            start_lat = self.start_lat
            start_lon = self.start_lon
            start_utmx = self.utm_x
            start_utmy = self.utm_y
            print("self.start_source_node_osm_way_id, self.utm_x, self.utm_y", self.start_source_node_osm_way_id, self.utm_x, self.utm_y)
            # start_osm_way_id = self.start_osm_way_id
            start_source_node_osm_way_id = self.start_source_node_osm_way_id
            start_target_node_osm_way_id = self.start_target_node_osm_way_id

        else:
            # Set start location based on start event
            # Determine osm_ways id for starting location
            # start_osm_way_id = start_event.osm_way_id
            start_source_node_osm_way_id = start_event.source_node_osm_way_id
            start_target_node_osm_way_id = start_event.target_node_osm_way_id
            start_lat = start_event.lat
            start_lon= start_event.lon
            start_utmx = start_event.utmx
            start_utmy = start_event.utmy


        # Define destination location and calulate route
        if dest_event_instance == "home":

            # Set home location for attached agent
            dest_lat = self.start_lat
            dest_lon = self.start_lon
            dest_utmx = self.utm_x
            dest_utmy = self.utm_y
            # dest_osm_way_id = self.start_osm_way_id
            dest_source_node_osm_way_id = self.start_source_node_osm_way_id
            dest_target_node_osm_way_id = self.start_target_node_osm_way_id


            # append event location to waypoint list
            self.waypoint_list.append((float(dest_lat), float(dest_lon)))

            # calculate route Linestring
            route_linestring = self._calculate_route(start_source_node_osm_way_id, dest_target_node_osm_way_id)
            # Calculate initial distance into Linestring where start point of journey will be
            initial_distance = route_linestring.project(Point(start_utmx, start_utmy))
            print("initial_distance", initial_distance)
            # Calculate final distance into Linestring where end point of journey will be
            final_distance = route_linestring.project(Point(dest_utmx, dest_utmy))
            print("final_distance", final_distance)


            # append route linestring
            self.route.append(route_linestring)

            #initialise self.route_matrix so that first row of matrix is the active row
            self.route_matrix[0,0] = 1
            # Populate route_matrix
            self.route_matrix[route_matrix_row,1] = -1
            self.route_matrix[route_matrix_row,2] = len(self.route) -1
            self.route_matrix[route_matrix_row,3] = initial_distance
            self.route_matrix[route_matrix_row,4] = final_distance
            self.route_matrix[route_matrix_row,5] = -1
            self.route_matrix[route_matrix_row,6] =  -1

        elif dest_event_instance == "random":
            """ Need to build"""
            pass


        else:
        # Specific event relating to a general location has been passed and is defined relative to agent location based on OSM search term

            if dest_event_instance.event_OSM_search_term:

                nearest_coords_gen = self._find_nearest_v2(lat = start_lat, lon = start_lon, amenity = dest_event_instance.event_OSM_search_term)

                route_returned = None
                while route_returned is None:
                    osm_way_id, source_node_osm_way_id, target_node_osm_way_id, lon, lat = next(nearest_coords_gen)

                    # assign values to destination event
                    dest_event_instance.lat = lat
                    dest_event_instance.lon = lon
                    dest_event_instance.osm_way_id = osm_way_id
                    dest_event_instance.source_node_osm_way_id = source_node_osm_way_id
                    dest_event_instance.target_node_osm_way_id = target_node_osm_way_id
                    dest_event_instance.utmx, dest_event_instance.utmy = self.projectlon_lat_2_utm(lon, lat)


                    dest_lat = lat
                    dest_lon = lon
                    dest_utmx = dest_event_instance.utmx
                    dest_utmy = dest_event_instance.utmy
                    dest_osm_way_id = osm_way_id
                    dest_source_node_osm_way_id = source_node_osm_way_id
                    dest_target_node_osm_way_id = target_node_osm_way_id


                    # append event location to waypoint list
                    self.waypoint_list.append((float(dest_lat), float(dest_lon)))
                    # Calculate route but only calculate route if start and end points are different
                    if start_source_node_osm_way_id == dest_target_node_osm_way_id:
                        route_returned = 1
                        print("check order",start_lon, start_lat)
                        self.route.append(LineString([(start_lon, start_lat),(dest_event_instance.lon, dest_event_instance.lat)]))
                        initial_distance = 0
                        final_distance = 0
                    else:

                        route_returned = self._calculate_route(start_source_node_osm_way_id, dest_target_node_osm_way_id)
                        print("calculate route had been calculated......")
                        if route_returned is not None:
                            self.route.append(route_returned)

                            # Calculate initial distance into Linestring where start point of journey will be
                            initial_distance = route_returned.project(Point(start_utmx, start_utmy))
                            # Calculate final distance into Linestring where end point of journey will be
                            final_distance = route_returned.project(Point(dest_utmx, dest_utmy))
                            print("initial_distance", initial_distance)
                            print("start_lon, start_lat", start_lon, start_lat)
                            print("final_distance", final_distance)
                            print("dest_lon, dest_lat", dest_lon, dest_lat)
                            print(list(route_returned.coords))
                            print("route_returned.length", route_returned.length)
                            print("start_utmx start_utmy, start_source_node_osm_way_id", start_utmx, start_utmy, start_source_node_osm_way_id)
                            print("dest_utmx dest_utmy, , dest_target_node_osm_way_id, dest_osm_way_id", dest_utmx, dest_utmy, dest_target_node_osm_way_id, dest_osm_way_id)


                if isinstance(start_event, str) or start_event is None:
                    print("dest_event_instance.source_node_osm_way_id",dest_event_instance.source_node_osm_way_id)

                else:
                    print("start_event.source_node_osm_way_id",start_event.source_node_osm_way_id)
                    print("dest_event_instance.source_node_osm_way_id",dest_event_instance.source_node_osm_way_id)

                #initialise self.route_matrix so that first row of matrix is the active row
                self.route_matrix[0,0] = 1
                # Populate route_matrix
                self.route_matrix[route_matrix_row,1] = dest_event_instance.starttime.astype("float")
                self.route_matrix[route_matrix_row,2] = len(self.route) -1

                self.route_matrix[route_matrix_row,3] = initial_distance
                self.route_matrix[route_matrix_row,4] = final_distance

                self.route_matrix[route_matrix_row,5] = -1
                self.route_matrix[route_matrix_row,6] =  dest_event_instance.time_at_event.astype("float")

            else:

                pass




    def go_home(self, start_event = None, route_matrix_row = 0):
        """
        Calculate route from start event to home location and update waypoint list with home location
        """
        # append home location as agent will return home before next event
        self.waypoint_list.append((self.start_lat, self.start_lon))

        # Generate route point list from previous event to home location
        self.route.append(self._calculate_route(start_event.osm_way_id, self.start_osm_way_id))

        self.route_matrix[route_matrix_row,1] = -1 # to be defined on the fly as the numpy array is iterated over during tstep
        self.route_matrix[route_matrix_row,2] = len(self.route) -1
        self.route_matrix[route_matrix_row,3] = 100
        self.route_matrix[route_matrix_row,5] = -1
        self.route_matrix[route_matrix_row,6] = -1 # # to be defined on the fly as the numpy array is iterated over during tstep


    def count_route_number(self, time_threshold = 120):
        """
        Count the number of Linestring routes based on whether events are joined together or happen in isolation
        self.sorted_events_indices : records the index from self.sorted_events_list of the events passed to self.route_matrix


        """
        # First leg of journey from home to event 1
        self.route_count = 1
        self.sorted_events_indices = []
        self.sorted_events_indices.append(0) # first event relates to home to event 1

        for i, event_tuple in enumerate(zip(self.sorted_events_list, self.sorted_events_list[1:])):
            # convert time difference to minutes
            delta_time = (event_tuple[1].starttime - event_tuple[0].starttime)
            if delta_time < time_threshold:
                # increase route count by 1 event i to event i+1
                self.route_count += 1
                self.sorted_events_indices.append(i + 1)

            else:
                # increase route count by 1 event i to home
                self.sorted_events_indices.append(-100) # no corresponding index from self.sorted_events_list
                # increase route count by 1 home to event i+1
                self.sorted_events_indices.append(i + 1) # append next event index
                self.route_count += 2

        # increase route count by 1 to account for return home leg of journey
        self.route_count += 1
        self.sorted_events_indices.append(-100) # no corresponding index from self.sorted_events_list

        # Initialise route list
        self.route_matrix = np.zeros((self.route_count,8))
        # Append indices for correspinding events from self.sorted_events_list
        self.route_matrix[:,7] = np.array(self.sorted_events_indices)





    def generate_route_waypoints(self, time_threshold = 120):
        """
        Calculates route waypoints based on nearest amenity and then uses these
        location lat, lon translates them to osm_way_ids and calculates routes
        between the two location.
        Joins all events for each agent instanc into a signle route object

        self.waypoint_list : contains an ordered list of locations in the time
        order that they are to be visited

        self.sorted_events_list : is a specifc event instance for the corresponding
        agent

        self.route = list of linestrings for all stages of the routes taken by
        the agent instance

        self.osm_way_id is the osm way id returned by the function _find_nearest()


        """
        # Sort events by starttime
        self.sort_eventtimes()
        # Run function only if there are available events to be calculated
        if self.sorted_events_list:
            # Initialise self.route_matrix by calculating the number of route legs to be generated based on whether events are to be joined together or happen in isolation
            self.count_route_number()

            # define first part of route relative to home location join_event_routes() defaults to home location as start point
            self.join_event_routes(dest_event_instance = self.sorted_events_list[0])

            if len(self.sorted_events_list) > 1:

                route_matrix_row = 0
                for i, event_tuple in enumerate(zip(self.sorted_events_list, self.sorted_events_list[1:])):
                    # convert time difference to minutes
                    delta_time = (event_tuple[1].starttime - event_tuple[0].starttime)
                    # join events if they occur close in time or if the currrent event stipulates not to return home
                    if (delta_time < time_threshold) or (self.sorted_events_list[i].return_home == 0):
                        route_matrix_row += 1
                        # ammend destination event starttime to take into account the joining of the events
                        self.sorted_events_list[i + 1].starttime = self.sorted_events_list[i].starttime + self.sorted_events_list[i].time_at_event

                        # define location relative to location of previous event
                        self.join_event_routes(start_event = self.sorted_events_list[i], dest_event_instance = self.sorted_events_list[i + 1], route_matrix_row = route_matrix_row)


                    else:
                        route_matrix_row += 1
                        # # calculate route info from event to home location of agent
                        # self.go_home(start_event = self.sorted_events_list[i], route_matrix_row = route_matrix_row)

                        ##############
                        # IF THIS WORKS CAN GET RID OF go_home function and just use join_event_routes function for everything
                        self.join_event_routes(start_event = self.sorted_events_list[i], dest_event_instance = "home", route_matrix_row = route_matrix_row)
                        ##############

                        route_matrix_row += 1
                        # define location relative to home
                        self.join_event_routes(dest_event_instance = self.sorted_events_list[i + 1], route_matrix_row = route_matrix_row)

                # Return home from final event
                if self.sorted_events_list[i + 1].return_home == 1:
                    # final destination is set to home
                    route_matrix_row += 1
                    # # calculate route info from event to home location of agent
                    # self.go_home(start_event = self.sorted_events_list[i + 1], route_matrix_row = route_matrix_row)
                    ##############
                    # IF THIS WORKS CAN GET RID OF go_home function and just use join_event_routes function for everything
                    self.join_event_routes(start_event = self.sorted_events_list[i + 1], dest_event_instance = "home", route_matrix_row = route_matrix_row)
                    ##############
            else:
                if self.sorted_events_list[0].return_home == 1:
                    # if len(self.sorted_events_list) == 0 then calculate route back home from single event
                    # calculate route info from event to home location of agent
                    route_matrix_row = 1
                    # self.go_home(start_event = self.sorted_events_list[0], route_matrix_row = route_matrix_row)
                    ##############
                    # IF THIS WORKS CAN GET RID OF go_home function and just use join_event_routes function for everything
                    self.join_event_routes(start_event = self.sorted_events_list[0], dest_event_instance = "home", route_matrix_row = route_matrix_row)
                    ##############

        else:
            self.route_matrix = None




    def route_step(self, speed = None):

        """
        Takes a tstep forward in route list.
        The location on the route is dependent on the speed the agent is travelling at and the length of tstep
        if journey marked in progress then move agent location one tstep along relevant Linestring
        Otherwise reduce time at event location by 1 tstep unit.

        self.route_matrix is a numpy array with following columns:
            0 : current view of array (current row being processed) 1 = current view otherwise 0
            1 : Event start time
            2 : self.route index
            3 : distance travelled
            4 : total distanace to travel
            5 : Journey in progress 1 = in progress 0 = complete -1 = journey not started
            6 : Time at event location
            7 : Index of event added from self.sorted_events_list (-100 if no event added eg rows which relate to deafult behavour of the agent returning home)
        """
        if self.route_matrix is not None:

            print("route matrix =", self.route_matrix)
            print("self.waypoint_list", self.waypoint_list)
            print("self.route", self.route)
            # merge all linestrings together into one
            current_view_row_idx = np.where(self.route_matrix[:,0] == 1)
            #  Check length of the index array relates to a single row
            try:
                current_view_row_idx[0].shape[0] == 1
            except IndexError as e:
                print("current_view_row_idx should relate to a single index relating to the current relevant row self.route_matrix.")
                raise e

            next_idx = current_view_row_idx[0] + 1


            # Pass over event if it is not time for it to occur yet or if the
            print("event time", self.route_matrix[current_view_row_idx[0],1])
            print("clock_instance.current_time in route_step function", self.clock_instance.current_time, "event_time=", self.route_matrix[current_view_row_idx[0],1])
            if self.clock_instance.current_time == self.route_matrix[current_view_row_idx[0],1]:
                # Set to journey in progress
                self.route_matrix[current_view_row_idx,5] = 1

            current_view = self.route_matrix[self.route_matrix[:,0] == 1]
            print("clock_instance.current_time in route_step function", self.clock_instance.current_time, "event_time=", current_view[0,1])

            # if journey status is set at -1 then journey has not started
            if current_view[0,5] == -1:
                pass
            # Move agent a single tstep if the journey status is 'in progress'
            elif current_view[0,5] == 1:

                # update distance travelled by agent
                print("self.route",self.route)
                print("current_view[0,3]", current_view[0,3])
                print("self.route_matrix[current_view_row_idx,3]",self.route_matrix[current_view_row_idx,3])
                print("self.route_matrix[current_view_row_idx,4]", self.route_matrix[current_view_row_idx,4])
                utm = self.route[int(current_view[0,2])].interpolate(current_view[0,3])


                # convert location back to lon lat coord system and update agent instance and subpopulation array used for tracking of infected individuals and onfig.point_plots_matrix used for plotting
                self.current_lon, self.current_lat = self.projectlon_lat_2_utm(utm.x, utm.y, inverse=True)
                # update sub_population array used for tracking infected individuals
                self.sub_population[int(self.id),[6,7]] = np.array([utm.x, utm.y])

                # update config.point_plots_matrix  array for plotting purposes
                self.point_plots_matrix[int(self.id),0] = Point(self.current_lon, self.current_lat)

                # Change journey status to 'complete' once end point of journey linestring has been reached
                if self.route_matrix[current_view_row_idx,3] == self.route_matrix[current_view_row_idx,4]:
                    self.route_matrix[current_view_row_idx,5] = 0 # journey complete
                    # If Agent is infected with COVID check if they have arrived home and if so remove subsequent events (agent.current_state = 0 'healthy', 1 'infected', 2 'recovered', 3 'dead')
                    # Convert array output to integer index for list
                    waypoint_list_idx = current_view_row_idx[0][0] + 1


                    if (self.current_state == 1) & ((self.start_lat, self.start_lon) == self.waypoint_list[waypoint_list_idx]):
                        print("Need to check if infected are in home location")
                        self.route_matrix = None
                        self.waypoint_list = []
                        self.route = []
                else:
                    self.route_matrix[current_view_row_idx,3] = self.route_matrix[current_view_row_idx,3] + 100 # need to change so it is in line with speed
                    # Check if current distance travelled exceeds total distance of journey and if so ammend current distance to total distance value
                    if self.route_matrix[current_view_row_idx,3] > self.route_matrix[current_view_row_idx,4]:
                        self.route_matrix[current_view_row_idx,3] = self.route_matrix[current_view_row_idx,4]

            # journey is not in progress. So agent is spending time at event location. Need to check if this is the last row (last row will have a time spent at event as -1) otherwise countdown time at event destination
            else:

                # If this is the last row of the event object then the time spent at event is set to -1 so erase route objects
                if self.route_matrix[current_view_row_idx,6] == -1:
                    self.route_matrix = None
                    self.waypoint_list = []
                    self.route = []

                else:
                    print("TIME AT EVENT = ", self.route_matrix[current_view_row_idx,6])
                    # update time at event location subtract 1 tstep unit
                    self.route_matrix[current_view_row_idx,6] = current_view[0,6] - 1 # needs updating for tstep units

                    # Once time at location has reached zero move on to next leg of journey
                    if self.route_matrix[current_view_row_idx,6] == 0:
                        # Make current row of route_matrix inactive and activate the next row
                        self.route_matrix[current_view_row_idx,0] = 0

                        # Check if completed event in self.sorted_events_list (any index relating to self.sorted_events_list is an index value greater than zero). For rows relating to returning to home the index value is -100
                        if self.route_matrix[current_view_row_idx,7] >= 0:
                            # Extract relevant event
                            extracted_event = self.sorted_events_list[int(self.route_matrix[current_view_row_idx,7])]

                            # Update agent's event_history dictionary with the completed event. This is required to monitor its time_before_event_repeat variable as event cannot occur again for this agent until time_before_event_repeat has reached 0
                            self.event_history_dict[extracted_event.description] = extracted_event.__dict__ # need to provide it as a dictionary in order for json logic to work

                        next_idx = current_view_row_idx[0] + 1
                        # update next row of self.route_matrix (no need to check if this is the last row as this is checked by "if self.route_matrix[current_view_row_idx,6] == -1" statement)
                        self.route_matrix[next_idx,0] = 1
                        self.route_matrix[next_idx,5] = 1


    def _random_route(self, start_vertex, time = 10, speed = 50):
        """
        generate a random route for an agent based on a specific amount of time
        start_vertex : is the OSM way vertex id where agent starts ie. nearest vertex to agent
        time : number of tsteps spent moving randomly
        speed : distance in meters travelled each tstep
        """
        total_dist_travelled = speed * time

        query = f"select length,st_astext(the_geom) from ways where source_osm = '19191796' or target_osm = '19191796';"
        Load_populations.database.cursor.execute(query)
        list(Load_populations.database.cursor)
        pass




    def _calculate_route(self, start, end):
        """
        This function is called within join_event_routes
        calculates shortest route from two specific locations
        start: OSM way ID
        end: OSM WAY ID
        Returns Linestring object of route
        """
        # make sure all osm ways ids are int values
        start = int(start)
        end = int(end)
        # Using OSM ids as source and target values calculate shortest route and convert to shapely geometric object
        # query = f"SELECT seq, edge, b.the_geom AS \"the_geom (truncated)\" FROM pgr_dijkstra('select gid as id, source_osm as source, target_osm as target, length as cost FROM ways as ways_outer, (select ST_Expand(ST_Extent(the_geom),0.1) as box from ways as box_table where box_table.source_osm = {start} OR box_table.target_osm = {end}) as box_final where ways_outer.the_geom && box_final.box', {start}, {end}, false) as a INNER JOIN ways as b ON a.edge = b.gid ORDER BY seq;"
        # query = f"SELECT UNNEST(pgr_flipedges(ARRAY(SELECT st_astext(b.the_geom) AS \"the_geom (truncated)\" FROM pgr_dijkstra('select gid as id, source_osm as source, target_osm as target, length as cost FROM ways as ways_outer, (select ST_Expand(ST_Extent(the_geom),0.1) as box from ways as box_table where box_table.source_osm = {start} OR box_table.target_osm = {end}) as box_final where ways_outer.the_geom && box_final.box', {start}, {end}, false) as a INNER JOIN ways as b ON a.edge = b.gid ORDER BY seq)));"

        ###### DELETE

        # query = f"SELECT ST_SetSRID(UNNEST(pgr_flipedges(ARRAY(SELECT st_astext(b.the_geom) FROM pgr_dijkstra('select gid as id, source_osm as source, target_osm as target, length as cost FROM ways as ways_outer, (select ST_Expand(ST_Extent(the_geom),0.1) as box from ways as box_table where box_table.source_osm = {start} OR box_table.target_osm = {end}) as box_final where ways_outer.the_geom && box_final.box', {start}, {end}, false) as a INNER JOIN ways as b ON a.edge = b.gid ORDER BY seq))),4326);"
        # Load_populations.database.cursor.execute(query)
        # route_list = [wkb.loads(row[0], hex=True) for row in Load_populations.database.cursor]
        # merged_routes = ops.linemerge([*route_list])
        # print(merged_routes)
        ###### DELETE



        query1 = f"SELECT ST_Transform(ST_SetSRID(UNNEST(pgr_flipedges(ARRAY(SELECT st_astext(b.the_geom) FROM pgr_dijkstra('select gid as id, source_osm as source, target_osm as target, length as cost FROM ways as ways_outer, (select ST_Expand(ST_Extent(the_geom),0.1) as box from ways as box_table where box_table.source_osm = {start} OR box_table.target_osm = {end}) as box_final where ways_outer.the_geom && box_final.box', {start}, {end}, false) as a INNER JOIN ways as b ON a.edge = b.gid ORDER BY seq))),4326), 32630);"
        query2 = f"SELECT ST_Transform(ST_SetSRID(UNNEST(pgr_flipedges(ARRAY(SELECT st_astext(b.the_geom) FROM pgr_dijkstra('select gid as id, source_osm as source, target_osm as target, length as cost FROM ways as ways_outer, (select ST_Expand(ST_Extent(the_geom),0.1) as box from ways as box_table where box_table.source_osm = {end} OR box_table.target_osm = {start}) as box_final where ways_outer.the_geom && box_final.box', {end}, {start}, false) as a INNER JOIN ways as b ON a.edge = b.gid ORDER BY seq))),4326), 32630);"

        print("query1",query1)
        print("query2",query2)
        # This try exept block ensures that database query does not respond an error code
        try:
            Load_populations.database.cursor.execute(query1)
            route_list = [wkb.loads(row[0], hex=True) for row in Load_populations.database.cursor]
            # merge linestrings into one large shapely linestring object
            merged_routes = ops.linemerge([*route_list])
            return merged_routes
        except:
            try:
                # rollback database before executing alternative query
                Load_populations.database.connection.rollback()
                # sometimes the route is only available in one direction
                Load_populations.database.cursor.execute(query2)
                route_list = [wkb.loads(row[0], hex=True) for row in Load_populations.database.cursor]
                # reverse list order
                route_list.reverse()
                # merge linestrings into one large shapely linestring object
                merged_routes = ops.linemerge([*route_list])
                return merged_routes
            except:
                # rollback database before executing alternative query
                Load_populations.database.connection.rollback()
                return None









    def find_nearest(self, lat = None, lon = None, amenity = None):
        """
        This function is called within join_event_routes()
        y : latitude
        x : longitdue
        amenity : str value of amenity to be searched for eg. "leisure=park" or "shop=supermarket"
        Translates node coordinate for nearest ways coordinate
        returns location of ways coordinate as latitude, longitude tuple
        """
        api = overpy.Overpass()
        query = '''(node[%s](around:7000,%s,%s); ); out;''' % (amenity, lat, lon)
        node_obj = api.query(query)
        node_list = node_obj.nodes
        # Convert node coordinate to ways coordinate
        self.xy2osm(lat = node_list[0].lat, lon = node_list[0].lon)

    def find_amenity(self, lat = None, lon = None, amenity = None):
        """
        This function is called within join_event_routes()
        y : latitude
        x : longitdue
        amenity : str value of amenity to be searched for eg. "leisure=park" or "shop=supermarket"
        Translates node coordinate for nearest ways coordinate
        returns location of ways coordinate as latitude, longitude tuple
        """
        api = overpy.Overpass()
        query = '''(way[%s](around:7000,%s,%s); ); out center;''' % (amenity, lat, lon)
        way_obj = api.query(query)
        way_list = way_obj.ways
        # Take the first way object in the list (will need to see how this performs interms of relevance of selected amenity)
        self.osm_way_id =  way_list[0].id
        self.lat = way_list[0].center_lat
        self.lon = way_list[0].center_lon








    def find_route(self, start, end):
        """
        start : OSM way id
        end : OSM way id
        return polypoint route object

        """

        self.curs.execute("SELECT seq, edge, ST_AsText(b.the_geom) AS \"the_geom (truncated)\", b.name FROM pgr_dijkstra('SELECT gid as id, source_osm as source, target_osm as target, length as cost FROM ways',%s, %s, false) a INNER JOIN ways b ON (a.edge = b.gid) ORDER BY seq;", [start, target])
        route_iterator = iter(self.curs)

        return route_iterator
