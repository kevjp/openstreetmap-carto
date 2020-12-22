from random import choice, randint
import numpy as np
from scipy.stats import skewnorm
from datetime import datetime, date, time, timedelta
from event_functions.event_sampling import Eventsampling # custom class containing custom probability initialisation and sampling functions
import copy
from event_functions.event_init import Eventinit
import re




class Event(Eventinit,Eventsampling):

    def __init__(self, travel_speed = 10, *args, **kwargs):

        """
        time_before_event_repeat : positive integers indicate number of days before event repeats and negative integers indicate the number of days overdue

        """

        self.description = kwargs.get('description')
        self.description_idx = kwargs.get('index')
        self.starttime = kwargs.get('starttime')
        self.time_at_event = kwargs.get('time_at_event')
        self.time_since_last_event = kwargs.get('time_since_last_event')
        self.time_before_event_repeat = kwargs.get('time_before_event_repeat')
        self.travel_speed = travel_speed
        self.status = False
        self.event_status = 0 # 0 = inactive, 1 = active
        self.event_OSM_search_term = ''
        self.lat = ''
        self.lon = ''
        self.utmx = ''
        self.utmy = ''
        self.osm_way_id = ''
        self.source_node_osm_way_id = ''
        self.target_node_osm_way_id = ''
        self.random_movement = False
        self.current_infections = {}
        self.attached_agent = None
        self.clock_instance = None
        self.return_home = 1 # default all events return home
        self.event_initialised = 0 # 0 indicates that the event has been initialised with values defined by the functions defined in the probability_sampling_functions dictionary within the config file




    def __deepcopy__(self, memo):
        """
        magic method to create a custom deepcopy method can make a copy of specific variables specified in this function
        This deepcopy method will not deepcopy any variables from the Eventinit class
        These variables will be instantiated and will be held in a different space
        in memory if relating to a different Event type eg go_to_the_park vs weekly_shop.
        However the variables will relate to the same space in memory for the same Events
        which are deep copied between agents. This avoid mass duplication of large probability
        distribution data in memory
        """
        # retrive all variables from Eventinit. These variables relate to sample
        # distributions and remain static so do not need to be copied for each agent instance
        event_init_vars = dir(Eventinit())
        regex = re.compile(r'^__.*__$')
        exempt_from_deepcopy = [v for v in event_init_vars if regex.match(v) is None]
        # print(f'exempt_from_deepcopy{exempt_from_deepcopy}')
        # make a copy of the class object
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result

        for k, v in self.__dict__.items():

            if k not in exempt_from_deepcopy:
                setattr(result, k, copy.deepcopy(v, memo))
            else:
                setattr(result, k, v)
        return result


    def determine_value(self, distribution):
        """
        Samples from a given distribution randomly
        """
        sample_val = choice(distribution)

        return sample_val









def add_method(cls):
        """
        use this decorator to add bespoke functions designed by the user to initilise
        and sample frpm their own probability distributions. These functions can be
        designated in event config json

        EXAMPLE:
        from event import Event

        @add_method(Event)
        def foo():
            print('hello world')



        """
        def decorator(func):
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                return func(*args, **kwargs)
            setattr(cls, func.__name_, wrapper)
            # Note we are not binding func, but wrapper which accepts self but does exactly the same as func
            return func # returning func means func can still be used normally
        return decorator


