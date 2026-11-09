# Use a third party multicarch base image for compatibility with both ARM and AMD architectures
# until PostGIS fix https://github.com/postgis/docker-postgis/issues/216
FROM ghcr.io/baosystems/postgis:18-3.6@sha256:dd7515b7d8b8b8bac3516a9c3e12584df5890b0864c29295c1b934ecd1db81a7

COPY create_db.sh /docker-entrypoint-initdb.d/create_db.sh
