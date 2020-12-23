from glob import glob
import os

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely import wkt
from shapely.geometry import Point, Polygon

from motion import get_motion_parameters
from utils import check_folder


def initialize_population(speed, pop_size, mean_age=45, max_age=105,
                          xbounds=[0, 1], ybounds=[0, 1],
                          household_data = './data/barnet_points_2.csv'):
    '''initialized the population for the simulation
    the population matrix for this simulation has the following columns:
    0 : unique ID
    1 : current x coordinate
    2 : current y coordinate
    3 : current heading in x direction
    4 : current heading in y direction
    5 : current speed
    6 : current state (0=healthy, 1 = infected, 3 = recovered, 4 = dead)
    7 : age
    8 : infected_since (frame the person got infected)
    9 : recovery vector (used in determining when someone recovers or dies)
    10 : in treatment
    11 : active destination (0 = random wander, 1 = go home, 2 = go to the supermarket, 3 = go to the park .. = destination matrix index)
    12 : at destination: whether arrived at destination (0=traveling, 1=arrived)
    13 : wander_range_x : wander ranges on x axis for those who are confined to a location
    14 : wander_range_y : wander ranges on y axis for those who are confined to a location
    15 : last home (the number of frames since last home)
    16 : length of time before next visit to supermarket
    17 : length of time before next visit to park
    18 : length of time to remain at current destination
    Keyword arguments
    -----------------
    pop_size : int
        the size of the population
    mean_age : int
        the mean age of the population. Age affects mortality chances
    max_age : int
        the max age of the population
    xbounds : 2d array
        lower and upper bounds of x axis
    ybounds : 2d array
        lower and upper bounds of y axis
    household_data : str to path of household csv file
    '''

    # feed in household data csv file contains initial point locations within an area of London
    household_df = pd.read_csv(household_data, delimiter=',')
    # convert from pandas to geodataframe
    household_df['geometry'] = household_df['geometry'].apply(wkt.loads)
    household_df_geo = gpd.GeoDataFrame(household_df, geometry='geometry')

    pop_size = household_df.shape[0]


    #initialize population matrix
    population = np.zeros((pop_size, 19))

    #initalize unique IDs
    population[:,0] = [x for x in range(pop_size)]

    # initialise coordinates to Points within London boroughs
    population[:,1] = household_df_geo.geometry.x.values

    population[:,2] = household_df_geo.geometry.y.values


    #initialize random headings -1 to 1

    rangex = xbounds[1] - xbounds[0]
    center_x = xbounds[0] + ((xbounds[1] - xbounds[0])/2)
    population[:,3] = np.random.normal(loc = center_x, scale = rangex/3,
                                       size=(pop_size,))

    rangey = ybounds[1] - ybounds[0]
    center_y = ybounds[0] + ((ybounds[1] - ybounds[0])/2)
    population[:,4] = np.random.normal(loc = center_y, scale = rangey/3,
                                       size=(pop_size,))

    #initialize random speeds
    population[:,5] = np.random.normal(speed, speed / 3)

    #initalize ages
    std_age = (max_age - mean_age) / 3
    population[:,7] = np.int32(np.random.normal(loc = mean_age,
                                                scale = std_age,
                                                size=(pop_size,)))

    population[:,7] = np.clip(population[:,7], a_min = 0,
                              a_max = max_age) #clip those younger than 0 years

    #build recovery_vector
    population[:,9] = np.random.normal(loc = 0.5, scale = 0.5 / 3, size=(pop_size,))

    # mark all individuals as arrived initially
    # population[:,12] = 1

    return population



def initialize_destination_matrix(pop_size, total_destinations):
    '''intializes the destination matrix

    function that initializes the destination matrix used to
    define individual location and roam zones for population members

    Keyword arguments
    -----------------
    pop_size : int
        the size of the population

    total_destinations : int
        the number of destinations to maintain in the matrix. Set to more than
        one if for example people can go to work, supermarket, home, etc.
    '''

    destinations = np.zeros((pop_size, total_destinations * 2))

    return destinations


def get_random_point_in_polygon(poly):
     minx, miny, maxx, maxy = poly.bounds
     while True:
         p = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
         if poly.contains(p):
             return p.x, p.y



def set_destination_bounds(population, destinations, polygon,
                           dest_no=1, teleport=True):
    '''teleports all persons within limits

    Function that takes the population and coordinates,
    teleports everyone there, sets destination active and
    destination as reached

    Keyword arguments
    -----------------
    population : ndarray
        the array containing all the population information

    destinations : ndarray
        the array containing all the destination information

    xmin, ymin, xmax, ymax : int or float
        define the bounds on both axes where the individual can roam within
        after reaching the defined area

    dest_no : int
        the destination number to set as active (if more than one)

    teleport : bool
        whether to instantly teleport individuals to the defined locations
    '''

    #teleport
    if teleport:
        random_points_x = [get_random_point_in_polygon() for _ in range(len(population))]
        population[:,1] = np.append(list(list(zip(*random_points_x))[0]))
        population[:,2] = np.append(list(list(zip(*random_points_x))[1]))


    #get parameters
    x_center, y_center, x_wander, y_wander = get_motion_parameters(xmin, ymin,
                                                                   xmax, ymax)

    #set destination centers
    destinations[:,(dest_no - 1) * 2] = x_center
    destinations[:,((dest_no - 1) * 2) + 1] = y_center

    #set wander bounds
    population[:,13] = x_wander
    population[:,14] = y_wander

    population[:,11] = dest_no #set destination active
    population[:,12] = 1 #set destination reached

    return population, destinations

def save_data(population, pop_tracker):
    '''dumps simulation data to disk

    Function that dumps the simulation data to specific files on the disk.
    Saves final state of the population matrix, the array of infected over time,
    and the array of fatalities over time

    Keyword arguments
    -----------------
    population : ndarray
        the array containing all the population information

    infected : list or ndarray
        the array containing data of infections over time

    fatalities : list or ndarray
        the array containing data of fatalities over time
    '''
    num_files = len(glob('data/*'))
    check_folder('data/%i' %num_files)
    np.save('data/%i/population.npy' %num_files, population)
    np.save('data/%i/infected.npy' %num_files, pop_tracker.infectious)
    np.save('data/%i/recovered.npy' %num_files, pop_tracker.recovered)
    np.save('data/%i/fatalities.npy' %num_files, pop_tracker.fatalities)


def save_population(population, tstep=0, folder='data_tstep'):
    '''dumps population data at given timestep to disk

    Function that dumps the simulation data to specific files on the disk.
    Saves final state of the population matrix, the array of infected over time,
    and the array of fatalities over time

    Keyword arguments
    -----------------
    population : ndarray
        the array containing all the population information

    tstep : int
        the timestep that will be saved
    '''
    check_folder('%s/' %(folder))
    np.save('%s/population_%i.npy' %(folder, tstep), population)


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
