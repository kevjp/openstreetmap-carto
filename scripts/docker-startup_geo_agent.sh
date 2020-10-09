#!/bin/bash --login

# This script is used to start the import of kosmtik containers for the Docker development environment.
# You can read details about that in DOCKER.md

# Testing if database is ready
i=1
MAXCOUNT=60
echo "Waiting for PostgreSQL to be running"
while [ $i -le $MAXCOUNT ]
do
  pg_isready -q && echo "PostgreSQL running" && break
  sleep 2
  i=$((i+1))
done
test $i -gt $MAXCOUNT && echo "Timeout while waiting for PostgreSQL to be running"

case "$1" in
import)
  # Creating default database
  psql -c "SELECT 1 FROM pg_database WHERE datname = 'gis';" | grep -q 1 || createdb gis && \
  psql -d gis -c 'CREATE EXTENSION IF NOT EXISTS postgis;' && \
  psql -d gis -c 'CREATE EXTENSION IF NOT EXISTS hstore;' && \

  # Creating default import settings file editable by user and passing values for osm2pgsql
  if [ ! -e ".env" ]; then
    cat > .env <<EOF
# Environment settings for importing to a Docker container database
PG_WORK_MEM=${PG_WORK_MEM:-16MB}
PG_MAINTENANCE_WORK_MEM=${PG_MAINTENANCE_WORK_MEM:-256MB}
OSM2PGSQL_CACHE=${OSM2PGSQL_CACHE:-512}
OSM2PGSQL_NUMPROC=${OSM2PGSQL_NUMPROC:-1}
OSM2PGSQL_DATAFILE=${OSM2PGSQL_DATAFILE:-data.osm.pbf}
EOF
    chmod a+rw .env
    export OSM2PGSQL_CACHE=${OSM2PGSQL_CACHE:-512}
    export OSM2PGSQL_NUMPROC=${OSM2PGSQL_NUMPROC:-1}
    export OSM2PGSQL_DATAFILE=${OSM2PGSQL_DATAFILE:-data.osm.pbf}
  fi

  # Importing data to a database
  osm2pgsql \
  --cache $OSM2PGSQL_CACHE \
  --number-processes $OSM2PGSQL_NUMPROC \
  --hstore \
  --multi-geometry \
  --database gis \
  --slim \
  --drop \
  --style openstreetmap-carto.style \
  --tag-transform-script openstreetmap-carto.lua \
  $OSM2PGSQL_DATAFILE

  # Downloading needed shapefiles
  scripts/get-external-data.py
  ;;

kosmtik)
  # Creating default Kosmtik settings file
  if [ ! -e ".kosmtik-config.yml" ]; then
    cp /tmp/.kosmtik-config.yml .kosmtik-config.yml
  fi
  export KOSMTIK_CONFIGPATH=".kosmtik-config.yml"
  # echo $KOSMTIK_CONFIGPATH
  cat .kosmtik-config.yml
  cd /
  ls -a
  cd -
  ls
  cd /openstreetmap-carto
  ls



  # Starting Kosmtik
  kosmtik -h
  kosmtik serve project.mml --host 0.0.0.0 --localconfig /openstreetmap-carto/localconfig.json

  # node /usr/lib/node_modules/kosmtik/index.js export project.mml --format png --output /agent_locations --minZoom 15 --maxZoom 16
  # kosmtik export project.mml --format 'png' --output tmp/export.png --minZoom 19 --maxZoom 19 --bounds='-0.20476251840591433,51.65462197274702,-0.2002564072608948,51.65611792315079' --width 1680 --height 899

  # It needs Ctrl+C to be interrupted
  ;;

# geo_agent)
#   conda init bash
#   conda activate $ENV_PREFIX
#   echo $CONDA_PREFIX
#   python main.py
#   ;;

esac
