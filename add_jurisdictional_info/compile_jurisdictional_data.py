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
arcpy.management.CopyFeatures(osm_b_box_state_plane, visual_b_box)

b_box_layer = 'osm_b_box_layer'
arcpy.management.MakeFeatureLayer(b_box_fc, b_box_layer)

# Assign city, county, zip datasets to variables
rlis_cities = '//gisstore/gis/RLIS/BOUNDARY/cty_fill.shp'
oregon_cities = os.path.join(env.workspace, 'statewide_data/.shp')
washington_cities = os.path.join(env.workspace, 'statewide_data/.shp')
rlis_counties = '//gisstore/gis/RLIS/BOUNDARY/co_fill.shp'
or_wa_tiger_counties = os.path.join(env.workspace, 'statewide_data/.shp')
rlis_zips = '//gisstore/gis/RLIS/BOUNDARY/zipcode.shp'
oregon_zips = os.path.join(env.workspace, 'statewide_data/.shp')
or_wa_tiger_zips = os.path.join(env.workspace, 'statewide_data/.shp')