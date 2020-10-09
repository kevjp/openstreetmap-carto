import psycopg2
from scipy.sparse import csr_matrix
import numpy as np
from sklearn.utils.graph import single_source_shortest_path_length
from sklearn.utils.graph_shortest_path import graph_shortest_path
import time

# connect to the london_routing database
conn = psycopg2.connect(f"dbname = {'london_routing'} user = {'postgres'} host = {'localhost'}")

curs = conn.cursor()

# query to extract ways table from data base
curs.execute("select source, target, length from ways order by source, target;")



data = [] # list of length values
indptr = [0] # pointer to the column indices list. Indicates lower upper range of index values in indices list which relate to the same row
indices = [] # column indices for each row

row_val = 0 # Initialise row_val to 1 indicating the first non zero entry in the graph
for row in curs.fetchall():
    if row[0] == row_val: # check if row relates to the same source vertex as previous row
        indices.append(row[1])
        data.append(row[2])


    else:
        indptr.append(len(indices))
        row_val += 1
        # keep adding 1 to row_val until it equals the next valid vertex entry and add a zero row to the csr_matrix
        while row_val < row[0]:
            indptr.append(len(indices))
            row_val += 1
        # once row_val equals the row[0] entry continue with for loop
        indices.append(row[1])
        data.append(row[2])

indptr.append(len(indices))







check = csr_matrix((data, indices, indptr), dtype=float).toarray()
check2 = csr_matrix((data, indices, indptr), dtype=float)

print(indices[0:5])
print(indptr[0:5])
print(data[0:5])

print(check[0:4,0:5])
print(check.shape)
print(check[6,264306])
 #6 | 264306
t1 = time.time()
route = list(sorted(single_source_shortest_path_length(check2, 1).items()))

t2 = time.time()
total = t2 -t1
print("time", total)
t1 = time.time()
route = graph_shortest_path(check2, directed=False)
t2 = time.time()
total = t2 -t1
print("time", total)


print(route)
