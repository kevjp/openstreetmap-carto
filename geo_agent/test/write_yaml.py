
import ruamel.yaml as yaml
import geopandas as gpd
#import yaml

fname = 'output.json'
pop_gdf = gpd.read_file(fname)
print(pop_gdf)


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
            # print("row:", row['geometry'], row['label'])
            output += str(row['label']) + ',' + str(row['geometry']) + '\n'
    return output

str_out = convert_df_2_string(pop_gdf)

yml = yaml.YAML()
yml.preserve_quotes = True
yml.width = 4096
file='../../project.mml'

with open(file, 'r') as stream:
    file_string = yml.load(stream)
print("filesrting before ...............\n", file_string['Layer'][-1]['Datasource']['inline'])
file_string['Layer'][-1]['Datasource']['inline'] = str_out
print("filesrting before ...............\n", file_string['Layer'][-1]['Datasource']['inline'])

with open('test.mml', 'w') as file:
        yml.indent(mapping=2, sequence=4, offset=2)
        documents = yml.dump(file_string, file)







# print(str_out)
# file='../../project.mml'

# loader = yaml.SafeLoader
# with open(file, 'r') as stream:
#     file_string = yaml.load(stream, Loader=loader)


# with open('test2.mml', 'w') as file:
#     yaml.dump(file_string, file, sort_keys=False, default_flow_style = False)




# yml = yaml.YAML()
# yml.preserve_quotes = True
# yml.width = 4096
# with open(file, 'r') as stream:
#     file_string = yml.load(stream)





with open('test.mml', 'w') as file:
    yml.indent(mapping=2, sequence=4, offset=2)
    documents = yml.dump(file_string, file)