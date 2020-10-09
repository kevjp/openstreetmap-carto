import geopandas
import shapely.geometry
gdf = geopandas.GeoDataFrame(geometry=[shapely.geometry.Point(x, x) for x in [5,4,3,2]])
gdf.index.name = 'id'
gdf.to_file("test.geojson", index=True, driver='GeoJSON')
gdf.to_file("test.geojson1", driver='GeoJSON')