'''
contains all methods for visualisation tasks
'''

import matplotlib.pyplot as plt
import matplotlib as mpl
import geopandas as gpd
import geoplot.crs as gcrs
import geoplot as gplt
import numpy as np
import pandas as pd
from shapely.geometry import Point, LineString, shape
import ruamel.yaml as yaml
from parse_yaml import parse_config
import os




def set_style(Config):
    '''sets the plot style

    '''
    if Config.plot_style.lower() == 'dark':
        mpl.style.use('plot_styles/dark.mplstyle')


def build_fig_geo(Config, shapefile = './postcode_shape_files/osm_north_london.shp', figsize=(5,7)):
    # set style parameters for plot
    set_style(Config)
    # Set total size of figure to 5'' x 7''
    fig = plt.figure(figsize=(5,7))
    # specify space where plots will be placed. There will be 2 subplots
    # one on each row where each plot will stretch across the entire screen
    spec = fig.add_gridspec(ncols=1, nrows=2, height_ratios=[10,5])

    # read in shapefile for map
    map_df = gpd.read_file(shapefile)


    #set projection for shapefile in  first subplot
    ax1 = fig.add_subplot(spec[0,0], projection=gcrs.AlbersEqualArea())

    extent = [-0.18, 51.62,  -0.10, 51.7]
    # plot map
    gplt.polyplot(map_df['geometry'], projection=gcrs.AlbersEqualArea(), ax=ax1, extent=extent)

    plt.title('Map showing location of infected individuals')
    # plt.show(ax1)

    # Plot to show SIR curve
    ax2 = fig.add_subplot(spec[1,0])
    ax2.set_title('number of infected')
    #ax2.set_xlim(0, simulation_steps)
    ax2.set_ylim(0, Config.pop_size + 100)
    return fig, spec, ax1, ax2, map_df



def draw_tstep(Config,
               fig, ax1, ax2, shapefile_df):
    #construct plot and visualise

    #get color palettes
    palette = Config.get_palette()

    # specify space where plots will be placed. There will be 2 subplots
    # one on each row where each plot will stretch across the entire screen
    spec = fig.add_gridspec(ncols=1, nrows=2, height_ratios=[10,5])
    # clear previous subplots
    ax1.clear()
    ax2.clear()

    extent = [-0.18, 51.62,  -0.10, 51.7]
    #set projection for shapefile in  first subplot
    ax1 = gplt.polyplot(shapefile_df, projection=gcrs.AlbersEqualArea(), ax=ax1)


    # if Config.self_isolate and Config.isolation_bounds != None:
    #     build_hospital(Config.isolation_bounds[0], Config.isolation_bounds[2],
    #                    Config.isolation_bounds[1], Config.isolation_bounds[3], ax1,
    #                    addcross = False)

    #plot population segments
    all_agents = Config.point_plots_matrix

    # # Create nd array containing healthy, infected, immune and fatalities in one column and a second column containing label
    # healthy = population[population[:,6] == 0][:,1:3]
    # healthy_label = ['healthy'] * healthy.shape[0]

    # infected = population[population[:,6] == 1][:,1:3]
    # infected_label = ['infected'] * infected.shape[0]

    # immune = population[population[:,6] == 2][:,1:3]
    # immune_label = ['immune'] * immune.shape[0]

    # fatalities = population[population[:,6] == 3][:,1:3]
    # fatalities_label = ['fatalities'] * fatalities.shape[0]

    # # merge all data together in one nd array for plotting
    # pop_coordinates = np.concatenate((healthy, infected, immune, fatalities))

    # pop_labels = np.concatenate((healthy_label, infected_label, immune_label, fatalities_label))

    # pop_matrix = np.vstack((pop_coordinates.T, pop_labels))
    # pop_df = pd.DataFrame(pop_matrix.T, columns = ['Longitude', 'Latitude', 'Label'])
    pop_df = pd.DataFrame(all_agents, columns = ['geometry', 'label', 'disease_progression'])
    # Manually added landmarks for now
    # pop_df = pop_df.append({'geometry' : Point(-0.1256032, 51.63368), 'label' : 'supermarket'}, ignore_index=True)
    # pop_df = pop_df.append({'geometry' : Point(-0.1713237, 51.6495658), 'label' : 'supermarket'}, ignore_index=True)
    # pop_df = pop_df.append({'geometry' : Point(-0.1137062, 51.6347074), 'label' : 'park'}, ignore_index=True)
    # pop_df = pop_df.append({'geometry' : Point(-0.1693677, 51.6615703), 'label' : 'home'}, ignore_index=True)
    # pop_df = pop_df.append({'geometry' : Point(-0.1705196, 51.6665827), 'label' : 'home'}, ignore_index=True)

    pop_gdf = gpd.GeoDataFrame(pop_df, geometry=pop_df.geometry)

    # pop_gdf = gpd.GeoDataFrame(all_agents, columns = ['geometry', 'label'])

    extent = [-0.18, 51.62,  -0.10, 51.7]
    extent = [-0.2671, 51.6167,  -0.1198, 51.6940]
    gplt.pointplot(pop_gdf, ax=ax1, extent=extent, hue='label', s= 2)


    # plt.show()
    plt.draw()
    plt.pause(0.001)
    # Convert to geodataframe and plot on axis
    # pop_gdf = gpd.GeoDa0taFrame(pop_df, geometry=gpd.points_from_xy(pop_df.Longitude.astype(float).values, pop_df.Latitude.astype(float).values))
    # gplt.pointplot(pop_gdf, ax=ax1, extent=shapefile_df.total_bounds, hue = 'Label', legend=True)
    # gplt.pointplot(pop_gdf, ax=ax1, hue = 'Label', legend=True)


