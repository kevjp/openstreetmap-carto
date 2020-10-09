from subpopulations import translate_2_osm_ways_coords


def xy2osm(self, lat = None, lon = None):

        """
        translate long, lat values to a tuple containing (lon, lat, OSM ways ID)
        tuple
        """

        # Will allow me to translate all locations into adjacent vertices points in ways table
        # selects the nearest OSM reference in OSM ways table to the required location as defined by the points returned from nearest amenity search (<-> is the distance operator)
        Load_populations.database.cursor.execute("select * from ways_vertices_pgr ORDER BY the_geom <-> ST_GeometryFromText('POINT(%s %s)',4326);", (lon, lat))

        # translate into OSM ref
        h = (next(Load_populations.database.cursor))
        self.osm_ways_id, self.lon, self.lat = (h[1], float(h[3]), float(h[4]))

def translate_2_osm_ways_coords(self, lat = None, lon = None):

    """
    lat : list of lat values
    lon : list of lon values
    Translate input coordinates into OSM ways coordinates
    """

    osm_ways_list = []
    nearest_lat_list = []
    nearest_lon_list = []
    nearest_point_convert = []
    for coord in zip(lat, lon):
        xy2osm(lat = coord[0], lon = coord[1]) # generates variables osm_ways_id, lon, lat
        osm_ways_list.append(osm_ways_id) # used to populate osm ways id column
        nearest_lat_list.append(lat) # used to populate lat column
        nearest_lon_list.append(lon) # used to populate lon column
        nearest_point_convert.append(Point(lon, lat)) # used to populate current position column (needs to be a Point object for plotting)






household_data = './data/barnet_points_2.csv'

household_df = pd.read_csv(household_data, delimiter=',')

household_df['geometry'] = household_df['geometry'].apply(wkt.loads)
household_df_geo = gpd.GeoDataFrame(household_df, geometry='geometry')


translate_2_osm_ways_coords(lat = household_df_geo.geometry.y.values, lon = household_df_geo.geometry.x.values)

point_plots_matrix = np.zeros((2, 2), dtype=object)

all_agents = Config.point_plots_matrix


pop_df = pd.DataFrame(all_agents, columns = ['geometry', 'label'])


pop_df.loc[2] = [Point(-0.1256032, 51.63368), 'supermarket']
pop_df.loc[3] = [Point(-0.1713237, 51.6495658), 'supermarket']
pop_df.loc[4] = [Point(-0.1137062, 51.6347074), 'park']
pop_df.loc[5] = [Point(-0.1693677, 51.6615703), 'home']
pop_df.loc[6] = [Point(-0.1705196, 51.6665827), 'home']