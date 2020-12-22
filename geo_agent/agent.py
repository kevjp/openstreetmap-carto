
from event import Event
from json_logic import jsonLogic
import copy
import numpy as np

class Agent():

    """

    Each agent from Load_populations.sub_population np.array is loaded into an 'Agent' class with the following attributes

    id : int (unique value)
    subpop_id : int
    osm_ways_ref : int
    current_state : int (0=healthy, 1 = infected, 2 = recovered, 3 = dead)
    age : int
    recovery_vector : vector (used to determine if someone recovers or dies)
    in_treatment : int (0= No, 1= Yes)
    current_events : dictionary of current class event instances
    travelling : 0 = No, 1 = Yes (indicates if agent is currently taking part in an event or series of events)
    event_description_string : dictionary [event.description] = 0 (Unavailable) , 1 (Available)

    self.current_lat : current lat location of agent
    self.current_lon : current lon location of agent
    self.tracker_instance : points to corresponding tracker instance for the agent instance
    """

    def __init__(self, row, id, *args, **kwargs):

        headers = ['id', 'subpop_id', 'start_source_node_osm_way_id', 'start_target_node_osm_way_id', 'start_lat', 'start_lon', 'utm_x', 'utm_y', 'age', 'current_state', 'recovery_vector']
        # assign header values as class attributes with corresponding values from row input
        for k, v in zip(headers, row):
            setattr(self, k, v)
        self.the_id = id
        self.current_events = {}
        self.event_description_string = {}
        self.current_lat = row[3] # lat column
        self.current_lon = row[4] # lon column
        # initialise all agents disease_progression_state to None and at each tstep update state depending on current disease progression as defined by Infection().disease_timer function
        # available values are None, -2 to indicate that the disease progression object needs to be defined, -1 to indicate that the disease progression object has been defined and  string values "asymptomatic", "mild", "hospitalised", "ventilated", "dead"
        # In Load_populations.sub_population[:,9] referes to disease state 0 = None, 1=aymptimatic, 2= mild, 3= hospitalised, 4= ventilated, 5= recovered, 6= dead
        self.disease_progression_state = None
        self.tracker_instance = None
        self.event_history_dict = {}
        self.current_infections = {}




    def __repr__(self):
         return self.the_id

    def activate_events(self):

        """
        Itterates over the list of events in agent.events and determines if event occurs.
        If event occurs then corresponding event instance is instantiated.
        """
        pass



    def retrieve_relevant_events(self, event_config_obj):

        """
        Based on the agent_eligibility and trigger conditions defined in the event config file
        this function filters out events for which each agent instance is not
        eligible to perform

        event_config_obj : dictionary of event instances

        agent_event_instances_dict : dict of a dict of event instances
        agent_eligibility_dict : dict of json objects of condition information indicating each agents eligibility to carry out the corresponding event
        """
        # Retrieve boolean vector indicating elegibility of event for each agent
        for key, event in event_config_obj.items():
            # extract event_eligibility_obj and event_instance for each event
            agent_eligibility_obj = event_config_obj[key].agent_eligibility
            event_eligibility_obj = event_config_obj[key].event_eligibility
            trigger_obj = event_config_obj[key].trigger
            event_instance = event_config_obj[key]

            print("self.current_state", self.current_state)
            # Instantiated event instance __dict__ in self.event_history_dict if not done so already
            if event_config_obj[key].description not in self.event_history_dict:
                self.event_history_dict[event_config_obj[key].description] = event_config_obj[key].__dict__

            # print("jsonLogic(agent_eligibility_obj, self.__dict__)", jsonLogic(agent_eligibility_obj, self.__dict__))
            # print(self.__dict__["age"])
            # print(self.__dict__["current_state"])
            # print(self.__dict__["event_history_dict"]["weekly_shop"]["time_before_event_repeat"])
            # print("jsonLogic(trigger_obj, self.__dict__)", jsonLogic(trigger_obj, self.__dict__))

            if jsonLogic(agent_eligibility_obj, self.__dict__) and jsonLogic(trigger_obj, self.__dict__):
                print("attaching event", key)
                # deepcopy instance to agent instance if agent is eligible or event has been triggered
                event_instance.attached_agent = self
                self.current_events[key] = copy.deepcopy(event_instance)


    def track_event_history_dict(self):
        """
        Counts down time_before_event_repeat timer for each event
        """

        for key, event in self.current_events.items():
            self.current_events[key].time_before_event_repeat = self.current_events[key].time_before_event_repeat - 1



    def attach_infection_obj(self, infection_config_obj):
        """
        Attach infection instance object to any newly infected agents
        infection_config_obj : dict object
        # see initialise_infection() in main.py for the structure of infection_config_obj
        """

        for key, infection in infection_config_obj.items():
            # extract infection eligibility
            infection_eligibility_obj = infection_config_obj[key].agent_eligibility
            infection_instance = infection_config_obj[key]


            # attach infection instance only to infected agents and agents where disease progression has not been defined
            if jsonLogic(infection_eligibility_obj, self.__dict__):
                # deepcopy instance to agent instance if agent is eligible (i.e. has been infected)
                self.current_infections[key] = copy.deepcopy(infection_instance)
                # set disease progression state to -2 meaning disease progression dictionary needs to be defined
                self.disease_progression_state = -2
                print("infection class obj has been attached")


    def infection_update(self,infection_json_obj):
        """
        update the infection instance attached to each agent
        """
        for infection in infection_json_obj["infection_criteria"]:
            # check if agent is infected only agents which are infected will have an infection class instance listed in self.current_infections
            if infection["description"] in self.current_infections and self.disease_progression_state == -2:
                # define disease progress for agent
                # reset args and kwargs variables
                args, kwargs = [], {}
                # retrieve disease_progression function
                func = infection["disease_progression"]["function"]   # retrieve function name
                # retrieve args for disease_progression function
                args = infection["timer_objects"]

                # Retrieve function from class instance
                func = getattr(self.current_infections[infection["description"]], func)
                # Run disease progression function
                func(*args, **kwargs)

                # Set disease progression to 1 to indicate that disease progreassion has been defined
                self.disease_progression_state = -1

            if self.disease_progression_state == -1:
                # define initial disease state
                self.disease_progression_state = infection["timer_objects"][0]["state"]
                # First time disease_progression_obj is processed by track_disease_progression
                self.track_disease_progression(self.current_infections[infection["description"]].disease_progression_obj)
            else:
                self.track_disease_progression(self.current_infections[infection["description"]].disease_progression_obj)


    def track_disease_progression(self, disease_progression_obj):

        """
        Tracks disease progression by:
            - counting down the time in each state
            - changing the disease_progression_state of the agent
            - execute action function

        """

        # Check if time at disease state has ended
        if disease_progression_obj[self.disease_progression_state]["days"] == np.timedelta64(0,'m'):
            # change label according to label_change.
            # Event functions will be initiated as part of the normal event attachment process
            self.disease_progression_state = disease_progression_obj[self.disease_progression_state]["label_change"]

        else:
            # reduce time at current infection state by 1 tstep
            disease_progression_obj[self.disease_progression_state]["days"] = disease_progression_obj[self.disease_progression_state]["days"] - np.timedelta64(1,'m')






    def update_time_b4_event_repeat(self):
        """
        updates event instance variable time_before_event_repeat
        """
        pass

    def next_event_update(self, event_json_obj):
        """
        update all event instances attached to agent with event details for next set of events
        """
        for event in event_json_obj["events"]:
            # check if agent is eligible to perform event

            if event["description"] in self.current_events:
                # Ignore events which are not due to occur
                # if self.current_events[event["description"]].time_before_event_repeat >= 0:
                #     self.update_time_b4_event_repeat() # placeholder function for updating this variable
                #     continue
                # sample from initialised distributions
                # update current event instances with infection dictionary if agent has become infected
                if self.current_infections:
                    self.current_events[event["description"]].current_infections = self.current_infections

                # Only sample probability functions once on input into the tracker
                if event["probability_sampling_functions"] is not None and self.current_events[event["description"]].event_initialised == 0:
                    for key in event["probability_sampling_functions"]:
                        # reset args and kwargs variables
                        args, kwargs = [], {}
                        # iterate over all intitialisation functions and call each to initialise all sampling distribution
                        func = event["probability_sampling_functions"][key]["function"]   # retrieve function name
                        if "args" in event["probability_sampling_functions"][key]:
                            args = event["probability_sampling_functions"][key]["args"]  # retrieve arguments for function
                        if "kwargs" in event["probability_sampling_functions"][key]:
                            kwargs = event["probability_sampling_functions"][key]["kwargs"] # retrieve key word arguments for function

                        func = getattr(self.current_events[event["description"]], func)
                        check = func(*args, **kwargs)
                        print("checking returned time_before_event_repeat value", check)
                        self.current_events[event["description"]].event_initialised = 1

                # Populate all variables which point to agent instance variables
                for k, item in event.items():
                    # check item in event config json refers to a dictionary object
                    if isinstance(item,dict):
                        # Check if dictionary contains the key "variables"
                        if "variables" in item:
                            # retrieve variable values and assign to relevant event instance atribute
                            setattr(self.current_events[event["description"]], k, self.populate_event_instance_variables(item["variables"]))

        # Remove events with inactive status
        self.remove_events_with_inactive_status()


    def populate_event_instance_variables(self, event_config_dict):

        attr_list = event_config_dict["variables"]
        value_list = [self.assign_attribute(attr) for attr in  attr_list]
        return value_list




    def assign_attribute(self, attr):

        # Retrieve variable value from self
        return getattr(self, attr)




    def remove_events_with_inactive_status (self):

        for key in list(self.current_events.keys()):
            if self.current_events[key].status is False:
                del(self.current_events[key])






    def append_event(self, *args, **kwargs):
        """
        attach event instance to agent
        """
        self.description = kwargs.get('description')
        self.starttime = kwargs.get('starttime')
        self.time_at_event = kwargs.get('time_at_event')
        self.time_since_last_event = kwargs.get('time_since_last_event')
        self.time_before_event_repeat = kwargs.get('time_before_event_repeat')
        self.event_instance = Event()
        self.current_events.append(self.event_instance)
        self.event_availability[event_instance.description] = 1



