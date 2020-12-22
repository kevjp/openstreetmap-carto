from subpopulations import Load_populations
from shapely.geometry import Point

def _find_nearest_v2(lat = None, lon = None, amenity = None):
        """
        Find nearest point to amenity returning nearest osm_ways_id, lat and lon
        """
        amenity = amenity.strip()
        amenity = amenity.replace(" ","")
        amenity_key = amenity.split('=')[0]
        amenity_value = amenity.split('=')[1]

        # SELECT ST_AsText(ST_ClosestPoint(line,pt)) As cp_line_pt FROM (SELECT 'POINT(-0.1687473308241547 51.66176239080847)'::geography::geometry As pt, (select the_geom from osm_ways where osm_id = (select ow.osm_id from osm_ways ow where ow.tags -> 'leisure' = 'park' order by ow.the_geom <-> (SELECT 'SRID=4326;POINT(-0.1687473308241547 51.66176239080847)'::geometry) limit 1)) As line) As foo;
        query = f"SELECT ST_X(ST_ClosestPoint(aline,pt)), ST_Y(ST_ClosestPoint(aline,pt)) As cp_line_pt FROM (SELECT 'POINT({lon} {lat})'::geography::geometry As pt, (select the_geom from osm_ways where osm_id = (select ow.osm_id from osm_ways ow where ow.tags -> '{amenity_key}' = '{amenity_value}' order by ow.the_geom <-> (SELECT 'SRID=4326;POINT({lon} {lat})'::geometry) limit 1)) As aline) As output;"

        Load_populations.database.cursor.execute(query)
        # results = Point(list(Load_populations.database.cursor)[0][0])
        results = list(Load_populations.database.cursor)[0]

        lon, lat = results[0], results[1]
        return lon, lat

def xy2osm(lat = None, lon = None):

        """
        translate long, lat values to a tuple containing (lon, lat, OSM ways ID)
        tuple
        """

        # Will allow me to translate all locations into adjacent vertices points in ways table
        # selects the nearest OSM reference in OSM ways table to the required location as defined by the points returned from nearest amenity search (<-> is the distance operator)
        Load_populations.database.cursor.execute("select * from ways_vertices_pgr ORDER BY the_geom <-> ST_GeometryFromText('POINT(%s %s)',4326);", (lon, lat))

        # translate into OSM ref
        h = (next(Load_populations.database.cursor))
        osm_ways_id, lon, lat = (h[1], float(h[3]), float(h[4]))
        return osm_ways_id, lon, lat

lon, lat = _find_nearest_v2(lat= 51.66176239080847, lon= -0.1687473308241547, amenity = "leisure = park")

print("here", lon, lat )

osm_ways_id, lon, lat = xy2osm(lat = lat, lon = lon)

print(osm_ways_id, lon, lat)