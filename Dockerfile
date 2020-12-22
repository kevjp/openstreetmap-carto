FROM ubuntu:bionic

RUN ls
# Style dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
    ca-certificates curl vim gnupg postgresql-client python3 python3-distutils \
    fonts-hanazono fonts-noto-cjk fonts-noto-hinted fonts-noto-unhinted \
    mapnik-utils nodejs npm ttf-unifont unzip && rm -rf /var/lib/apt/lists/*

# Kosmtik with plugins, forcing prefix to /usr because bionic sets
# npm prefix to /usr/local, which breaks the install
# RUN npm set prefix /usr && npm install -g kosmtik
# Replace original kosmtik install with my version which uses leaflet realtime
RUN npm set prefix /usr && npm install -g https://github.com/kevjp/kosmtik/archive/v0.0.17.1.tar.gz

WORKDIR /usr/lib/node_modules/kosmtik/
RUN kosmtik plugins --install kosmtik-overpass-layer \
                    --install kosmtik-fetch-remote \
                    --install kosmtik-overlay \
                    --install kosmtik-open-in-josm \
                    --install kosmtik-map-compare \
                    --install kosmtik-osm-data-overlay \
                    --install kosmtik-mapnik-reference \
                    --install kosmtik-geojson-overlay \
    && cp /root/.config/kosmtik.yml /tmp/.kosmtik-config.yml



# Closing section
RUN mkdir -p /openstreetmap-carto
RUN mkdir -p /agent_locations

COPY /project.mml /agent_locations/project.mml



WORKDIR /
RUN ls
WORKDIR /openstreetmap-carto
RUN ls

USER 1000
CMD sh scripts/docker-startup_geo_agent.sh kosmtik
