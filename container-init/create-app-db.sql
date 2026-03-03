-- Runs once, on the first start of an empty Postgres volume.
-- Creates the role and database the Flask app connects to (see app/app.py)
-- and loads the schema into it as that role.
CREATE USER flaskapp WITH PASSWORD 'flask_app';
CREATE DATABASE aviacao WITH OWNER flaskapp ENCODING 'UTF8';

\connect aviacao flaskapp
\i /schema/aviacao.sql
