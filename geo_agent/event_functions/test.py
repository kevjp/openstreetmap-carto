from os import path
import sys
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
from clock.Clock import convert_numpy_datetime64_to_mins

print(path.dirname( path.dirname( path.abspath(__file__) ) ))