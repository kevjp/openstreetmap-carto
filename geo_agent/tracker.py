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





class Tracker():

    def __init__(self, dict_current_events, home_location_y, home_location_x, Config, agent_instance = None, *args, **kwargs):

        """
        dict_current_events : dictionary of event instances attached to agent
        home_location_y : lat of home location obtained from Agent.lat
        home_location_x : long of home location obtained from Agent.long
        Config : Instantiated Configuration class
        self.route_matrix is a numpy array with following columns:
            0 : current view of array (current row being processed) 1 = current view otherwise 0
            1 : Event start time
            2 : self.route index
            3 : distance travelled
            4 : Journey in progress 1 = in progress 0 = complete
            5 : Time at event location

        """

        self.agent_events = dict_current_events
        self.sorted_events_list = []
        self.home_location_y = home_location_y
        self.home_location_x = home_location_x
        self.agent = agent_instance
        self.route = []
        # initialise list of waypoints for entire trip chaining all agents events.
        # Initialise list with agent's home location
        self.waypoint_list = [(self.home_location_y, self.home_location_x)]

        self.projectlon_lat_2_utm = pyproj.Proj(proj='utm', zone=30, ellps='WGS84', preserve_units=True)

        # Load_populations.database.cursor.execute("select osm_id, attributes -> 'lon' as lon, attributes -> 'lat' as lat, svals(slice(tags, ARRAY['leisure','shop'])) from osm_nodes where tags -> 'shop' = 'supermarket' or tags -> 'leisure' = 'park';")

        # load osm_nodes table into memory
        self.osm_nodes_np_arr = osm_nodes_np_arr
        self.osm_waysvertex_np_arr = osm_waysvertex_np_arr

        # initialise subpopulation numpy array relating to loaded agents
        self.config = Config







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

    def _find_nearest(self, lat = None, lon = None, amenity = None):

        amenity = amenity.split('=')[1]
        # slice relevant part of array
        self.slice_array(lat, lon, tag = amenity)
        # t1 = time.time()
        # self._nearest(lat, lon, self.sliced_array)

        lat_nearest, lon_nearest = _nearest(lat, lon, self.sliced_array) # coordinate of nearest amenity

        # find nearest way vertex to location
        bounds_test = _buffer_line(lat_nearest, lon_nearest) # find bounds to slice vertex array
        slice_osm_waysvertex_np_arr = self.osm_waysvertex_np_arr[((self.osm_waysvertex_np_arr[:,1]> bounds_test[3][1]) & (self.osm_waysvertex_np_arr[:,1]< bounds_test[1][1]) & (self.osm_waysvertex_np_arr[:,2]> bounds_test[2][0]) & (self.osm_waysvertex_np_arr[:,2]< bounds_test[0][0]))]
        self.osm_ways_id, self.lat, self.lon = c_nearest_v2(lat_nearest, lon_nearest, self.osm_waysvertex_np_arr)





    def sort_eventtimes(self):
        """
        Filter out events which are not due to occur then
        sort event instance for agent by starttime
        """
        filter_events = {item[0]: item[1] for item in self.agent_events.items() if item[1].time_before_event_repeat > 0}
        self.sorted_events_list = [v for k, v in sorted(filter_events.items(), key=lambda item: item[1].starttime)]



    def join_event_routes(self, start_event = None, start_lat = None, start_lon = None, dest_event_instance = None, route_matrix_row = 0):
        """
        Input
        dest_event_instance :  a destination event instance object
        """

        start_event = start_event if start_event else self.agent
        start_lat = start_lat if start_lat else self.home_location_y
        start_lon = start_lon if start_lon else self.home_location_x

        # For events not involving random movement
        if dest_event_instance.event_OSM_search_term:
            # find nearest amenity to start location
            self._find_nearest(lat = start_lat, lon = start_lon, amenity = dest_event_instance.event_OSM_search_term)


            # append event location to waypoint list
            self.waypoint_list.append((float(self.lat), float(self.lon)))

            # set current event OSM way location and id within destination event instance
            dest_event_instance.lat = float(self.lat)
            dest_event_instance.lon = float(self.lon)
            dest_event_instance.osm_ways_id = self.osm_ways_id


            self.route.append(self._calculate_route(start_event.osm_ways_id, self.osm_ways_id))
        # if self.random_movement:
        #     self._random_route(start_vertex, time = 10, speed = 50)


        #initialise self.route_matrix so that first row of matrix is the active row
        self.route_matrix[0,0] = 1

        self.route_matrix[route_matrix_row,1] = dest_event_instance.starttime.astype("float")
        self.route_matrix[route_matrix_row,2] = len(self.route) -1
        self.route_matrix[route_matrix_row,3] = 100
        self.route_matrix[0,4] = 1 # set first row to in progress
        self.route_matrix[route_matrix_row,5] =  dest_event_instance.time_at_event.astype("float")




    def go_home(self, start_event = None, route_matrix_row = 0):
        """
        Calculate route from start event to home location and update waypoint list with home location
        """
        # append home location as agent will return home before next event
        self.waypoint_list.append((self.home_location_y, self.home_location_x))

        # Generate route point list from previous event to home location
        self.route.append(self._calculate_route(start_event.osm_ways_id, self.agent.osm_ways_id))

        self.route_matrix[route_matrix_row,1] = -1 # to be defined on the fly as the numpy array is iterated over during tstep
        self.route_matrix[route_matrix_row,2] = len(self.route) -1
        self.route_matrix[route_matrix_row,3] = 100
        self.route_matrix[route_matrix_row,5] = -1 # # to be defined on the fly as the numpy array is iterated over during tstep


    def count_route_number(self, time_threshold = 120):
        """
        Count the number of Linestring routes based on whether events are joined together or happen in isolation


        """
        # First leg of journey from home to event 1
        self.route_count = 1
        for i, event_tuple in enumerate(zip(self.sorted_events_list, self.sorted_events_list[1:])):
            # convert time difference to minutes
            delta_time = ((event_tuple[1].starttime - event_tuple[0].starttime)/ np.timedelta64(1, 'm'))
            if delta_time < time_threshold:
                # increase route count by 1 event i to event i+1
                self.route_count += 1

            else:
                # increase route count by 1 event i to home
                # increase route count by 1 event i to event i+1
                self.route_count += 2
        # increase route count by 1 to account for return home leg of journey
        self.route_count += 1

        # Initialise route list
        self.route_matrix = np.zeros((self.route_count,6))



    def generate_route_waypoints(self, time_threshold = 120):
        """
        Calculates route waypoints based on nearest amenity and then uses these
        location lat, lon translates them to osm_ways_ids and calculates routes
        between the two location.
        Joins all events for each agent instanc into a signle route object

        self.waypoint_list : contains an ordered list of locations in the time
        order that they are to be visited

        self.sorted_events_list : is a specifc event instance for the corresponding
        agent

        self.route = list of linestrings for all stages of the routes taken by
        the agent instance

        self.lat, self.lon are lat lon coordinates returned by the function _find_nearest()
        self.osm_ways_id is the osm ways id returned by the function _find_nearest()


        """

        # Run function only if there are available events to be calculated
        if self.sorted_events_list:
            # Initialise self.route_matrix by calculating the number of route legs to be generated based on whether events are to be joined together or happen in isolation
            self.count_route_number()

            # define first part of route relative to home location join_event_routes() defaults to home location as start point
            self.join_event_routes(dest_event_instance = self.sorted_events_list[0])
            route_matrix_row = 0
            for i, event_tuple in enumerate(zip(self.sorted_events_list, self.sorted_events_list[1:])):
                # convert time difference to minutes
                delta_time = ((event_tuple[1].starttime - event_tuple[0].starttime)/ np.timedelta64(1, 'm'))
                if delta_time < time_threshold:
                    route_matrix_row += 1
                    # define location relative to location of previous event
                    self.join_event_routes(start_event = self.sorted_events_list[i], start_lat = self.lat, start_lon = self.lon, dest_event_instance = self.sorted_events_list[i + 1], route_matrix_row = route_matrix_row)


                else:
                    route_matrix_row += 1
                    # calculate route info from event to home location of agent
                    self.go_home(start_event = self.sorted_events_list[i], route_matrix_row = route_matrix_row)

                    route_matrix_row += 1
                    # define location relative to home
                    self.join_event_routes(dest_event_instance = self.sorted_events_list[i + 1], route_matrix_row = route_matrix_row)



            # final destination is set to home
            route_matrix_row += 1
            # calculate route info from event to home location of agent
            self.go_home(start_event = self.sorted_events_list[i + 1], route_matrix_row = route_matrix_row)
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
            4 : Journey in progress 1 = in progress 0 = complete
            5 : Time at event location
        """
        if self.route_matrix is not None:
            # merge all linestrings together into one
            current_view_row_idx = np.where(self.route_matrix[:,0] == 1)
            #  Check length of the index array relates to a single row
            try:
                current_view_row_idx[0].shape[0] == 1
            except IndexError as e:
                print("current_view_row_idx should relate to a single index relating to the current relevant row self.route_matrix.")
                raise e

            next_idx = current_view_row_idx[0] + 1

            current_view = self.route_matrix[self.route_matrix[:,0] == 1]
            # Move agent a single tstep if the journey status is 'in progress'
            if current_view[0,4] == 1:
                # update distance travelled by agent
                utm = self.route[int(current_view[0,2])].interpolate(current_view[0,3])

                self.route_matrix[current_view_row_idx,3] = self.route_matrix[current_view_row_idx,3] + 100 # need to change so it is in line with speed


                # convert location back to lon lat coord system and update agent instance and subpopulation array used for plotting
                self.agent.current_lon, self.agent.current_lat = self.projectlon_lat_2_utm(utm.x, utm.y, inverse=True)
                # update sub_population array for plotting purposes
                self.config.point_plots_matrix[int(self.agent.id),0] = Point(self.agent.current_lon, self.agent.current_lat)

                # Change journey status to 'complete' once end point of journey linestring has been reached
                if (utm.x == self.route[int(current_view[0,2])].coords[-1][0]) & (utm.y == self.route[int(current_view[0,2])].coords[-1][1]):
                    self.route_matrix[current_view_row_idx,4] = 0 # journey complete
                    # If Agent is infected with COVID check if they have arrived home and if so remove subsequent events (agent.current_state = 0 'healthy', 1 'infected', 2 'recovered', 3 'dead')
                    # Convert array output to integer index for list
                    current_idx = current_view_row_idx[0].shape[0]
                    if (self.agent.current_state == 1) & ((self.home_location_y, self.home_location_x) == self.waypoint_list[current_idx]):
                        print("Need to check if infected are in home location")
                        self.route_matrix = None
                        self.waypoint_list = []
                        self.route = []

            else:

                # If this is the last row of the event object then the time spent at event is set to -1 so erase route objects
                if self.route_matrix[current_view_row_idx,5] == -1:
                    self.route_matrix = None
                    self.waypoint_list = []
                    self.route = []
                else:
                    # update time at event location subtract 1 tstep unit
                    self.route_matrix[current_view_row_idx,5] = current_view[0,5] - 1 # needs updating for tstep units

                    # Once time at location has reached zero move on to next leg of journey
                    if self.route_matrix[current_view_row_idx,5] == 0:
                        # Make current row of route_matrix inactive and activate the next row
                        self.route_matrix[current_view_row_idx,0] = 0
                        next_idx = current_view_row_idx[0] + 1
                        # update next row of self.route_matrix (no need to check if this is the last row as this is checked by "if self.route_matrix[current_view_row_idx,5] == -1" statement)
                        self.route_matrix[next_idx,0] = 1
                        self.route_matrix[next_idx,4] = 1


    def _random_route(self, start_vertex, time = 10, speed = 50):
        """
        generate a random route for an agent based on a specific amount of time
        start_vertex : is the OSM ways vertex id where agent starts ie. nearest vertex to agent
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
        try:
            Load_populations.database.cursor.execute(query1)
            route_list = [wkb.loads(row[0], hex=True) for row in Load_populations.database.cursor]
        except:
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








    def find_route(self, start, end):
        """
        start : OSM ways id
        end : OSM ways id
        return polypoint route object

        """

        self.curs.execute("SELECT seq, edge, ST_AsText(b.the_geom) AS \"the_geom (truncated)\", b.name FROM pgr_dijkstra('SELECT gid as id, source_osm as source, target_osm as target, length as cost FROM ways',%s, %s, false) a INNER JOIN ways b ON (a.edge = b.gid) ORDER BY seq;", [start, target])
        route_iterator = iter(self.curs)

        return route_iterator
