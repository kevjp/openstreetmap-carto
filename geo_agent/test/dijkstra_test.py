import psycopg2
import numpy as np
import time
import pyproj
import geopy.distance
import math


# Connect to database
conn = psycopg2.connect(dbname = "london_routing", user = "kevinryan", host = "localhost")
curs = conn.cursor()


# snpwberry_close = (51.654277, -0.196017)
# waitrose = (51.655883, -0.203937)
# start = 1629133901 # snowberry close
# end = 1380218940 # waitrose

# start = 2448172873
# end = 2372627054
# t1 = time.time()
# curs.execute("SELECT seq, edge, b.the_geom AS \"the_geom (truncated)\", b.name FROM pgr_dijkstra('SELECT gid as id, source_osm as source, target_osm as target, length as cost FROM ways',%s, %s, false) a INNER JOIN ways b ON (a.edge = b.gid) ORDER BY seq;", [start, end])

# t2 = time.time()
# total = t2 - t1

# print(total)


# t1 = time.time()
# curs.execute("SELECT seq, edge, b.the_geom AS \"the_geom (truncated)\", b.name FROM pgr_dijkstra('select gid as id, source_osm as source, target_osm as target, length as cost FROM ways as ways_outer, (select ST_Expand(ST_Extent(the_geom),0.1) as box from ways as box_table where box_table.source_osm = 1629133901 OR box_table.target_osm = 1380218940) as box_final where ways_outer.the_geom && box_final.box', 1629133901, 1380218940, false) a INNER JOIN ways b ON (a.edge = b.gid) ORDER BY seq;", [start, end])
# t2 = time.time()
# total = t2 - t1
# print(total)

# t1 = time.time()
# curs.execute("SELECT seq, edge, b.the_geom FROM pgr_dijkstra('select gid as id, source_osm as source, target_osm as target, length as cost FROM ways as ways_outer, (select ST_Expand(ST_Extent(the_geom),0.05) as box from ways as box_table where box_table.source_osm = 1629133901 OR box_table.target_osm = 1380218940) as box_final where ways_outer.the_geom && box_final.box', 1629133901, 1380218940, false) as a INNER JOIN ways as b ON a.edge = b.gid ORDER BY seq;", [start, end])
# t2 = time.time()
# total = t2 - t1
# print(total)


from shapely import geometry, ops, wkb
start = 2372627054
end = 19191797
# end = 1889862438

start = 19191797
end = 1889862438

# Using OSM ids as source and target values calculate shortest route and convert to shapely geometric object
query = f"SELECT seq, edge, b.the_geom AS \"the_geom (truncated)\" FROM pgr_dijkstra('select gid as id, source_osm as source, target_osm as target, length as cost FROM ways as ways_outer, (select ST_Expand(ST_Extent(the_geom),0.1) as box from ways as box_table where box_table.source_osm = {start} OR box_table.target_osm = {end}) as box_final where ways_outer.the_geom && box_final.box', {start}, {end}, false) as a INNER JOIN ways as b ON a.edge = b.gid ORDER BY seq;"
query = f"SELECT UNNEST(pgr_flipedges(ARRAY(SELECT st_astext(b.the_geom) AS \"the_geom (truncated)\" FROM pgr_dijkstra('select gid as id, source_osm as source, target_osm as target, length as cost FROM ways as ways_outer, (select ST_Expand(ST_Extent(the_geom),0.05) as box from ways as box_table where box_table.source_osm = 19191797 OR box_table.target_osm = 1889862438) as box_final where ways_outer.the_geom && box_final.box', {start}, {end}, false) as a INNER JOIN ways as b ON a.edge = b.gid ORDER BY seq)));"
curs.execute(query)
# Load_populations.database.cursor.execute("SELECT seq, edge, b.the_geom AS \"the_geom (truncated)\", b.name FROM pgr_dijkstra('SELECT gid as id, source_osm as source, target_osm as target, length as cost FROM ways',%s, %s, false) a INNER JOIN ways b ON (a.edge = b.gid) ORDER BY seq;", [start, end])
#route_list = [wkb.loads(row[2], hex=True) for row in curs]
route_list = [wkb.loads(row[0], hex=True) for row in curs]
# print("route_list", list(route_list[0].coords))
# print("route_list", route_list)
for v in route_list:
    print(v)
# merge linestrings into one large shapely linestring object
merged_routes = ops.linemerge([*route_list])
# print(merged_routes)

print("!!!!!!!!!!!!!!!!!!!!!!!!!")
start = 1889862438
end = 19191797
start = 2372627054
end =2448172873
query = f"SELECT seq, edge, b.the_geom AS \"the_geom (truncated)\" FROM pgr_dijkstra('select gid as id, source_osm as source, target_osm as target, length as cost FROM ways as ways_outer, (select ST_Expand(ST_Extent(the_geom),0.1) as box from ways as box_table where box_table.source_osm = {start} OR box_table.target_osm = {end}) as box_final where ways_outer.the_geom && box_final.box', {start}, {end}, false) as a INNER JOIN ways as b ON a.edge = b.gid ORDER BY seq;"
query = f"SELECT UNNEST(pgr_flipedges(ARRAY(SELECT st_astext(b.the_geom) AS \"the_geom (truncated)\" FROM pgr_dijkstra('select gid as id, source_osm as source, target_osm as target, length as cost FROM ways as ways_outer, (select ST_Expand(ST_Extent(the_geom),0.1) as box from ways as box_table where box_table.source_osm = {start} OR box_table.target_osm = {end}) as box_final where ways_outer.the_geom && box_final.box', {start}, {end}, false) as a INNER JOIN ways as b ON a.edge = b.gid ORDER BY seq)));"
query = f"SELECT ST_Transform(ST_SetSRID(UNNEST(pgr_flipedges(ARRAY(SELECT st_astext(b.the_geom) FROM pgr_dijkstra('select gid as id, source_osm as source, target_osm as target, length as cost FROM ways as ways_outer, (select ST_Expand(ST_Extent(the_geom),0.1) as box from ways as box_table where box_table.source_osm = {start} OR box_table.target_osm = {end}) as box_final where ways_outer.the_geom && box_final.box', {start}, {end}, false) as a INNER JOIN ways as b ON a.edge = b.gid ORDER BY seq))),4326), 32630);"
curs.execute(query)
# Load_populations.database.cursor.execute("SELECT seq, edge, b.the_geom AS \"the_geom (truncated)\", b.name FROM pgr_dijkstra('SELECT gid as id, source_osm as source, target_osm as target, length as cost FROM ways',%s, %s, false) a INNER JOIN ways b ON (a.edge = b.gid) ORDER BY seq;", [start, end])

route_list = [wkb.loads(row[0], hex=True) for row in curs]


# for v in route_list:
#     print(v)
# merge linestrings into one large shapely linestring object
merged_routes_1 = ops.linemerge([*route_list])


# assert(merged_routes == merged_routes_1)

print(merged_routes_1)
t =time.time()
point = merged_routes_1.interpolate(50000).wkt
t1 =time.time()
print (t1 -t)
print("separator", point)
# print(merged_routes_1)








