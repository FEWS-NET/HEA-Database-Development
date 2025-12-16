# Use a third party multicarch base image for compatibility with both ARM and AMD architectures
# until PostGIS fix https://github.com/postgis/docker-postgis/issues/216
FROM ghcr.io/baosystems/postgis:17-3.5

COPY create_db.sh /docker-entrypoint-initdb.d/create_db.sh
