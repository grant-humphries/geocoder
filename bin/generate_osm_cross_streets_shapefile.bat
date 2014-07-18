@echo off
setlocal EnableDelayedExpansion

::Set workspaces
set workspace=G:\PUBLIC\GIS_Projects\Geocoding\TriMet_Geocoder
set code_workspace=%workspace%\git\geocoder
set data_workspace=%workspace%\data

::Set postgres parameters
set pg_host=maps10.trimet.org
set db_name=trimet
set pg_user=geoserve

::Prompt the user to enter their postgres password, 'pgpassword' is a keyword and will automatically
::set the password for most postgres commands in the current session
set /p pgpassword="Enter postgres password (escape special characters using '^^'):"

::Run script that generates cross street points
echo "Generating cross street points from osmosis'd openstreetmap data"

set x_streets_script=%code_workspace%\generate-prep_xstreets\generate_cross_streets_from_osm.sql
psql -q -h %pg_host% -d %db_name% -U %pg_user% -f %x_streets_script%


::Launch python scripts that abbreviate the lengthy OSM versions of street names
echo "Street name abbreviation starting..."

::The command prompt must be in the location below for the python renamer to run properly
call G:
cd %code_workspace%\abbreviate_street_names
python rename_streets.py %pgpassword%


::Optionally run arcpy script that numerous jurisdictional datasets into two shapefiles
set /p update_jurisdictional_data="Has any of the underlying jurisdictional data been updated?  Type 'y' (no quotes) to run script that will integrate that new data, type anything else to skip it"

set jurisdiction_compilation_script=%code_workspace%\add_jurisdictional_info\compile_jurisdictional_data.py
if %update_jurisdictional_data%==y python %jurisdiction_compilation_script%

::Load the jurisdictional shapefiles into postgis
echo "Loading jurisdictional shapefiles into PostGIS..."
::Spatial reference id of the shapefiles being loaded
set srid=2913

set city_county=or_wa_city_county
shp2pgsql -s %srid% -d -I %data_workspace%\%city_county%.shp %city_county% | psql -q -h %pg_host% -U %pg_user% -d %db_name%

set zips=or_wa_zip_codes
shp2pgsql -s %srid% -d -I %data_workspace%\%zips%.shp %zips% | psql -q -h %pg_host% -U %pg_user% -d %db_name%


::Determine city/county and zip code of x-street points
echo "Assigning city/county and zip code information to cross street points"
echo "Start time is: %time:~0,8%"

set assign_loc_info_script=%code_workspace%\add_jurisdictional_info\add_cty-co-zip_to_xstreets.sql
psql -q -h %pg_host% -d %db_name% -U %pg_user% -f %assign_loc_info_script%

echo "Jurisdiction assigment completed at: %time:~0,8%"


::convert cross streets table into schema used by SOLR geocoder (is derived from old data provided by Metro)
echo "Converting data to SOLR compatible schema"

set conversion_script=%code_workspace%\generate-prep_xstreets\convert_xstreets_to_solr_schema.sql
psql -q -h %pg_host% -d %db_name% -U %pg_user% -f %conversion_script%

echo "Export to shapefile?  This will move the old version of the file and replace it"
echo "Press crtl + c to abort or"
pause

set export_location=G:\Data\Metro\intersection
set shp_name=intersection

::Get the last modified date from old intersections shapefile
for %%i in (%export_location%\%shp_name%.shp) do (
	rem appending '~t' in front of the variable name in a loop will return the time and date 
	rem that the file that was assigned to that variable was last modified
	set mod_date_time=%%~ti
	
	rem reformat the date such the it is in the following form YYYY_MM
	set mod_year_month=!mod_date_time:~6,4!_!mod_date_time:~0,2!
)

::Rename old file based on modification date and move it to the 'old' folder
for /f %%i in ('dir /b %export_location%\%shp_name%.*') do (
	set file_name=%%i
	set new_name=!file_name:%shp_name%=%shp_name%_osm_%mod_year_month%!
	move !export_location!\!file_name! !export_location!\old\!new_name!
)

::Export to now vacated location at which SOLR grabs the data
set export_table=cross_street_export
pgsql2shp -k -u %pg_user% -P %pgpassword% -h %pg_host% -f %export_location%\%shp_name%.shp %db_name% %export_table%