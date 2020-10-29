import numpy as np
from scipy.stats import skewnorm, truncnorm
from random import choice, randint
import random
from json_logic import jsonLogic
import libpysal.weights as weights
from infection_functions.infect_init import Infectioninit


class Infection(Infectioninit):

    """
    Infection object defines the nature of the infection and is attached to the agent on infection
    """
    def __init__(self, *args, **kwargs):

        self.infection_radius = kwargs.get("infection_radius")
        self.isolation_adherence = kwargs.get("isolation_adherence")
        self.infection_status = "healthy"
        self.disease_progression_obj = {} # populate with specifics of how disease progresses for each agent
        self.infection_days = self.gauss_distribution_generator(start = 0, stop = 14, mean = 5, sd = 2, size = 1000, conversion_factor = 1440, tstep_units = 'm')





    def infect(self,p=Infectioninit().time_dependent_prob(), current_points=None, infectious_indices=None, infection_distance =2):
        """
        Sample Distance x Time since infected distribution of how infectious the infected agent is
        p : probability of contracting COVID over infectious period default set to 0.5 constant over entire infectious period may want to assign probability distribution here. Can define in Infectioninit class found in infect_init.py script
        current_points : list of tuples of points in UTM projection for all agents
        list of indices relating to the agents that are infectious
        Returns a list of indices relating the agents that have been newly infected
        """
        # Calculate distance weights for each healthy agent based on their proximity to infected agents. Only consider agents within 2m of each other
        # agents which are touching the weight value is 1 and the weight value is the recipricol of the distance in meters from the infected agent
        distance_weights = weights.distance.DistanceBand(current_points, threshold= infection_distance,binary=False)

        newly_infected_indices = []
        # Filter out weights not relating to agents which are not infectious and scale distance_weights by time-dependent infection probability p
        for index, (key,weight) in enumerate(distance_weights.neighbors.items()):
            relevant_bool_ind = np.in1d(weight,infectious_indices)
            relevant_weights = np.array(distance_weights.weights[key])[relevant_bool_ind]
            # scale weights by time-dependent infection probability p
            scaled_relevant_weights = relevant_weights * p
            # calculating probability of getting infected
            prob_of_not_infecting = np.prod(1 - scaled_relevant_weights)
            prob_of_infecting = 1 - prob_of_not_infecting
            # sample probability
            sample_prob = random.random()
            if sample_prob <= prob_of_infecting:
                # add index of newly infected agent
                newly_infected_indices.append(index)
        return newly_infected_indices





    def gauss_distribution_generator(self, start = None, stop = None, mean = None, sd = None, size = None, conversion_factor = None, tstep_units = 'm'):
        """
        Generate Gaussian distribution of values from which to sample from. Use Conversion factor to convert values in tstep units
        eg. if each tstep represents 1 min of time then to convert values to days for example mean multiplying by a facot of 1440 (60 *24).
        tstep_units can be 's' (seconds), 'm' (minutes), 'h' (hours)
        """
        value_list = []
        values = truncnorm.rvs(start - (mean/sd), stop - (mean/sd),loc=mean, size=size, scale=sd)
        # Convert values over to timedelta values
        for i, v in enumerate(values):
            v = int(round(v)) # numpy timedelta only accepts whole int values
            v_converted = v * conversion_factor

            value_list.append(np.timedelta64(v_converted, tstep_units))
        value_arr = np.array(value_list)

        return value_arr



    def disease_progression_func(self, *args, **kwargs):
        """
        Based on the defined disease attributes define a disease progression object for the infected agent
        disease_progress_obj : dict of dict
        {asymptomatic : {days : , action : None or call to function eg None, label_change : eg. mild},
         mild : {days : , action : None or call to function eg event go_hospital, label_change : eg. hospitalised},
         hospitalised : {days : , action : None or call to function eg event go_icu, label_change : eg. ventilated},
         ventilated : {days : , action : None or call to function eg event go_home, label_change : eg. recovered}}

        """
        # Retrieve infection states from config file
        timer_objects = args

        for state_obj in timer_objects:
            # Initial disease state
            self.disease_progression_obj[state_obj["state"]] : {}
            # calculate number of days at this disease state (distributions for days in each state are intialised by initialise_infection in main.py)
            # Each distribution is accessible from infection class instance via self.<state>.days_in_state where for COVID <state> is defined by value in timer_objects list realting to state keyword
            infection_class_att = state_obj["state"] + "_days_in_state"
            days_distribution = getattr(self, infection_class_att)

            self.disease_progression_obj[state_obj["state"]] = {"days" : choice(days_distribution)}


            # Determine if disease pregresses to worst state
            # Sample Randomly probability value
            sample_prob = random.random()
            # return true according to probability threshold defined in config file
            if jsonLogic(state_obj["probability_worstens"], {"p" : sample_prob}):
                self.disease_progression_obj[state_obj["state"]]["label_change"] = state_obj['label_change']
                self.disease_progression_obj[state_obj["state"]]["action_function"] = state_obj['action_function']
            else:
                self.disease_progression_obj[state_obj["state"]]["label_change"] = "recovered"
                self.disease_progression_obj[state_obj["state"]]["action_function"] = "go_home"
                break


    def disease_timer(self, agent_disease_progression_state):
        """
        Take the self.disease_progression_obj as input and reduces current disease state days by 1 tstep
        Take also agent.agent_disease_progression_state to identify current disease progression state for agent
        If disease state changes then re-assign agent labels to new state and execute appropriate functions (for now this utility is not implemented the agent will eventually returnhome after the current set of events and will not carry oput any further events until infection passed)
        """
        # Access current disease state from agent disease progression object
        self.disease_progression_obj[agent_disease_progression_state]["days"] -= 1
        if self.disease_progression_obj[agent_disease_progression_state]["days"] == 0:
            new_state = self.disease_progression_obj[agent_disease_progression_state]["label_change"]
        return new_state


    def sample_gaus_dist(self, distribution_values):

        """
        sample from gaussian distributions generated by gauss_distribution_generator function
        """
        sample_value = choice(distribution_values)
        return sample_value




    def does_it_occur(self, threshold=None, **kwargs):

        """
        Determine if infection occurs based on probability threshold defined in config.json file
        """
        sample_prob = random.random()


        # determine if infection state occurs
        if sample_prob > threshold:
            return True
        else:
            return False

