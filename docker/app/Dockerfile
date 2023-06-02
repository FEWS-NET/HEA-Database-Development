FROM --platform=linux/amd64 python:3.11-buster as base

# set up apt repositories for nodejs and postgres installation
RUN curl -s https://deb.nodesource.com/gpgkey/nodesource.gpg.key | gpg --dearmor | tee /usr/share/keyrings/nodesource.gpg >/dev/null && \
    echo 'deb [signed-by=/usr/share/keyrings/nodesource.gpg] https://deb.nodesource.com/node_12.x buster main' > /etc/apt/sources.list.d/nodesource.list && \
    curl -s https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor | tee /usr/share/keyrings/pgdg.gpg >/dev/null && \
    echo "deb [signed-by=/usr/share/keyrings/pgdg.gpg] http://apt.postgresql.org/pub/repos/apt buster-pgdg main" > /etc/apt/sources.list.d/pgdg.list

RUN apt-get -qq update && \
    apt-get -qq upgrade -y && \
    apt-get -qq install -y --no-install-recommends \
        ca-certificates \
        curl \
        gdal-bin \
        gettext \
        gosu \
        graphviz \
        iproute2 \
        iputils-ping \
        latexmk \
        less \
        libgdal-dev \
        libgraphviz-dev \
        make \
        nano \
        pkg-config && \
        postgresql-client-12 \
        python3-dev \
        redis-tools \
        tex-gyre \
        texlive-fonts-recommended \
        texlive-latex-extra \
        vim \
        xvfb \
    apt-get -y autoremove && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    rm -f /var/cache/apt/archives/*.deb

# Set up mostly static layers that don't change often
ENV PYTHONIOENCODING UTF-8
# Expose Gunicorn (8000), Luigid (8082), Jupyter (8888) and SSH (8022) ports
EXPOSE 8000 8082 8888 8022
ENTRYPOINT ["/usr/src/app/docker/app/run_django.sh"]

# On Debian Stretch, $(gdal-config --version) gives 2.1.2 and Pypi only has 2.1.0 and 2.1.3
# so we may need to strip the last part of the version number using GDAL==${VERSION%.*}
# GDAL requires numpy for some extensions to build, make sure the version here matches requirements/base.txt
RUN pip install numpy==1.21.3
RUN VERSION=$(gdal-config --version); CFLAGS=$(gdal-config --cflags) pip install GDAL==${VERSION}

# Install the Python requirements
COPY requirements /usr/src/app/requirements
ARG PIP_TRUSTED_HOST=127.0.0.1
ARG PIP_INDEX_URL=https://pypi.python.org/simple/
# Pin old pip to avoid `AttributeError: 'ParsedRequirement' object has no attribute 'req'`
# when installing badly behaved packages
RUN pip install pip==20.0.2
RUN pip install --quiet --no-cache-dir -r requirements/base.txt

# Create the user and required user-writable directories.
# These directories should be listed in .dockerignore
# - assets contains compiled staticfiles
# - cache contains locally cached objects
# - log is required for the Django logs
# - media is required for user uploaded files
# - run is required for pid files
RUN mkdir -p \
        assets \
        cache \
        log \
        media \
        run && \
    adduser --disabled-password --disabled-login --no-create-home --gecos django django && \
    chown -R django:django cache log media run

# Create volumes for writable directories inside the container. Note that absolute
# paths are required for them to still work when docker-compose.override.yml is
# mounting the working directory into /usr/src/app
VOLUME /usr/src/app/assets /usr/src/app/cache /usr/src/app/log /usr/src/app/media /usr/src/app/run

# Create a second build stage that adds the source code
# This allows the test and dev stages below to reuse the base stage
FROM base as prod
COPY . /usr/src/app

# Create a third build stage that adds the test dependencies and the source code
FROM base as test
RUN pip install --quiet --no-cache-dir -r requirements/test.txt
COPY . /usr/src/app

# Create a fourth build stage that adds the local dependencies and the source code
FROM base as dev
RUN pip install --quiet --no-cache-dir -r requirements/local.txt
COPY . /usr/src/app
