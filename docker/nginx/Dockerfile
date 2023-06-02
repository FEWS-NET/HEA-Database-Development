FROM --platform=linux/amd64 nginx:1.20

LABEL MAINTAINER Jesaja Everling <jesaja.everling@kimetrica.com>

EXPOSE 80

RUN apt-get -qq update && \
    apt-get -qq install -y --no-install-recommends \
        # Kimetrica standard packages
        ca-certificates \
        curl \
        iproute2 \
        nano \
        vim && \
    apt-get -y autoremove && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    rm -f /var/cache/apt/archives/*.deb

# Copies nginx.conf to a temporary file, so that we can use envsubst to replace environment variables on startup
COPY mime.types /etc/nginx/mime.types
COPY nginx.conf /etc/nginx/nginx.conf.template

# Use envsubst to replace only those environment variables that are defined in the OS,
# using the Bash built-in compgen to avoid envsubst replacing things that look like
# environment variables but aren't, e.g. `proxy_set_header Host $http_host;`
CMD /bin/bash -c "envsubst \"`printf '${%s} ' $(bash -c \"compgen -A variable\")`\" < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf && nginx -g 'daemon off;'"
