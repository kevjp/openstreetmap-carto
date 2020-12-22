import psycopg2

class Database():


    """
    Class responsible for connect to OSM local database


    Postgres database schema for osm2pgrouting of OSM file

    routing=# \d
                        List of relations
     Schema |           Name           |   Type   |   Owner
    --------+--------------------------+----------+-----------
     public | configuration            | table    | postgres
     public | configuration_id_seq     | sequence | postgres
     public | geography_columns        | view     | kevinryan
     public | geometry_columns         | view     | kevinryan
     public | osm_nodes                | table    | postgres
     public | osm_relations            | table    | postgres
     public | osm_ways                 | table    | postgres
     public | pointsofinterest         | table    | postgres
     public | pointsofinterest_pid_seq | sequence | postgres
     public | spatial_ref_sys          | table    | kevinryan
     public | ways                     | table    | postgres
     public | ways_gid_seq             | sequence | postgres
     public | ways_vertices_pgr        | table    | postgres
     public | ways_vertices_pgr_id_seq | sequence | postgres
    (14 rows)

    ways contains edges in maps defined by source and target values
    """

    # docker login
    def __init__(self, name = 'routing', user = 'docker', password = 'docker', host = 'pg_routing'):
    # local machine login
    #def __init__(self, name = 'latest_routing', user = 'kevinryan', host = 'localhost'):
        # docker login
        self._conn = psycopg2.connect(f"dbname = {name} user = {user} password = {password} host = {host}")
        # local machine login
        # self._conn = psycopg2.connect(f"dbname = {name} user = {user} host = {host}")
        self._curs = self._conn.cursor()


    @property
    def connection (self):
        return self._conn

    @property
    def cursor(self):
        return self._curs


