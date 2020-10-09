'''
file that contains all configuration related methods and classes
'''
# -*- coding: utf-8 -*-
import numpy as np
from population_geo import initialize_population
import pandas as pd
from shapely import wkt
import geopandas as gpd
# import googlemaps

# import overpy


class config_error(Exception):
    pass


class Configuration():
    def __init__(self, *args, **kwargs):
        # Population dictionary to hold all subpopulations key = [subpopulation_id]
        self.pop_dict = {}
        # Dictionary storing probability distribution of visiting a location for different subpopulations key = [location_subpopulation_id]
        self.prob_of_visiting_dict = {}
        # Dictionary storing clock time value distributions of visiting a location in a single day period for different subpopulations key = [location_subpopulation_id]
        self.time_of_visit_dict = {}

        #simulation variables
        self.verbose = True #whether to print infections, recoveries and fatalities to the terminal
        self.simulation_steps = 10000 #total simulation steps performed
        self.tstep = 0 #current simulation timestep
        self.save_data = False #whether to dump data at end of simulation
        self.save_pop = False #whether to save population matrix every 'save_pop_freq' timesteps
        self.save_pop_freq = 10 #population data will be saved every 'n' timesteps. Default: 10
        self.save_pop_folder = 'pop_data/' #folder to write population timestep data to
        self.endif_no_infections = True #whether to stop simulation if no infections remain

        #scenario flags
        self.traveling_infects = False
        self.self_isolate = False
        self.lockdown = False
        self.lockdown_percentage = 0.1 #after this proportion is infected, lock-down begins
        self.lockdown_compliance = 0.95 #fraction of the population that will obey the lockdown

        #world variables, defines where population can and cannot roam
        self.xbounds = [0, 0]
        self.ybounds = [0, 0]
        # set boundary on map these relates to the boundary area of possible regions any point can wander in
        self.xbounds[0], self.ybounds[0], self.xbounds[1], self.ybounds[1] = self.set_bounds()


        #visualisation variables
        self.visualise = True #whether to visualise the simulation
        self.plot_mode = 'sir' #default or sir
        #size of the simulated world in coordinates
        self.x_plot = [0, 1]
        self.y_plot = [0, 1]
        self.save_plot = False
        self.plot_path = 'render/' #folder where plots are saved to
        self.plot_style = 'default' #can be default, dark, ...
        self.colorblind_mode = False
        #if colorblind is enabled, set type of colorblindness
        #available: deuteranopia, protanopia, tritanopia. defauld=deuteranopia
        self.colorblind_type = 'deuteranopia'

        #population variables
        self.pop_size = 2000
        self.mean_age = 45
        self.max_age = 105
        self.age_dependent_risk = True #whether risk increases with age
        self.risk_age = 55 #age where mortality risk starts increasing
        self.critical_age = 75 #age at and beyond which mortality risk reaches maximum
        self.critical_mortality_chance = 0.1 #maximum mortality risk for older age
        self.risk_increase = 'quadratic' #whether risk between risk and critical age increases 'linear' or 'quadratic'

        #movement variables
        #mean_speed = 0.01 # the mean speed (defined as heading * speed)
        #std_speed = 0.01 / 3 #the standard deviation of the speed parameter
        #the proportion of the population that practices social distancing, simulated
        #by them standing still
        proportion_distancing = 0
        self.speed = 0.01 #average speed of population
        self.speed_dict = {}
        self.speed_dict['walking'] = 0.083
        self.speed_dict['car'] = 0.805
        self.speed_dict['public_transport'] = 0.705
        #when people have an active destination, the wander range defines the area
        #surrounding the destination they will wander upon arriving
        self.wander_range = 0.05
        self.wander_factor = 1
        self.wander_factor_dest = 1.01 #area around destination

        #infection variables
        self.infection_range=0.02 #range surrounding sick patient that infections can take place  set to around 2m
        self.infection_chance=0.1   #chance that an infection spreads to nearby healthy people each tick
        self.recovery_duration=(200, 500) #how many ticks it may take to recover from the illness
        self.mortality_chance=0.02 #global baseline chance of dying from the disease

        #healthcare variables
        self.healthcare_capacity = 300 #capacity of the healthcare system
        self.treatment_factor = 0.5 #when in treatment, affect risk by this factor
        self.no_treatment_factor = 3 #risk increase factor to use if healthcare system is full
        #risk parameters
        self.treatment_dependent_risk = True #whether risk is affected by treatment

        #self isolation variables
        self.self_isolate_proportion = 0.6
        self.isolation_bounds = [0.02, 0.02, 0.1, 0.98]

        # googlemaps api key
        self.api_key = 'AIzaSyDCghpNB7UZ3qMpNJFUmSI9JoDL52eZS3U'

        #lockdown variables
        self.lockdown_percentage = 0.1
        self.lockdown_vector = []

        # visit supermarket settings
        # set to true to allow shoppers to return home
        self.return_from_shops = False

        # go home settings
        self.go_home_proportion = 0.9

        # list of locations supply a list of locations defined as strings
        self.locations = ['supermarket']


        # Dictionary of numpy arrays showing different sets of destinations. i.e. 1 = home, 2 = supermarket, 3 = park
        # Key relates to destination assignement and values relate to a pop_size x 3 numpy array showing latitude and longitude for all agents
        self.location_dict = {}

        # Dictionary of numpy arrays showing different sets of routes going from home to different locations as defined by find_nearest() function
        # Key relates to destination assignement and values relate to a pop_size x 5 numpy array showing col 0: start x, col 1: start y, col 2: dest x, col 3: dest y, col 4: route
        self.route_dict = {}

        # initialize population home_locations matrices
        self.population_init()





    def population_init(self):
        '''(re-)initializes population'''
        self.population = initialize_population(self.speed, self.pop_size, self.mean_age,
                                                self.max_age, self.xbounds,
                                                self.ybounds)
        self.pop_size = len(self.population)

        # set initial setting as home destination settings
        self.home_locations = self.population.copy() # may be able to get rid of this variable eventually
        # add home locations to self.location_dict
        self.location_dict['home'] = self.home_locations[:,1:3]




    def timeout_prob_dist(self, mean = 7, sd = 3):

        """ Model the timeout length based on each person visiting the location once every mean value nsteps
            Default set togGenerate a Gaussian of mean 7 and sd =3 to defined the timeout length in tsteps

        """
        # defines the number of days until next visit using a gaussian distribution mean= 7 and sd =3
        self.sm_timeout_length = np.random.normal(loc = 7, scale = 3)
        return self.sm_timeout_length




    def load_probability_distribution(self, max_pos_skew = -5, max_neg_skew = 5):
        """
        Generate probability distribution for visiting each location.
        At the moment this is set to generate a set of increasingly skewed probability distributions depending on how long since the agent visited the location
        """
        # Define list of distributions relating to the number of frames since last visited
        # so let's say we base it over 100 frames
        skewness_values  = np.linspace(max_neg_skew, max_pos_skew, 100)
        # generate 1000 random values for each skewness setting
        dist_sample_size = 1000

        # initialize the _sm_probabilities numpy array
        self._probabilities = np.zeros((dist_sample_size, len(skewness_values)))

        # Populate numpy array with probabilities changing the skewness of the prob distribution depending on how long it is since the agent last visited a specific destination
        for idx, skewness in enumerate(skewness_values):
            # generate _sm_probabilities distributions for each time frame
            self._probabilities[:,idx] = skewnorm.rvs(a = skewness,loc=100, size=dist_sample_size)

            # shift values so that lowest value is 0
            self._probabilities[:,idx] = self._sm_probabilities[:,idx] - np.min(self._sm_probabilities[:,idx])

            # standardise all values between 0 and 1
            self._probabilities[:,idx] = self._sm_probabilities[:,idx] / np.max(self._sm_probabilities[:,idx])
        return self._probabilities


    # def find_supermarkets(self, home_locations, pop_size):

    #     """
    #     identify supermarket location for each agent based on the nearest suopermarket to their home.
    #     At the moment they all go to the same supermarket but will need to build this out using Google maps nearest utility
    #     """
    #     sm_list = ['Asda', 'Waitrose', 'Sainsbury', 'Lidl', 'Aldi', 'Tesco', 'Co-op', 'Morrisons', 'Marks and Spencer']
    #     for home_location in home_locations:
    #         # Retrive top 20 list of nearest supermarkets
    #         dict_top20_nearest = self.find_nearest(home_location)
    #         # Find the well known supermarket as opposed to the independent shop which may not contain suptable quantity of stock for a weekly food shop
    #         # Iterate over the list of super market dictionaries
    #         for sm in dict_top20_nearest['results']:
    #             # stops at first value that is true as opposed to iterating over whole list
    #             for brand_sm in sm_list:
    #                 if any(brand_sm in sm['name']):
    #                     # store supermarket location in cache database
    #                     sm['geometry']['location']['lat']
    #                     sm['geometry']['location']['lng']




        self.gmaps = googlemaps.Client(key=self.api_key)
        # geocode_result = self.gmaps.geocode('Waitrose & Partners Barnet, 111 High St, Barnet EN5 5XY')
        # self.sm_long = geocode_result[0]['geometry']['location']['lng']
        # self.sm_lat = geocode_result[0]['geometry']['location']['lat']
        self.sm_locations = np.zeros((pop_size,4))
        self.sm_long = -0.2039372
        self.sm_lat = 51.65572030000001
        self.sm_locations[:,0] = self.sm_long
        self.sm_locations[:,1] = self.sm_lat
        # self.location_matrix[:,3] = 2
        # self.location_matrix[:,4] = self.sm_long
        # self.location_matrix[:,5] = self.sm_lat


    def set_bounds(self, polygon_file = './postcode_shape_files/barnet_polygons.csv'):
        '''
        load polygon file which relates to boundary for map
        '''
        # read in csv file as pandas dataframe
        polygon_df = pd.read_csv(polygon_file, delimiter = ',')
        polygon_df['geometry'] = polygon_df['geometry'].apply(wkt.loads)
        # Convert to geodataframe and plot on axis
        poly_gdf = gpd.GeoDataFrame(polygon_df, geometry=polygon_df.geometry)

        # return xmin, ymin, xmax, ymax boundary values
        return poly_gdf.total_bounds





    def get_palette(self):
        '''returns appropriate color palette

        Uses config.plot_style to determine which palette to pick,
        and changes palette to colorblind mode (config.colorblind_mode)
        and colorblind type (config.colorblind_type) if required.

        Palette colors are based on
        https://venngage.com/blog/color-blind-friendly-palette/
        '''

        #palette colors are: [healthy, infected, immune, dead]
        palettes = {'regular': {'default': ['gray', 'red', 'green', 'black'],
                                'dark': ['#404040', '#ff0000', '#00ff00', '#000000']},
                    'deuteranopia': {'default': ['gray', '#a50f15', '#08519c', 'black'],
                                     'dark': ['#404040', '#fcae91', '#6baed6', '#000000']},
                    'protanopia': {'default': ['gray', '#a50f15', '08519c', 'black'],
                                   'dark': ['#404040', '#fcae91', '#6baed6', '#000000']},
                    'tritanopia': {'default': ['gray', '#a50f15', '08519c', 'black'],
                                   'dark': ['#404040', '#fcae91', '#6baed6', '#000000']}
                    }

        if self.colorblind_mode:
            return palettes[self.colorblind_type.lower()][self.plot_style]
        else:
            return palettes['regular'][self.plot_style]

    def get(self, key):
        '''gets key value from config'''
        try:
            return self.__dict__[key]
        except:
            raise config_error('key %s not present in config' %key)


    def set(self, key, value):
        '''sets key value in config'''
        self.__dict__[key] = value


    def read_from_file(self, path):
        '''reads config from filename'''
        #TODO: implement
        pass


    def set_lockdown(self, lockdown_percentage=0.1, lockdown_compliance=0.9):
        '''sets lockdown to active'''

        self.lockdown = True

        #fraction of the population that will obey the lockdown
        self.lockdown_percentage = lockdown_percentage
        self.lockdown_vector = np.zeros((self.pop_size,))
        #lockdown vector is 1 for those not complying
        self.lockdown_vector[np.random.uniform(size=(self.pop_size,)) >= lockdown_compliance] = 1

    def set_visit_supermarket(self, offline_shopping_proportion=0.8,
                                supermarket_bounds = [-0.2037, 51.6555, -0.2039, 51.6557],
                                traveling_infects=True):
        '''sets supermarket visit scenario to active'''
        self.visit_supermarket = True
        self.supermarket_bounds = supermarket_bounds
        self.offline_shopping_proportion = offline_shopping_proportion
        #set roaming bounds to outside isolated area
        # self.xbounds = [-0.2049, -0.2029]
        # self.ybounds = [51.6547, 51.6567]
        #update plot bounds everything is shown
        # self.x_plot = [-0.2049, -0.2029]
        # self.y_plot = [51.6547, 51.6567]
        #update whether traveling agents also infect
        self.traveling_infects = traveling_infects

    def set_go_home(self, go_home = True, go_home_proportion = 0.9):
        ''' sets go_home function to active'''
        self.go_home = go_home
        self.go_home_proportion = go_home_proportion



    def set_self_isolation(self, self_isolate_proportion=0.9,
                           isolation_bounds = [0.02, 0.02, 0.09, 0.98],
                           traveling_infects=False):
        '''sets self-isolation scenario to active'''

        self.self_isolate = True
        self.isolation_bounds = isolation_bounds
        self.self_isolate_proportion = self_isolate_proportion
        #set roaming bounds to outside isolated area
        self.xbounds = [0.1, 1.1]
        self.ybounds = [0.02, 0.98]
        #update plot bounds everything is shown
        self.x_plot = [0, 1.1]
        self.y_plot = [0, 1]
        #update whether traveling agents also infect
        self.traveling_infects = traveling_infects


    def set_reduced_interaction(self, speed = 0.001):
        '''sets reduced interaction scenario to active'''

        self.speed = speed


