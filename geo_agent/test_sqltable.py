import psycopg2
import numpy as np
import time
import pyproj
import geopy.distance
import math


# Connect to database
conn = psycopg2.connect(dbname = "london_routing", user = "kevinryan", host = "localhost")
curs = conn.cursor()

# execute query to retrieve table in memory
curs.execute("select osm_id, attributes -> 'lon' as lon, attributes -> 'lat' as lat, svals(slice(tags, ARRAY['leisure','shop'])) from osm_nodes where tags -> 'shop' = 'supermarket' or tags -> 'leisure' = 'park';")


num_rows = int(curs.rowcount)
print(num_rows)

results = curs.fetchall()



projectlon_lat_2_utm = pyproj.Proj(proj='utm', zone=30, ellps='WGS84', preserve_units=True)
rows = []
for res in results:
    x, y = projectlon_lat_2_utm(float(res[1]), float(res[2]))
    res_elem = (res[0], float(res[1]), float(res[2]), y, x, res[3])
    rows.append(res_elem)


# convert sql table to numpy array
dt = np.dtype([('osm_id', 'i4'), ('lon', 'float'), ('lat', 'float'), ('y', 'float'), ('x', 'float'), ('tags', 'U12')])

D = np.array(rows, dt)
# sort according to location
D = D[np.lexsort((D['y'], D['x']))]

t1 = time.time()
print(D[(D['tags'] == "supermarket") & ((D['lon'] > -0.0901794) & (D['lon'] < 0.1)) & ((D['lat'] > 51.1) & (D['lat'] < 52.5))])
t2 = time.time()
total1 = t2-t1

print(total1)



# test home location
home =(51.653705, -0.195408)

#geopy.distance.vincenty(home, coords_2).km

# def distance_calc(current_lat,current_lon, amenity = None, distance):

def buffer_line(current_lat, current_lon, br_list = [0, 1.57, 3.142, 4.712], d = 5):
    R = 6378.1 #Radius of the Earth
    # br_list is 0, 90, 180, 270 degrees converted to radians.

    lat1 = math.radians(current_lat) #Current lat point converted to radians
    lon1 = math.radians(current_lon) #Current long point converted to radians
    # d = 15 #Distance in km
    coord_list =[]
    for br in br_list:
        print(br)
        lat2 = math.asin( math.sin(lat1)*math.cos(d/R) +
         math.cos(lat1)*math.sin(d/R)*math.cos(br))

        lon2 = lon1 + math.atan2(math.sin(br)*math.sin(d/R)*math.cos(lat1),
                 math.cos(d/R)-math.sin(lat1)*math.sin(lat2))

        lat2 = math.degrees(lat2)
        lon2 = math.degrees(lon2)
        coord_list.append((lat2, lon2))
    return coord_list

def slice_array(start_lat, start_lon, array_in, tag = "supermarket"):
    bounds = buffer_line(start_lat, start_lon)

    print(bounds[3][1])
    print(bounds[1][1])
    print(bounds[2][0])
    print(bounds[0][0])
    sliced_array = array_in[(array_in['tags'] == tag) & ((array_in['lon'] > bounds[3][1]) & (array_in['lon'] < bounds[1][1])) & ((array_in['lat'] > bounds[2][0]) & (array_in['lat'] < bounds[0][0]))]

    return sliced_array

def find_nearest(start_lat, start_lon, arr):
    tup_candidates = arr[['lat', 'lon']]
    print(tup_candidates.shape)
    print(tup_candidates.shape[0])
    start_up = [(start_lat, start_lon)] * tup_candidates.shape[0]
    print(start_up)
    dt=np.dtype('float,float')
    start_arr = np.array(start_up, dtype=dt)
    print(start_arr.shape)
    print(start_arr)
    # vectorise distance function for ease of readability
    vect_dist_func = np.vectorize(geopy.distance.vincenty)
    vals = vect_dist_func(start_arr, tup_candidates)
    # find index of nearest amenity
    val = np.argmin(np.array([dist.km for dist in vals]))
    lat, lon = arr['lat'][val], arr['lon'][val]
    return lat, lon


t1 = time.time()
slice = slice_array(home[0], home[1], D, tag = "supermarket")
t2 = time.time()

total1 = t2-t1

print(total1)

print("hey", slice)
print(D[['lat', 'lon']].shape[0])

lat, lon = find_nearest(home[0], home[1], slice)
print("DISTS",lat, lon)









# projectlon_lat_2_utm = pyproj.Proj(proj='utm', zone=30, ellps='WGS84', preserve_units=True)

# projectlon_lat_2_utm(lat, lon)


# projectlon_lat_2_utm(lat, lon, inverse=True)



