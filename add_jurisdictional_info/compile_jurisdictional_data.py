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

# Assign city, county, zip datasets to variables
rlis_cities = '//gisstore/gis/RLIS/BOUNDARY/cty_fill.shp'
oregon_cities = os.path.join(env.workspace, 'statewide_data/oregon_citylim_2010.shp')
washington_cities = os.path.join(env.workspace, 'statewide_data/washington_cities.shp')
rlis_counties = '//gisstore/gis/RLIS/BOUNDARY/co_fill.shp'
or_wa_tiger_counties = os.path.join(env.workspace, 'statewide_data/or_wa_counties_tiger13.shp')
rlis_zips = '//gisstore/gis/RLIS/BOUNDARY/zipcode.shp'
oregon_zips = os.path.join(env.workspace, 'statewide_data/ORE_zipcodes.shp')
or_wa_tiger_zips = os.path.join(env.workspace, 'statewide_data/or_wa_zip_code_tab_areas_tiger10.shp')

def renameField(fc, old_name, new_name):
	desc = arcpy.Describe(fc)
	if old_name in [field.name for field in desc.fields]:
		# As described here http://resources.arcgis.com/en/help/main/10.2/index.html#//018z0000004n000000, not all
		# values return by the field objects 'type' parameter map to inputs for arcpy, this dictionary corrects
		field_type_dict = {'Integer': 'LONG', 'String': 'TEXT', 'SmallInteger':'SHORT'}

		for field in desc.fields:
			if old_name == field.name:
				if field.type in field_type_dict:
					f_type = field_type_dict[field.type]
					break
				else:
					f_type = field.type
					break

		arcpy.management.AddField(fc, new_name, f_type)

		fields = [old_name, new_name]
		with arcpy.da.UpdateCursor(fc, fields) as cursor:
			for o_name, n_name in cursor:
				n_name = o_name
				cursor.updateRow((o_name, n_name))
		
		arcpy.management.DeleteField(fc, old_name)

	else:
		print 'The field: ' + old_name + ' does not exist in the input feature class'

or_cty_old_name = 'CITY_NAME'
or_cty_name = 'name_or_ci'
renameField(oregon_cities, or_cty_old_name, or_cty_name)

wa_cty_old_name = 'NAME'
wa_cty_name = 'name_wa_ci'
renameField(washington_cities, wa_cty_old_name, wa_cty_name)

tiger_co_old_name = 'NAME'
tiger_co_name = 'name_tg_co'
renameField(or_wa_tiger_counties, tiger_co_old_name, tiger_co_name)

# Union city and county limit data into a single layer
cty_co_union_feats = [[rlis_cities, 1], [oregon_cities, 2], [washington_cities, 3], 
						[rlis_counties, 4], [or_wa_tiger_counties, 5]]
cty_co_union = 'in_memory/cty_co_union'
arcpy.analysis.Union(cty_co_union_feats, cty_co_union)

# Clip the union layer to only cover the extent of the OSM bounding box defined above
cty_co_union_clip = 'in_memory/cty_co_union_clip'
arcpy.analysis.Clip(cty_co_union, b_box_fc, cty_co_union_clip)

# Name field is 'CITYNAME' for rlis cities and 'COUNTY' for rlis counties.  The name field for all other inputs has 
# been modified to be unique and stored in a variable above
rlis_cty_name = 'CITYNAME'
rlis_co_name = 'COUNTY'
fields = [rlis_cty_name, or_cty_name, wa_cty_name, rlis_co_name, tiger_co_name]
with arcpy.da.UpdateCursor(cty_co_union_clip, fields) as cursor:
	for final_name, or_cty, wa_cty, rlis_co, tiger_co in cursor:
		if final_name == '':
			if or_cty != '':
				final_name = or_cty
			elif wa_cty != '':
				final_name = wa_cty
			elif rlis_co != '':
				final_name = rlis_co + ' County'
			elif tiger_co != '':
				final_name = tiger_co + ' County'

			cursor.updateRow((final_name, or_cty, wa_cty, rlis_co, tiger_co))

# Change the name of the 'CITYNAME' column because it no longer holds values for just the rlis cities layer, but
# rather names for cities and counties across the whole region
region_name = 'reg_name'
renameField(cty_co_union_clip, rlis_cty_name, region_name)

city_county_final = os.path.join(env.workspace, 'data/or_wa_city_county.shp')
dissolve_field = region_name
arcpy.management.Dissolve(cty_co_union_clip, city_county_final, dissolve_field)