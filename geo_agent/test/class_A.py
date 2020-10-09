import psycopg2
from shapely import geometry, ops, wkb
import time
import pyproj
import numpy as np



def ways_tab(convert_osm_nodes_sql_2_numpy, convert_osm_ways_vertices_sql_2_numpy):
    # Connect to database
    print("I was here")
    conn = psycopg2.connect(dbname = "london_routing", user = "kevinryan", host = "localhost")
    curs = conn.cursor()
    t1 = time.time()
    start = 2448172873
    end = 2372627054
    curs.execute("select osm_id, attributes -> 'lon' as lon, attributes -> 'lat' as lat, svals(slice(tags, ARRAY['leisure','shop'])) from osm_nodes where tags -> 'shop' = 'supermarket' or tags -> 'leisure' = 'park';")
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




a,b = ways_tab(convert_osm_nodes_sql_2_numpy, convert_osm_ways_vertices_sql_2_numpy)




    # def __init__(self):
    #     # Connect to database
    #     self.projectlon_lat_2_utm = pyproj.Proj(proj='utm', zone=30, ellps='WGS84', preserve_units=True)
    #     print("I was here")
    #     conn = psycopg2.connect(dbname = "london_routing", user = "kevinryan", host = "localhost")
    #     curs = conn.cursor()
    #     t1 = time.time()
    #     start = 2448172873
    #     end = 2372627054
    #     curs.execute("select osm_id, attributes -> 'lon' as lon, attributes -> 'lat' as lat, svals(slice(tags, ARRAY['leisure','shop'])) from osm_nodes where tags -> 'shop' = 'supermarket' or tags -> 'leisure' = 'park';")
    #     results = curs.fetchall()
    #     self.convert_osm_nodes_sql_2_numpy(results)

    #     curs.execute("select osm_id, lon, lat from ways_vertices_pgr;")

    #     ways_vertices = curs.fetchall()
    #     self.convert_osm_ways_vertices_sql_2_numpy(ways_vertices)

    # def convert_osm_nodes_sql_2_numpy(self,sql_table):
    #     """
    #         convert sql table to numpy array
    #     """

    #     rows = []
    #     for res in sql_table:
    #         x, y = self.latlon_2_yx(float(res[1]), float(res[2]))
    #         res_elem = (res[0], float(res[1]), float(res[2]), y, x, res[3])
    #         rows.append(res_elem)

    #     # convert sql table to numpy array
    #     dt = np.dtype([('osm_id', 'i4'), ('lon', 'float'), ('lat', 'float'), ('y', 'float'), ('x', 'float'), ('tags', 'U12')])

    #     self.osm_nodes_np_arr = np.array(rows, dt)
    #     # sort according to location
    #     self.osm_nodes_np_arr = self.osm_nodes_np_arr[np.lexsort((self.osm_nodes_np_arr['y'], self.osm_nodes_np_arr['x']))]



    # def convert_osm_ways_vertices_sql_2_numpy(self,sql_table):
    #     """
    #         convert sql table to numpy array
    #     """

    #     rows = []
    #     for res in sql_table:
    #         x, y = self.latlon_2_yx(float(res[1]), float(res[2]))
    #         res_elem = (res[0], float(res[1]), float(res[2]), y, x)
    #         rows.append(res_elem)

    #     # convert sql table to numpy array
    #     # dt = np.dtype([('osm_id', 'i4'), ('lon', 'float'), ('lat', 'float'), ('y', 'float'), ('x', 'float')])
    #     dt = np.dtype(float)

    #     self.osm_waysvertex_np_arr = np.array(rows, dt)
    #     # sort according to location
    #     y = self.osm_waysvertex_np_arr[:,3] # sort by y
    #     x = self.osm_waysvertex_np_arr[:,4] # sort by x
    #     self.osm_waysvertex_np_arr = self.osm_waysvertex_np_arr[np.lexsort((x,y))]


    # def latlon_2_yx(self, lat=None, lon=None):

    #     """
    #     Converts WGS84 lat lon values to UTM
    #     """
    #     # Project lon lat coordinates into UTM scale
    #     return self.projectlon_lat_2_utm(lat, lon)


    # def yx_2_latlon(self,y,x):
    #     """
    #     Converts y,x UTM values to WGS84 lat, lon
    #     """
    #     # Project UTM y, x values to lon lat
    #     return self.projectlon_lat_2_utm(lat, lon, inverse=True)


    # # Connect to database
    # conn = psycopg2.connect(dbname = "london_routing", user = "kevinryan", host = "localhost")
    # curs = conn.cursor()
    # t1 = time.time()
    # start = 2448172873
    # end = 2372627054
    # curs.execute("SELECT seq, edge, b.the_geom AS \"the_geom (truncated)\", b.name FROM pgr_dijkstra('SELECT gid as id, source_osm as source, target_osm as target, length as cost FROM ways',%s, %s, false) a INNER JOIN ways b ON (a.edge = b.gid) ORDER BY seq;", [start, end])

    # __conf = {
    #     'route_list' : [wkb.loads(row[2], hex=True) for row in curs]
    #     }

    # t2 = time.time()
    # total = t2 -t1

    # print(total)

    # @staticmethod
    # def config(name):
    #     return A.__conf[name]


