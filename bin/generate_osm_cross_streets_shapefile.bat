@echo off
setlocal EnableDelayedExpansion

::Set workspaces
set workspace=G:\PUBLIC\GIS_Projects\Geocoding\TriMet_Geocoder
set code_workspace=%workspace%\git\geocoder
set data_workspace-%workspace%\data

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

::Launch python scripts that abbreviate the lengthy OSM versions of street names
set renamer_script=%code_workspace%\abbreviate_street_names\rename_streets.py
python %renamer_script%

::Optionally run arcpy script that numerous jurisdictional datasets into two shapefiles
set /p update_jurisdictional_data="Has any of the underlying jurisdictional data been updated?  Type 'y' (no quotes) to run script that will integrate that new data, type anything else to skip it"

set jurisdiction_compilation_script=%code_workspace%/add_jursidictional_info/compile_jurisdictional_data.py
if %update_jurisdictional_data%==y python %jurisdiction_compilation_script%

::Load the jurisdictional shapefiles into postgis
set srid=
shp2pgsql -s %srid% -d -I %data_workspace%\ | psql -q -h %pg_host% -U %pg_user% -d %db_name%