# -*- coding: utf-8 -*-
from glob import glob
import os
from config_geo import Configuration

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely import wkt
from shapely.geometry import Point, Polygon

from motion import get_motion_parameters
from utils import check_folder
from random import randint

from generate_probabilities import Generate_location_probs
from database import Database
import pyproj



class Load_populations(Configuration):

    """
    Class to load subpopulations into simulations via csv files.


    Can supply key word argument to class Load_populations(household_data = '/Users/kevinryan/Documents/City_DSI/population_movement_simulations/geo_agent/config/barnet_points_2.csv'
                                                            locations = ['supermarket', 'park'])
    Can add additional parameterisation at later date


    """

    # connect to osm database
    database = Database()
    # database = Database(name = 'gis', user = 'postgres', host = 'db')

    def __init__(self, *args, **kwargs):

        # Inherit init from everything from Configuration class
        super().__init__()


        self.household_data = kwargs.get('household_data')

        # feed in household data csv file contains initial point locations within an area of London
        self.household_df = pd.read_csv(self.household_data, delimiter=',')
        # convert from pandas to geodataframe
        self.household_df['geometry'] = self.household_df['geometry'].apply(wkt.loads)
        self.household_df_geo = gpd.GeoDataFrame(self.household_df, geometry='geometry')

        self.pop_size = self.household_df.shape[0]

        #initialize population matrix
        self.sub_population = np.zeros((self.pop_size, 10))
        # initalize point_plots_matrix
        self.point_plots_matrix = np.zeros((self.pop_size, 2), dtype=object)

        #initalize unique IDs
        self.sub_population[:,0] = [x for x in range(self.pop_size)]
        #initalize subpopulation ID (generate a random integer between 1-10000)
        self.sub_population[:,1] = randint(0,10000)

        # Translate home input coordinates into OSM ways coordinates
        self.translate_2_osm_ways_coords(lat = self.household_df_geo.geometry.y.values, lon = self.household_df_geo.geometry.x.values)

        # N.B. assinging the integer to numpy array means the int value is changed to a float
        self.sub_population[:,2] = self.osm_ways_list

        # initialise coordinates to Points within London boroughs
        self.sub_population[:,3] = self.nearest_lat_list

        self.sub_population[:,4] = self.nearest_lon_list

        # convert lat lon to utm projection (tuple (utm.x,utm.y))

        projectlon_lat_2_utm = pyproj.Proj(proj='utm', zone=30, ellps='WGS84', preserve_units=True)
        self.sub_population[:,[5,6]] = np.array([projectlon_lat_2_utm(lat, lon) for lat, lon in zip(self.nearest_lat_list, self.nearest_lon_list)])


        self.max_age = 105
        self.mean_age = 45

        #initalize ages
        std_age = (self.max_age - self.mean_age) / 3
        self.sub_population[:,7] = np.int32(np.random.normal(loc = self.mean_age,
                                                scale = std_age,
                                                size=(self.pop_size,)))

        self.sub_population[:,7] = np.clip(self.sub_population[:,7], a_min = 0,
                              a_max = self.max_age) #clip those younger than 0 years

        # initialize which agents are infected randomly with specified percentage of starting population infected (healthy =0 , infected = 1, recovered = 2, death = 3)
        self.sub_population[:,8] = self.random_assign_zero_ones(array_size = self.pop_size)

        #build recovery_vector
        self.sub_population[:,9] = np.random.normal(loc = 0.5, scale = 0.5 / 3, size=(self.pop_size,))

        # Generate numpy matrix for plotting points using leaflet realtime. These points are outputted to /openstreetmap-carto/output.json
        self.point_plots_matrix[:,0] = self.nearest_point_convert
        self.point_plots_matrix[:,1] = self.sub_population[:,8]
        # self.point_plots_matrix[:,1] = ["sample"] * self.pop_size


    def random_assign_zero_ones(self, list_of_values = [0, 1, 2, 3], array_size= 1000, prob_list = [.9, .1, 0, 0]):
        """
        generates numpy array of zeros and ones at a defined ratio specified by prob_list argument [proportion of zeros (healthy), proportion of ones (infected), proportion of twos (recovered), proportion of threes (dead)]

        """
        nums = np.random.choice(list_of_values, size=array_size, p=prob_list)
        return nums



    def translate_2_osm_ways_coords(self, lat = None, lon = None):

        """
        lat : list of lat values
        lon : list of lon values
        Translate input coordinates into OSM ways coordinates
        """

        self.osm_ways_list = []
        self.nearest_lat_list = []
        self.nearest_lon_list = []
        self.nearest_point_convert = []
        for coord in zip(lat, lon):
            self.xy2osm(lat = coord[0], lon = coord[1]) # generates variables self.osm_ways_id, self.lon, self.lat
            self.osm_ways_list.append(self.osm_ways_id) # used to populate osm ways id column
            self.nearest_lat_list.append(self.lat) # used to populate lat column
            self.nearest_lon_list.append(self.lon) # used to populate lon column
            self.nearest_point_convert.append(Point(self.lon, self.lat)) # used to populate current position column (needs to be a Point object for plotting)



    def xy2osm(self, lat = None, lon = None):

        """
        translate long, lat values to a tuple containing (lon, lat, OSM ways ID)
        tuple
        """

        # Will allow me to translate all locations into adjacent vertices points in ways table
        # selects the nearest OSM reference in OSM ways table to the required location as defined by the points returned from nearest amenity search (<-> is the distance operator)
        Load_populations.database.cursor.execute("select * from ways_vertices_pgr ORDER BY the_geom <-> ST_GeometryFromText('POINT(%s %s)',4326);", (lon, lat))

        # translate into OSM ref
        h = (next(Load_populations.database.cursor))
        self.osm_ways_id, self.lon, self.lat = (h[1], float(h[3]), float(h[4]))




# PLACEHOLDER WILL NEED TO BUILD THIS OUT AS A TRACKER FOR SIR PLOTS
class Population_trackers():
    '''class used to track population parameters

    Can track population parameters over time that can then be used
    to compute statistics or to visualise.

    TODO: track age cohorts here as well
    '''
    def __init__(self):
        self.susceptible = []
        self.infectious = []
        self.recovered = []
        self.fatalities = []

        #PLACEHOLDER - whether recovered individual can be reinfected
        self.reinfect = False

    def update_counts(self, population):
        '''docstring
        '''
        pop_size = population.shape[0]
        self.infectious.append(len(population[population[:,6] == 1]))
        self.recovered.append(len(population[population[:,6] == 2]))
        self.fatalities.append(len(population[population[:,6] == 3]))

        if self.reinfect:
            self.susceptible.append(pop_size - (self.infectious[-1] +
                                                self.fatalities[-1]))
        else:
            self.susceptible.append(pop_size - (self.infectious[-1] +
                                                self.recovered[-1] +
                                                self.fatalities[-1]))











