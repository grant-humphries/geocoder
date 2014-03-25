# Copyright: (c) Grant Humphries for TriMet, 2014
# ArcGIS Version:   10.2.1
# Python Version:   2.7.5
#--------------------------------

import os
import arcpy
from arcpy import env

# Allow shapefiles to be overwritten and set the current workspace
env.overwriteOutput = True
env.addOutputsToMap = True
env.workspace = '//gisstore/gis/PUBLIC/GIS_Projects/Geocoding/TriMet_Geocoder'

# Create a 'temp' folder to store temporary project output (if it doesn't already exist)
if not os.path.exists(os.path.join(env.workspace, 'temp')):
	os.makedirs(os.path.join(env.workspace, 'temp'))

# Create a polygon object that represents the bounding box of the OpenStreet Map export that we use here at TriMet
b_box_coords = [(44.68000, -123.80000), (44.68000, -121.50000), (45.80000, -121.50000), (45.80000, -123.80000)]

# To create a polygon objeect one must first create point objects, put them in an arcpy Array and then pass that array
# to the polygon object constructor
pt_array = arcpy.Array()
for lat, lon in b_box_coords:
	pt_array.append(arcpy.Point(lon, lat))

wgs84 = arcpy.SpatialReference(4326)
osm_b_box = arcpy.Polygon(pt_array, wgs84)

# Since the coordinates passed were in latitude and longitude the spatial reference of the bounding box is
# is WGS 84, convert it to Oregon State Plane North
oregonStatePlane = arcpy.SpatialReference(2913)
osm_b_box_state_plane = osm_b_box.projectAs(oregonStatePlane)

# Convert the B Box from a polygon object to feature class and feature layer so that it can be used as an input
# for arcpy tools
b_box_fc = 'in_memory/osm_b_box'
arcpy.management.CopyFeatures(osm_b_box_state_plane, b_box_fc)

b_box_layer = 'osm_b_box_layer'
arcpy.management.MakeFeatureLayer(b_box_fc, b_box_layer)

# Assign city, county, zip datasets to variables
rlis_cities = '//gisstore/gis/RLIS/BOUNDARY/cty_fill.shp'
oregon_cities = os.path.join(env.workspace, 'statewide_data/oregon_citylim_2010.shp')
washington_cities = os.path.join(env.workspace, 'statewide_data/washington_cities.shp')
rlis_counties = '//gisstore/gis/RLIS/BOUNDARY/co_fill.shp'
or_wa_tiger_counties = os.path.join(env.workspace, 'statewide_data/or_wa_counties_tiger13.shp')
rlis_zips = '//gisstore/gis/RLIS/BOUNDARY/zipcode.shp'
oregon_zips = os.path.join(env.workspace, 'statewide_data/ORE_zipcodes.shp')
or_wa_tiger_zips = os.path.join(env.workspace, 'statewide_data/or_wa_zip_code_tab_areas_tiger10.shp')

def trimAndReproject(dataset, name):
	# Check to see if the input dataset is in the Oregon State Plane North Projection, if it is not reproject it
	# to that spatial reference
	desc = arcpy.Describe(dataset)
	if desc.spatialReference.factoryCode != 2913:
		spatial_ref = arcpy.SpatialReference(2913)
		dataset_2913 = os.path.join(env.workspace, 'data/temp/' + name + '_2913.shp')
		arcpy.management.Project(dataset, dataset_2913, spatial_ref)
		dataset = dataset_2913

	# Get rid of any features that aren't within the OSM bounding box defined above
	dataset_layer = name + '_layer'
	arcpy.management.MakeFeatureLayer(dataset, dataset_layer)

	spatial_relationship = 'INTERSECT'
	st = 'NEW_SELECTION'
	arcpy.management.SelectLayerByLocation(dataset_layer, spatial_relationship, b_box_layer, selection_type=st)

	b_box_feats = 'in_memory/' + name + '_b_box_feats'
	arcpy.management.CopyFeatures(dataset_layer, b_box_feats)

	# Delete in memory layers that are no longer needed, note that first feature class will only exist if 
	# the input dataset was not in Oregon State Plane North projection
	#arcpy.management.DeleteFeatures(dataset_layer)

	return b_box_feats

# Cities/Counties layer
rlis_cities_trim = trimAndReproject(rlis_cities, 'rlis_cities')
or_cities_trim = trimAndReproject(oregon_cities, 'or_cities')
wa_cities_trim = trimAndReproject(washington_cities, 'wa_cities')

# Create a new feature class to hold the merged cities layers
or_wa_cities = os.path.join(env.workspace, 'data/or_wa_cities.shp')
geom_type = 'POLYGON'
projection = arcpy.SpatialReference(2913)
arcpy.management.CreateFeatureclass(os.path.dirname(or_wa_cities), os.path.basename(or_wa_cities), geom_type, 
										spatial_reference=projection)

f_name = 'Name'
f_type = 'TEXT'
arcpy.management.AddField(or_wa_cities, f_name, f_type)

drop_field = 'Id'
arcpy.management.DeleteField(or_wa_cities, drop_field)

i_fields = ['SHAPE@', 'Name'] 
i_cursor = arcpy.da.InsertCursor(or_wa_cities, i_fields)

# First insert rlis cities, this is the most accurate and up-to-date of the three datasets that contains cities
cities_list = []
fields = ['SHAPE@', 'CITYNAME']
with arcpy.da.SearchCursor(rlis_cities_trim, fields) as cursor:
	for geom, name in cursor:
		i_cursor.insertRow((geom, name))
		cities_list.append(name)

fields = ['SHAPE@', 'CITY_NAME']
with arcpy.da.SearchCursor(or_cities_trim, fields) as cursor:
	for geom, name in cursor:
		if name not in cities_list:
			i_cursor.insertRow((geom, name))
			cities_list.append(name)

fields = ['SHAPE@', 'NAME']
with arcpy.da.SearchCursor(wa_cities_trim, fields) as cursor:
	for geom, name in cursor:
		if name not in cities_list:
			i_cursor.insertRow((geom, name))

del i_cursor