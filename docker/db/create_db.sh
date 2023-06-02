#!/bin/sh
psql --set=CLIENT=$CLIENT --set=APP=$APP --set=ENV=$ENV --set=POSTGRES_PASSWORD=$POSTGRES_PASSWORD --set=CREATE_TEMPLATE=${CREATE_TEMPLATE:-false} -d postgres << EOF

\set DATABASE :CLIENT :APP :ENV
\set OWNER :CLIENT :APP :ENV
\set SCHEMA :APP '_owner'
\set REPORTER :APP '_reporter'
\set TEMPLATE 'template_' :APP

-- Create postgis_users role
CREATE ROLE postgis_users NOLOGIN NOCREATEDB NOCREATEROLE NOSUPERUSER;

-- Create application reporter role
CREATE ROLE :REPORTER NOLOGIN NOCREATEDB NOCREATEROLE NOSUPERUSER;

-- Create application owner user
CREATE ROLE :OWNER PASSWORD :'POSTGRES_PASSWORD' NOLOGIN CREATEDB NOCREATEROLE NOSUPERUSER;

-- Grant postgis_users to the application user
GRANT postgis_users to :OWNER;

-- Create the application database
CREATE DATABASE :DATABASE encoding 'utf8' CONNECTION LIMIT 0;
REVOKE ALL ON DATABASE :DATABASE FROM public;
GRANT CONNECT, TEMPORARY, CREATE ON DATABASE :DATABASE TO :OWNER;

-- Configure the application database
\connect :DATABASE
CREATE EXTENSION hstore;  -- Required for audit migrations to run even though no longer used
CREATE EXTENSION postgis;
CREATE EXTENSION postgis_raster;
ALTER DATABASE :DATABASE SET postgis.gdal_enabled_drivers TO 'GTiff';
ALTER DATABASE :DATABASE SET postgis.enable_outdb_rasters = true;
REVOKE ALL ON SCHEMA public FROM public;
GRANT USAGE ON SCHEMA public TO public;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE public.geometry_columns TO postgis_users;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE public.spatial_ref_sys TO postgis_users;
GRANT SELECT ON public.geography_columns TO postgis_users;
CREATE SCHEMA :SCHEMA;
ALTER SCHEMA :SCHEMA OWNER TO :OWNER;
GRANT USAGE ON SCHEMA public TO :REPORTER;
GRANT USAGE ON SCHEMA :SCHEMA TO :REPORTER;
ALTER DEFAULT PRIVILEGES IN SCHEMA :SCHEMA
  GRANT SELECT ON TABLES TO :REPORTER;
ALTER DEFAULT PRIVILEGES REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA PUBLIC FROM PUBLIC;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA PUBLIC TO postgis_users;
\connect postgres

-- Configure the database search path
ALTER DATABASE :DATABASE SET search_path=:SCHEMA,audit,public,pg_temp;

-- In development and test environments, we can't set the database search path
-- on databases created by "./manage.py test" before migrations are run, and we can't
-- set it in the template database, so make sure the application user is using
-- the same search path
ALTER USER :OWNER SET search_path=:SCHEMA,audit,public,pg_temp;

-- Make sure the database application owner can create new schemas
ALTER DATABASE :DATABASE OWNER TO :OWNER;

-- FDW requires a second user and a second schema for use by the Mayan application
\set APP myn
\set SCHEMA 'mayan'
\connect :DATABASE
CREATE SCHEMA :SCHEMA;
GRANT USAGE ON SCHEMA :SCHEMA TO :REPORTER;
ALTER DEFAULT PRIVILEGES IN SCHEMA :SCHEMA
  GRANT SELECT ON TABLES TO :REPORTER;
GRANT USAGE ON SCHEMA :SCHEMA TO :OWNER;
ALTER DEFAULT PRIVILEGES IN SCHEMA :SCHEMA
  GRANT SELECT ON TABLES TO :OWNER;

\set MAYAN :CLIENT :APP :ENV
CREATE ROLE :MAYAN PASSWORD :'POSTGRES_PASSWORD' LOGIN CREATEDB NOCREATEROLE NOSUPERUSER;
GRANT :MAYAN TO :OWNER;
GRANT CONNECT ON DATABASE :DATABASE TO :MAYAN;
GRANT CREATE ON DATABASE :DATABASE TO :MAYAN;
ALTER SCHEMA :SCHEMA OWNER TO :MAYAN;
ALTER USER :MAYAN SET search_path=:SCHEMA,public,pg_temp;
\connect postgres

-- FDW requires a third user and a third schema for use by the Luigi scheduler
\set APP klg
\set SCHEMA :APP '_owner'
\connect :DATABASE
CREATE SCHEMA :SCHEMA;
GRANT USAGE ON SCHEMA :SCHEMA TO :REPORTER;
ALTER DEFAULT PRIVILEGES IN SCHEMA :SCHEMA
  GRANT SELECT ON TABLES TO :REPORTER;
GRANT USAGE ON SCHEMA :SCHEMA TO :OWNER;
ALTER DEFAULT PRIVILEGES IN SCHEMA :SCHEMA
  GRANT SELECT ON TABLES TO :OWNER;

\set KILUIGI :CLIENT :APP :ENV
CREATE ROLE :KILUIGI PASSWORD :'POSTGRES_PASSWORD' LOGIN CREATEDB NOCREATEROLE NOSUPERUSER;
GRANT :KILUIGI TO :OWNER;
GRANT CONNECT ON DATABASE :DATABASE TO :KILUIGI;
GRANT CREATE ON DATABASE :DATABASE TO :KILUIGI;
ALTER SCHEMA :SCHEMA OWNER TO :KILUIGI;
ALTER USER :KILUIGI SET search_path=:SCHEMA,public,pg_temp;
\connect postgres

-- Create Template Database used for running tests
\if :CREATE_TEMPLATE
  CREATE DATABASE :TEMPLATE template :DATABASE encoding 'utf8';

  -- Mark the template database as a template
  UPDATE pg_database SET datistemplate = true, datallowconn = false WHERE datname = :'TEMPLATE';
\endif

-- Enable connections to the database
ALTER DATABASE :DATABASE WITH CONNECTION LIMIT 100;
ALTER ROLE :OWNER WITH LOGIN;
EOF
