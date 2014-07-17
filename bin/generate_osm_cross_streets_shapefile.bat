@echo off
setlocal EnableDelayedExpansion

::Set workspace
set workspace=G:\PUBLIC\GIS_Projects\Geocoding\TriMet_Geocoder\git\geocoder

::Set postgres parameters
set pg_host=maps10.trimet.org
set db_name=trimet
set pg_user=geoserve

::Prompt the user to enter their postgres password, 'pgpassword' is a keyword and will automatically
::set the password for most postgres commands in the current session
set /p pgpassword="Enter postgres password:"

::Run script that generates cross street points
set x_streets_script=%workspace%\generate_cross_streets_from_osm.sql
psql -h %pg_host% -d %db_name% -U %pg_user% -f %x_streets_script%

