
import json

json_file = "/Users/kevinryan/Documents/City_DSI/population_movement_simulations/openstreetmap-carto/geo_agent/config/example_config_with_infection.json"

f = open(json_file)

event_json = json.load(f)


for event in event_json["events"]:
    print(event['description'])
    print(event['time_before_event_repeat'])