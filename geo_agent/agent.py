
from event import Event
from json_logic import jsonLogic
import copy

class Agent():

    """

    Each agent from Load_populations.sub_population np.array is loaded into an 'Agent' class with the following attributes

    id : int (unique value)
    subpop_id : int
    osm_ways_ref : int
    current_state : int (0=healthy, 1 = sick, 2 = imune, 3 = dead, 4 = immune but infectious)
    age : int
    infected_since : int (frame the agent got infected)
    recovery_vector : vector (used to determine if someone recovers or dies)
    in_treatment : int (0= No, 1= Yes)
    current_events : dictionary of current class event instances
    travelling : 0 = No, 1 = Yes (indicates if agent is currently taking part in an event or series of events)
    event_description_string : dictionary [event.description] = 0 (Unavailable) , 1 (Available)

    self.current_lat : current lat location of agent
    self.current_lon : current lon location of agent
    self.tracker_instance : points to corresponding tracker instance for the agent instance
    """

    def __init__(self, row, id):

        self.headers = ['id', 'subpop_id', 'osm_ways_id', 'lat', 'lon', 'age', 'current_state', 'infected_since', 'recovery_vector', 'in_treatment', 'current_events', 'travelling', 'event_description_string']
        self.__dict__ = dict(zip(self.headers, row))
        self.the_id = id
        self.current_events = {}
        self.event_description_string = {}
        self.current_lat = row[3] # lat column
        self.current_lon = row[4] # lon column
        self.tracker_instance = None


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
            event_eligibility_obj = event_config_obj[key].agent_eligibility
            event_trigger_obj = event_config_obj[key].trigger
            event_instance = event_config_obj[key]

            if jsonLogic(event_eligibility_obj, self.__dict__) and jsonLogic(event_trigger_obj, self.__dict__):
                # deepcopy instance to agent instance if agent is eligible or event has been triggered
                self.current_events[key] = copy.deepcopy(event_instance)


    def update_time_b4_event_repeat(self):
        """
        updates event instance variable time_before_event_repeat
        """
        pass

    def next_update(self, event_json_obj):
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
                    func(*args, **kwargs)



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



