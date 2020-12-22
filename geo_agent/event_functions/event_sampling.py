import numpy as np
from random import choice, randint
from scipy.stats import skewnorm
from event_functions.event_init import Eventinit # custom file containing custom probability initialisation functions
import math
import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
print(path.dirname( path.dirname( path.abspath(__file__) ) ))
from clock import Clock
# from geo_agent.clock.Clock import convert_numpy_datetime64_to_mins


class Eventsampling():

    """
    Class to hold all sampling functions for all events specify names and corresponding event instances
    in event config json

    """




    def determine_event_occurs(self, tsteps_overdue, **kwargs):

        """
        Sample from probability distribution defined in self._probabilities as defined by init_event_occurring()
        """
        threshold = kwargs.get("threshold")
        # convert tsteps to days
        days_overdue = math.floor(tsteps_overdue / 1440)
        print("tsteps_overdue",tsteps_overdue)
        self.sample_prob = choice(self._probabilities[days_overdue,:])
        # determine if event occurs
        if self.sample_prob > threshold:
            self.status = True
            print("EVENT IS HAPPENING")
        else:
            self.status = False
            print("NOOOOOO!!!!!!!!!!!! EVENT IS NOT HAPPENING")



    def determine_starttime(self):
        """
        Sample from starttime distribution defined by init_event_starttime and convert to minute representation of time
        """
        # sample from time distribution self._starttime
        starttime = choice(self._starttime)
        print("starttime", starttime)
        # Convert to minute representation of the time
        self.starttime = Clock().convert_numpy_datetime64_to_mins(np_datetime64 = starttime)
        print("self.starttime", self.starttime)


    def determine_time_at_event(self):

        # sample from time period distribution self._minutes
        self.time_at_event = choice(self._minutes)
        return self.time_at_event



    def determine_time_before_event_repeat(self):
        """

        """

        # sample from time period distribution self._minutes
        self.time_before_event_repeat = (choice(self._days)).astype("float")
        return self.time_before_event_repeat


    def determine_time_at_event_hospitalised(self, *args, **kwargs):



        disease_description = kwargs.get("disease_description")

        # retrieve infection instance which contains disease_progression_obj
        infection_instance = self.current_infections[disease_description]
        states = kwargs.get("states")
        print(infection_instance.disease_progression_obj)
        # add up the collective time at hospital
        time_at_event = 0
        for state in states:
            if state in infection_instance.disease_progression_obj:
                print("self.attached_agent.current_infections[disease_description].disease_progression_obj", self.attached_agent.current_infections[disease_description].disease_progression_obj)
                time_at_event += self.attached_agent.current_infections[disease_description].disease_progression_obj[state]["days"]
        self.time_at_event = time_at_event