def parse_agent_location(Config):

    #plot population segments
    all_agents = Config.point_plots_matrix

    pop_df = pd.DataFrame(all_agents, columns = ['geometry', 'label', 'disease_progression'])
    # pop_df = pd.DataFrame(all_agents, columns = ['geometry', 'label'])

    # pop_df = pop_df.append({'geometry' : Point(-0.1256032, 51.63368), 'label' : 'supermarket'}, ignore_index=True)
    # pop_df = pop_df.append({'geometry' : Point(-0.1713237, 51.6495658), 'label' : 'supermarket'}, ignore_index=True)
    # pop_df = pop_df.append({'geometry' : Point(-0.1137062, 51.6347074), 'label' : 'park'}, ignore_index=True)
    # pop_df = pop_df.append({'geometry' : Point(-0.1693677, 51.6615703), 'label' : 'home'}, ignore_index=True)
    # pop_df = pop_df.append({'geometry' : Point(-0.1705196, 51.6665827), 'label' : 'home'}, ignore_index=True)


    pop_gdf = gpd.GeoDataFrame(pop_df, geometry=pop_df.geometry)
    pop_gdf.index.name = 'id'
    # local machine file path
    # pop_gdf.to_file("/Users/kevinryan/Documents/City_DSI/population_movement_simulations/openstreetmap-carto/output.json", index=True, driver="GeoJSON")
    # docker file path
    pop_gdf.to_file("/openstreetmap-carto/output.json", index=True, driver="GeoJSON")

    # convert_df_2_string(pop_gdf)

    # parse_yaml_result()

    # str_out = convert_df_2_string(pop_gdf)
    # assign_agent_loc_2_mml_file(updated_locations = str_out)
    # return str_out


def convert_df_2_string(df):
    """
    Convert data frame rows to string output where each new line is defined as \n
    """
    # ititialise string
    output = 'agent,wkt\n'
    for i, row in df.iterrows():
        if i == len(df) - 1:
            output += str(row['label']) + ',' + str(row['geometry'])
        else:
            output += str(row['label']) + ',' + str(row['geometry']) + '\n'
    # set environment variable ${AGENTS}
    # os.environ['AGENTS'] = output
    return output

# local machine version
# def assign_agent_loc_2_mml_file(file='/Users/kevinryan/Documents/City_DSI/population_movement_simulations/openstreetmap-carto/project.mml', updated_locations = None):
# docker version
def assign_agent_loc_2_mml_file(file='/openstreetmap-carto/project.mml', updated_locations = None):

    yml = yaml.YAML()
    yml.preserve_quotes = True
    yml.width = 4096
    with open(file, 'r') as stream:
        file_string = yml.load(stream)
    # update project.mml file with current agent locations
    file_string['Layer'][-1]['Datasource']['inline'] = updated_locations
    # write to yaml file
    # local machine version
    # with open('/Users/kevinryan/Documents/City_DSI/population_movement_simulations/openstreetmap-carto/project.mml', 'w') as file:
    # docker version
    with open('/openstreetmap-carto/project.mml', 'w') as file:

        yml.indent(mapping=2, sequence=4, offset=2)
        documents = yml.dump(file_string, file)


def parse_yaml_result():
    # local machine version
    # conf = parse_config(path="/Users/kevinryan/Documents/City_DSI/population_movement_simulations/openstreetmap-carto/project.mml")
    # with open('/Users/kevinryan/Documents/City_DSI/population_movement_simulations/openstreetmap-carto/project.mml', 'w') as file:
    # docker version
    conf = parse_config(path="/openstreetmap-carto/project.mml")
    with open('/openstreetmap-carto/project.mml', 'w') as file:
        yaml.dump(conf, file)




