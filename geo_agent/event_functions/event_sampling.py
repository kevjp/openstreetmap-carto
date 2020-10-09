import numpy as np
from random import choice, randint
from scipy.stats import skewnorm
from event_functions.event_init import Eventinit # custom file containing custom probability initialisation functions
import math

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

        self.sample_prob = choice(self._probabilities[days_overdue,:])

        # determine if event occurs
        if self.sample_prob > threshold:
            self.status = True
        else:
            self.status = False






    def determine_starttime(self):
        """
        Sample from starttime distribution defined by init_event_starttime
        """
        # sample from time distribution self._starttime
        self.starttime = choice(self._starttime)


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
