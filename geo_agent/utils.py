'''
collection of utility methods shared across files
'''

import os

def check_folder(folder='render/'):
    '''check if folder exists, make if not present'''
    if not os.path.exists(folder):
            os.makedirs(folder)



def _closest_point_on_way (data_base_cursor = None, osm_id = None, lon = None, lat = None):
    """
    input current database cursor and osm_id of way object
    Return nearest point to inputted lon and lat
    """
    query = f"SELECT ST_X(ST_ClosestPoint(aline,pt)), ST_Y(ST_ClosestPoint(aline,pt)) As cp_line_pt FROM (SELECT 'POINT({lon} {lat})'::geography::geometry As pt, (select the_geom from osm_ways where osm_id = {osm_id}) As aline) As output;"
    # Execute query
    data_base_cursor.execute(query)

    closest_point = list(data_base_cursor)[0]
    lon, lat = closest_point[0], closest_point[1]
    return lon, lat
