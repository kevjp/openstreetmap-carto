################################################
import psycopg2
import numpy as np
import time
import pyproj
import geopy.distance
import math
import random
from shapely import geometry, ops, wkb
from shapely.geometry import Point, LineString, shape

def cut(line, distance):
    # Cuts a line in two at a distance from its starting point
    if distance <= 0.0 or distance >= line.length:
        return [LineString(line)]
    coords = list(line.coords)
    for i, p in enumerate(coords):
        pd = line.project(Point(p))
        if pd == distance:
            return [
                LineString(coords[:i+1]),
                LineString(coords[i:])]
        if pd > distance:
            cp = line.interpolate(distance)
            return [
                LineString(coords[:i] + [(cp.x, cp.y)]),
                LineString([(cp.x, cp.y)] + coords[i:])]

def joinSegments( linestring_list):
    if linestring_list[0][0] == linestring_list[1][0] or linestring_list[0][0] == linestring_list[1][-1]:
        linestring_list[0].reverse()
    c = linestring_list[0][:]
    for x in linestring_list[1:]:
        if x[-1] == c[-1]:
            x.reverse()
        c += x
    return c



conn = psycopg2.connect(dbname = "london_routing", user = "kevinryan", host = "localhost")
curs = conn.cursor()
speed = 50
time = 10
total_dist_2_travel = speed * time
route_ls = [] # list of linestrings
route_ls_check = []
distance_travelled = 0
prev_ls = None
start_osm = 19191796
while distance_travelled != total_dist_2_travel:
    query = f"select source_osm, target_osm, length_m, ST_Transform(ST_SetSRID(st_astext(the_geom),4326), 32630) from ways where source_osm = {start_osm} or target_osm = {start_osm};"
    curs.execute(query)
    query_list = [*curs]
    res = random.sample(query_list,1)

    ls = wkb.loads(res[0][3], hex=True)
    current_ls = list(ls.coords)

    # generate new start_osm for next query
    if res[0][0] == start_osm:
        start_osm = res[0][1]
    else:
        current_ls.reverse()
        start_osm = res[0][0]
    # print("before pop",current_ls,"\n")
    # if prev_ls:
    #     current_ls.pop(0)

    # Need to orientate current Linestring so it starts from previous ls end point



    # if prev_ls:
    #     print("hello")
    #     if current_ls[-1] == prev_ls[0] or current_ls[-1] == prev_ls[-1]:

    #         print("before pop",current_ls,"\n")
    #         current_ls.pop(0)
    #     else:
    #         current_ls.pop(0)


    print(current_ls,"\n")

    # route_ls_check.append(current_ls)




    dist_still_2_travel = total_dist_2_travel - distance_travelled

    if res[0][2] < dist_still_2_travel:
        current_ls_formatted = LineString(current_ls)
        route_ls_check.append(current_ls_formatted)
        distance_travelled = distance_travelled + res[0][2]
        prev_ls = current_ls
    else:
        current_ls_formatted = LineString(current_ls)

        abridged_ls = current_ls_formatted.interpolate(dist_still_2_travel)
        l_check = cut(current_ls_formatted, dist_still_2_travel)
        route_ls_check.append(l_check[0])
        distance_travelled = distance_travelled + dist_still_2_travel
print("@@@@@@@@@@@",route_ls_check)
for ls in route_ls_check:
    print(list(ls.coords))

merged_routes = ops.linemerge([*route_ls_check])
print("!!!!!!!!!!!!",merged_routes)

c = merged_routes.interpolate(100)
print(c)


# ls_segments = [LineString(l) for l in route_ls_check]
# print(ops.linemerge([*ls_segments]))



