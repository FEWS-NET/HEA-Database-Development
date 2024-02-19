FROM --platform=linux/amd64 python:3.11-bookworm as base
# set up apt repositories for postgres installation
RUN curl -s https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor | tee /usr/share/keyrings/pgdg.gpg >/dev/null && \
    echo "deb [signed-by=/usr/share/keyrings/pgdg.gpg] http://apt.postgresql.org/pub/repos/apt bookworm-pgdg main" > /etc/apt/sources.list.d/pgdg.list && \
    apt-get -qq update && \
    apt-get -qq upgrade -y && \
    apt-get -qq install -y --no-install-recommends \
        python3-distutils \
        ca-certificates \
        curl \
        gdal-bin \
        gettext \
        gosu \
        iproute2 \
        iputils-ping \
        less \
        libgdal-dev \
        libgraphviz-dev \
        make \
        nano \
        pkg-config \
        postgresql-client-15 \
        python3-dev \
        vim && \
    apt-get -y autoremove && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    rm -f /var/cache/apt/archives/*.deb

# Set up mostly static layers that don't change often
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_ROOT_USER_ACTION=ignore
ENV PYTHONIOENCODING UTF-8
# Expose Gunicorn (8000), Jupyter (8888) and SSH (8022) ports
EXPOSE 8000 8888 8022
ENTRYPOINT ["/usr/src/app/docker/app/run_django.sh"]

# Update pip for faster dependency resolution.
ARG PIP_TRUSTED_HOST=127.0.0.1
ARG PIP_INDEX_URL=https://pypi.python.org/simple/
RUN pip install --quiet --no-cache-dir --upgrade pip

# Install pyGDAL based on the version of GDAL available in the OS.
# Currently, the version of GDAL in use conflicts with current setuptools,
# so pin an older version - see https://github.com/pypa/setuptools/issues/2781
RUN pip --quiet --no-cache-dir install "setuptools==69.1.0"
# GDAL requires numpy for some extensions to build, make sure the numpy version
# specified here matches requirements/base.txt
RUN VERSION=$(gdal-config --version); CFLAGS=$(gdal-config --cflags) pip install --quiet --no-cache-dir numpy==1.23.5 GDAL[numpy]==${VERSION}

# Install the Python requirements
COPY requirements /usr/src/app/requirements
RUN pip install --quiet --no-cache-dir -r /usr/src/app/requirements/base.txt

WORKDIR /usr/src/app
# Create the user and required user-writable directories.
# These directories should be listed in .dockerignore
# - assets contains compiled staticfiles
# - cache contains locally cached objects
# - jupyter contains local Jupyter/IPython files such as settings and the notebook secret
# - log is required for the Django logs
# - media is required for user uploaded files
# - run is required for pid files
RUN mkdir -p \
        assets \
        cache \
        jupyter \
        log \
        media \
        notebooks \
        run && \
    adduser --disabled-password --disabled-login --no-create-home --gecos django django && \
    chown -R django:django cache jupyter log media run notebooks

# Create volumes for writable directories inside the container. Note that absolute
# paths are required for them to still work when docker-compose.override.yml is
# mounting the working directory into /usr/src/app
VOLUME \
    /usr/src/app/assets \
    /usr/src/app/cache \
    /usr/src/app/jupyter \
    /usr/src/app/log \
    /usr/src/app/media \
    /usr/src/app/notebooks \
    /usr/src/app/run

## Create a second build stage that adds the source code
## This allows the test and dev stages below to reuse the base stage
FROM base as prod
COPY . /usr/src/app

# Create a third build stage that adds the test dependencies and the source code
FROM base as test
RUN pip install --quiet --no-cache-dir -r /usr/src/app/requirements/test.txt
COPY . /usr/src/app

# Create a fourth build stage that adds the local dependencies and the source code
FROM base as dev
RUN pip install --quiet --no-cache-dir -r /usr/src/app/requirements/local.txt
COPY . /usr/src/app
