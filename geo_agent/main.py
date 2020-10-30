

from subpopulations import Load_populations
from agent import Agent
from event import Event, add_method
from infection import Infection
import json
import copy
from tracker import Tracker
import time
import os
from clock import Clock
from visualiser_geo import build_fig_geo, set_style, draw_tstep, parse_agent_location, parse_yaml_result
import time
import numpy as np




class Simulation():

    def read_in_event_config(self, json_file = "./config/example_config_with_infection.json"):
        # open json config file
        f = open(json_file)
        self.event_json = json.load(f)

    def inititialise_events(self, json_obj):

        """Read in events config json defining event description and probability
        inititialisation and sampling functions. Can define these functions bespoke
        to the event and can load as a bespoke event class instance.

        json_file : file path to json config file for simulation events

        returns
        dictionary for each event attribute which can be recalled by event[event_attribute]
        These dictionaries are held in event_confidictionary objects extracted from the json
        Event objects can be retrieved from event_config_obj by using the corresponding event.description as the key
        eg. event_config_obj["weekly_shop"]. The corresponding value is the class instance for the weekly_shop event containing required and user-defined fields
        eg.
        Dictionary names relate to json_attributename_dict. Returned dictionaries include:
        event.description
        event.starttime
        event.time_at_event_dict
        event.time_since_last_event_dict
        event.time_before_event_repeat_dict
        event.travel_speed_dict
        event.probability_initialisation_functions_dict
        event.probability_sampling_functions_dict
        event.agent_eligibility_dict
        event.trigger_dict

        event.status = 0 available or 1 unavailable
        """

        self.event_config_obj = {} # overarching dictionary that holds all extracted objects from json file
        # Initialise dictionaries of event json objects
        event_index = 1 # index value for each  event class starting from 1 (0 value indicates go home)
        for event in self.event_json["events"]:
            # initialise event status equal to 0 i.e. available
            event["status"] = 0
            # instantiate Event class
            event["class_instance"] = Event()
            # generate unique numerical index value for each event class
            event["index"] = event_index
            event_index += 1
            # update event class with variables from config
            vars(event["class_instance"]).update(event)
            # print(event["class_instance"].__dict__)

            # generate distrib of probabilities for event occuring accroding to list of functions specified in config json
            for key in event["probability_initialisation_functions"]:
                # reset args and kwargs variables
                args, kwargs = [], {}
                # iterate over all intitialisation functions and call each to initialise all sampling distributions
                func = event["probability_initialisation_functions"][key]["function"]   # retrieve function name
                if "args" in event["probability_initialisation_functions"][key]:
                    args = event["probability_initialisation_functions"][key]["args"]  # retrieve arguments for function
                if "kwargs" in event["probability_initialisation_functions"][key]:
                    kwargs = event["probability_initialisation_functions"][key]["kwargs"] # retrieve key word arguments for function

                func = getattr(event["class_instance"], func)
                func(*args, **kwargs)

            # update event_config_obj dictionary with Event class instance
            self.event_config_obj[event["class_instance"].description] = event["class_instance"]

    def initialise_infection(self):

        """
        Initialise infection instance which can be attached to each agent
        """
        self.infection_obj = {} # holds infection class instance
        infection_index = 0
        for infection in self.event_json["infection_criteria"]:
            # initialise infection status equal to healthy
            infection["status"] = "healthy"
            # instantiate Infection class
            infection["class_instance"] = Infection()
            # generate unique numerical index value for each event class
            infection["index"] = infection_index
            infection_index += 1

            # generate distributions for the number of days in each infection state for each disease as defined in config infection_criteria dictionary
            # Need to iterate over time_objects list
            # Initialises all distributions for days in each state (infection.<state>_days_in_state where for COVID <state> equals either aymptomatic, mild, hospitalised, ventilated or death)
            for state in infection["timer_objects"]:
                if "days_in_state" in state.keys():
                    func = getattr(infection["class_instance"], state["days_in_state"]["function"])
                    kwargs = state["days_in_state"]["kwargs"]
                    infection_class_att = state["state"] + "_days_in_state"
                    infection[infection_class_att] = func(**kwargs)
            # update infection class with variables from config
            vars(infection["class_instance"]).update(infection)

            # update infection_obj dictionary with Infection class instance
            self.infection_obj[infection["class_instance"].description] = infection["class_instance"]








    def load_events_into_tracker(self, agent_current_events):
        """
        Loads list of available event instances for each agent into Tracker class and
        Tracker class looks for events that are overlapping in time (or by a specific threshold)
        and links these events together. So if event "weekly_shop" and "walk_in_park"
        overlap then the tracker will trace a journey for the agent from home to shops
        and then from the shops to the park. Locations will be based on nearest amenity
        to agent's current location.

        agent_current_events : Agent.current_events dictionary

        """



    def initialise_simulation(self, household_data = './data/barnet_points_19.csv', \
        config_file = './config/example_config_with_infection.json'):

        """
        Function to initialise the simulation. This will involve loading config files
        and instantiating Agent, Event, Tracker and Clock instances.

        Event class will need to be instantiated

        """
        # load agent data into a numpy array
        self.pop_config = Load_populations(household_data = household_data)

        # instantiate agent instances based on numpy array
        self.agents = [Agent(self.pop_config.sub_population[i,:], "agent_{}".format(i+1)) for i in range(self.pop_config.pop_size)]

        # instantiate infection instances will set up self.infection_obj which contains infection class instance which can be intantiated for each agent
        self.initialise_infection()

        # returns self.event_config_obj dictionary which is a dictionary of each event instance
        self.inititialise_events(config_file)
        # initialise the plot obect to visualise agent movement on map
        self.fig, self.spec, self.ax1, self.ax2, self.shapefile_df = build_fig_geo(self.pop_config)



    def tstep(self):
        """
        Function to advance agent based simulation by a single tstep
        """

        #### NEED TO PUT INTO SEPARATE FUNCTION SO THAT inititialise_events is only called once
        # add event instances to current_events attributes for each agent

        # Iterate over list of infection and infect agents
        if self.event_json["infection_criteria"]:
            for infection_dict in self.event_json["infection_criteria"]:
                infect_func_string = infection_dict["infect"]["function"]
                # Retrieve infection function from config file
                infection_func = getattr(Infection(), infect_func_string)
                # Call function with keyword arguments from config. Here we are calling the infect() function
                kwargs = infection_dict["infect"]["kwargs"]
                current_points  = list(zip(self.pop_config.sub_population[:,5], self.pop_config.sub_population[:,6]))

                infectious_indices = np.where(self.pop_config.sub_population[:,8] == 1)
                print("infectious_indices", infectious_indices)
                print(kwargs)
                newly_infected_indices = infection_func(current_points =  current_points, infectious_indices = infectious_indices, **kwargs)

                # Convert affected agents to infected
                self.pop_config.sub_population[newly_infected_indices,7] = 1
                # update point_plots_matrix which is used to visualise the agents. This update allows point to be labelled on the basis of their infection status
                self.pop_config.point_plots_matrix[:,1] = self.pop_config.sub_population[:,8]

        for agent in self.agents:
            # attach infection instance to infected agents. The infection instance determines the infection progression for each agent
            if self.event_json["infection_criteria"]:
                agent.attach_infection_obj(self.infection_obj)
                agent.infection_update(self.event_json)
            # Load events into Tracker class
            if agent.tracker_instance is None:
                print("1")
                # add events that agent is eligible for
                agent.retrieve_relevant_events(self.event_config_obj)
                print("2")
                # configure the event for the agent from the supplied json
                agent.next_update(self.event_json)
                print("3")
                # instantiate tracker instance for agent
                track_obj = Tracker(agent.current_events, agent.lat, agent.lon, self.pop_config, agent_instance = agent)
                print("4")
                # attach tracker instance to agent instance
                agent.tracker_instance = track_obj
                print("5")
                # Sort events according to starttime
                track_obj.sort_eventtimes()
                print("6")
                # obtain amenity locations for all attached events returns a list of waypoints starting and ending at home
                track_obj.generate_route_waypoints()

            # Take a tstep through the Tracker instance for each agent
            print("7")
            agent.tracker_instance.route_step()
            print("8")
        # Plot agents on map
        # draw_tstep(self.pop_config, self.fig, self.ax1, self.ax2, self.shapefile_df)
        parse_agent_location(self.pop_config)
        #parse_yaml_result()
        # wait 1 second while the kosmtik page updates
        time.sleep(1)








    def load_tracker(self, ):

        pass







def main():



    # Initialise agent simulation
    simulation = Simulation()
    simulation.read_in_event_config(json_file = "./config/example_config_with_infection.json") # read in event config json file

    simulation.initialise_simulation()
    # Initialise clock
    # Initialise the Clock
    clock = Clock()
    while clock.tstep_count < 10000:

        simulation.tstep()

        # Advance the clock on one tstep (currently hardcoded to advance 1min)
        clock.update_tstep()
        clock.update_time()
        clock.update_day()
        print("tstep_count",clock.tstep_count)

    print("tstep_count",clock.tstep_count)




if __name__ == "__main__":

    main()

