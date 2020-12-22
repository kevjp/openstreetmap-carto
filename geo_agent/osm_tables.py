from subpopulations import Load_populations
import pyproj
import numpy as np

import psycopg2
from shapely import geometry, ops, wkb
import time
import pyproj
import numpy as np



def ways_tab(convert_osm_nodes_sql_2_numpy, convert_osm_ways_vertices_sql_2_numpy):
    # Connect to database
    # local machine
    # conn = psycopg2.connect(dbname = "latest_routing", user = "kevinryan", host = "localhost")
    # docker version
    conn = psycopg2.connect(dbname = 'routing', user = 'docker', password = 'docker', host = 'pg_routing')
    # conn = psycopg2.connect(dbname = "gis", user = "postgres", host = "db")
    curs = conn.cursor()
    t1 = time.time()
    start = 2448172873
    end = 2372627054
    # curs.execute("select osm_id, attributes -> 'lon' as lon, attributes -> 'lat' as lat, svals(slice(tags, ARRAY['leisure','shop'])) from osm_nodes where tags -> 'shop' = 'supermarket' or tags -> 'leisure' = 'park';")
    curs.execute("select osm_id, attributes -> 'lon' as lon, attributes -> 'lat' as lat, svals(slice(tags, ARRAY['leisure','shop','amenity'])) from osm_nodes where tags -> 'shop' = 'supermarket' or tags -> 'leisure' = 'park' or tags -> 'amenity' = 'hospital';")
    # curs.execute("select osm_id, attributes -> 'lon' as lon, attributes -> 'lat' as lat, svals(slice(tags, ARRAY['leisure','shop'])) from planet_osm_point where tags -> 'shop' = 'supermarket' or tags -> 'leisure' = 'park';")
    results = curs.fetchall()
    osm_nodes_np_arr = convert_osm_nodes_sql_2_numpy(results)

    curs.execute("select osm_id, lon, lat from ways_vertices_pgr;")

    ways_vertices = curs.fetchall()
    osm_waysvertex_np_arr = convert_osm_ways_vertices_sql_2_numpy(ways_vertices)
    return osm_nodes_np_arr, osm_waysvertex_np_arr

def convert_osm_nodes_sql_2_numpy(sql_table):
    """
        convert sql table to numpy array
    """
    projectlon_lat_2_utm = pyproj.Proj(proj='utm', zone=30, ellps='WGS84', preserve_units=True)
    rows = []
    for res in sql_table:
        x, y = projectlon_lat_2_utm(float(res[1]), float(res[2]))
        res_elem = (res[0], float(res[1]), float(res[2]), y, x, res[3])
        rows.append(res_elem)

    # convert sql table to numpy array
    dt = np.dtype([('osm_id', 'i4'), ('lon', 'float'), ('lat', 'float'), ('y', 'float'), ('x', 'float'), ('tags', 'U12')])

    osm_nodes_np_arr = np.array(rows, dt)
    # sort according to location
    osm_nodes_np_arr = osm_nodes_np_arr[np.lexsort((osm_nodes_np_arr['y'], osm_nodes_np_arr['x']))]
    return osm_nodes_np_arr



def convert_osm_ways_vertices_sql_2_numpy(sql_table):
    """
        convert sql table to numpy array
    """
    projectlon_lat_2_utm = pyproj.Proj(proj='utm', zone=30, ellps='WGS84', preserve_units=True)
    rows = []
    for res in sql_table:
        x, y = projectlon_lat_2_utm(float(res[1]), float(res[2]))
        res_elem = (res[0], float(res[1]), float(res[2]), y, x)
        rows.append(res_elem)

    # convert sql table to numpy array
    # dt = np.dtype([('osm_id', 'i4'), ('lon', 'float'), ('lat', 'float'), ('y', 'float'), ('x', 'float')])
    dt = np.dtype(float)

    osm_waysvertex_np_arr = np.array(rows, dt)

    # sort according to location
    y = osm_waysvertex_np_arr[:,3] # sort by y
    x = osm_waysvertex_np_arr[:,4] # sort by x
    osm_waysvertex_np_arr = osm_waysvertex_np_arr[np.lexsort((x,y))]
    return osm_waysvertex_np_arr

t0 = time.time()
osm_nodes_np_arr,osm_waysvertex_np_arr = ways_tab(convert_osm_nodes_sql_2_numpy, convert_osm_ways_vertices_sql_2_numpy)
t1 = time.time()
total1 = t1-t0
print("check",total1)





