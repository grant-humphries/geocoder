# Copyright: (c) Grant Humphries for TriMet, 2014
# ArcGIS Version:   10.2.1
# Python Version:   2.7.5
#--------------------------------

import os
import fnmatch
import arcpy
from arcpy import env

# Allow shapefiles to be overwritten and set the current workspace
env.overwriteOutput = True
env.addOutputsToMap = True
env.workspace = '//gisstore/gis/PUBLIC/GIS_Projects/Geocoding/TriMet_Geocoder'

# Create a 'temp' folder to store temporary project output (if it doesn't already exist)
if not os.path.exists(os.path.join(env.workspace, 'temp')):
	os.makedirs(os.path.join(env.workspace, 'temp'))

# 0) Create a polygon object that represents the bounding box of the OpenStreet Map export that we use here at TriMet

# The coordinates in the dictionary below are the extent of the bounding box extract from OSM 
b_box = {'lat_min': 44.68000, 'lat_max': 45.80000, 'lon_min': -123.80000, 'lon_max': -121.50000}

# From the osm extract the entirety of a street segment that has any part of its length in that b-box is included in the
# output, thus some intersections outside that area persist. To account for the I'm expanding the box by 5% on each side
lat_span = b_box['lat_max'] - b_box['lat_min']
lon_span = b_box['lon_max'] - b_box['lon_min']

box_expansion_pct = 0.05
b_box['lat_min'] -= (box_expansion_pct * lat_span)
b_box['lat_max'] += (box_expansion_pct * lat_span)
b_box['lon_min'] -= (box_expansion_pct * lon_span)
b_box['lon_max'] += (box_expansion_pct * lon_span)

b_box_coords = [(b_box['lat_min'], b_box['lon_min']), (b_box['lat_min'], b_box['lon_max']),
					(b_box['lat_max'], b_box['lon_max']), (b_box['lat_max'], b_box['lon_min'])]

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
rlis_cities_read_only = '//gisstore/gis/RLIS/BOUNDARY/cty_fill.shp'
oregon_cities = os.path.join(env.workspace, 'statewide_data/oregon_citylim_2010.shp')
washington_cities = os.path.join(env.workspace, 'statewide_data/washington_cities.shp')
rlis_counties_read_only = '//gisstore/gis/RLIS/BOUNDARY/co_fill.shp'
or_wa_tiger_counties = os.path.join(env.workspace, 'statewide_data/or_wa_counties_tiger13.shp')

# Rename a field in a shapefile
def renameField(fc, old_name, new_name, num2str=False):
	desc = arcpy.Describe(fc)
	if old_name in [field.name for field in desc.fields]:
		# As described here http://resources.arcgis.com/en/help/main/10.2/index.html#//018z0000004n000000, not all
		# values return by the field objects 'type' parameter map to inputs for arcpy, this dictionary corrects
		field_type_dict = {'Integer': 'LONG', 'String': 'TEXT', 'SmallInteger':'SHORT'}

		if num2str == False:
			for field in desc.fields:
				if old_name == field.name:
					if field.type in field_type_dict:
						f_type = field_type_dict[field.type]
						break
					else:
						f_type = field.type
						break
		else:
			f_type = 'TEXT'

		arcpy.management.AddField(fc, new_name, f_type)

		fields = [old_name, new_name]
		with arcpy.da.UpdateCursor(fc, fields) as cursor:
			for o_name, n_name in cursor:
				n_name = o_name
				
				if num2str == True:
					n_name = str(int(n_name))

				cursor.updateRow((o_name, n_name))
		
		arcpy.management.DeleteField(fc, old_name)

	else:
		print 'renameField Error:'
		print 'The field: ' + old_name + ' does not exist in the input feature class'

# 1) Merge city and county data into a single layer

# Assign city and county datasets to variables
rlis_cities_read_only = '//gisstore/gis/RLIS/BOUNDARY/cty_fill.shp'
oregon_cities = os.path.join(env.workspace, 'statewide_data/oregon_citylim_2010.shp')
washington_cities = os.path.join(env.workspace, 'statewide_data/washington_cities.shp')
rlis_counties_read_only = '//gisstore/gis/RLIS/BOUNDARY/co_fill.shp'
or_wa_tiger_counties = os.path.join(env.workspace, 'statewide_data/or_wa_counties_tiger13.shp')

# rlis data is read only and needs to be modified thus the copies that are created below
rlis_cities = 'in_memory/rlis_cities'
arcpy.management.CopyFeatures(rlis_cities_read_only, rlis_cities)

rlis_counties = 'in_memory/rlis_counties'
arcpy.management.CopyFeatures(rlis_counties_read_only, rlis_counties)

# Rename 'name' fields on input datasets so that they are unique amongst each other easily identifiable
rename_list = [(rlis_cities, 'CITYNAME', 'rlis_city'), 
				(oregon_cities, 'CITY_NAME', 'or_city'),
				(washington_cities, 'NAME', 'wa_city'), 
				(rlis_counties, 'COUNTY', 'rlis_cnty'),
				(or_wa_tiger_counties, 'NAME','tiger_cnty')]

name_fields = []
for fc, old_name, new_name in rename_list:
	renameField(fc, old_name, new_name)
	name_fields.append(new_name)

# Union city and county limit data into a single layer
cty_co_union_feats = [[rlis_cities, 1], [oregon_cities, 2], [washington_cities, 3], 
						[rlis_counties, 4], [or_wa_tiger_counties, 5]]
cty_co_union = 'in_memory/cty_co_union'
arcpy.analysis.Union(cty_co_union_feats, cty_co_union)

# Clip the union layer to only cover the extent of the OSM bounding box defined above
cty_co_union_clip = 'in_memory/cty_co_union_clip'
arcpy.analysis.Clip(cty_co_union, b_box_fc, cty_co_union_clip)

# Add a new field to store the final name that will be used for each of the features in the union dataset
region_name = 'reg_name'
f_type = 'TEXT'
arcpy.management.AddField(cty_co_union_clip, region_name, f_type)

# Using the established heirarchy amongst the datasets consolidate all of the city/county names into a single field
fields = [region_name] + name_fields
with arcpy.da.UpdateCursor(cty_co_union_clip, fields) as cursor:
	for final_name, rlis_cty, or_cty, wa_cty, rlis_co, tiger_co in cursor:
		if rlis_cty != '':
			final_name = rlis_cty
		elif or_cty != '':
			final_name = or_cty
		elif wa_cty != '':
			final_name = wa_cty
		elif rlis_co != '':
			final_name = rlis_co + ' County'
		elif tiger_co != '':
			final_name = tiger_co + ' County'

		cursor.updateRow((final_name, rlis_cty, or_cty, wa_cty, rlis_co, tiger_co))

# Dissolve city/county boundaries based on the unified 'reg_name' field
city_county_final = os.path.join(env.workspace, 'data/or_wa_city_county.shp')
dissolve_field = region_name
arcpy.management.Dissolve(cty_co_union_clip, city_county_final, dissolve_field)


# 2) Merge zip codes datasets into a single layer

# Assign zip code datasets to variables
rlis_zips_read_only = '//gisstore/gis/RLIS/BOUNDARY/zipcode.shp'
oregon_zips = os.path.join(env.workspace, 'statewide_data/ORE_zipcodes.shp')
or_wa_tiger_zips = os.path.join(env.workspace, 'statewide_data/or_wa_zip_code_tab_areas_tiger10.shp')

# rlis zips is read only and needs to be modified thus the copy
rlis_zips = 'in_memory/rlis_zips'
arcpy.management.CopyFeatures(rlis_zips_read_only, rlis_zips)

# Rename 'name' fields on input datasets so that they are unique amongst each other
# the rlis zip field is of type int while all other zip data has their corresponding fields as string
# I'm converting the rlis zip field to string here for compatibility
rlis_zip_old_field = 'ZIPCODE'
rlis_zip_field = 'rlis_zip'
covert_to_string = True
renameField(rlis_zips, rlis_zip_old_field, rlis_zip_field, True)

or_zip_old_field = 'ZIP'
or_zip_field = 'or_zip'
renameField(oregon_zips, or_zip_old_field, or_zip_field)

tiger_zip_old_field = 'ZCTA5CE10'
tiger_zip_field = 'tiger_zip'
renameField(or_wa_tiger_zips, tiger_zip_old_field, tiger_zip_field)

# Union the zip code layers
zip_union_feats = [[rlis_zips, 1], [oregon_zips, 2], [or_wa_tiger_zips, 3]]
zip_union = 'in_memory/zip_union'
arcpy.analysis.Union(zip_union_feats, zip_union)

# Clip the union layer to only cover the extent of the OSM bounding box defined above
zip_union_clip = 'in_memory/zip_union_clip'
arcpy.analysis.Clip(zip_union, b_box_fc, zip_union_clip)

# Add field to store final zip code of for unioned regions
final_zip_field = 'zip_code'
f_type = 'TEXT'
arcpy.management.AddField(zip_union_clip, final_zip_field, f_type)

# Using the established heirarchy amongst the datasets consolidate all of the zip code value into a single field
fields = [final_zip_field, rlis_zip_field, or_zip_field, tiger_zip_field]
with arcpy.da.UpdateCursor(zip_union_clip, fields) as cursor:
	for final_zip, rlis_zip, or_zip, tiger_zip in cursor:
		if rlis_zip != '':
			final_zip = rlis_zip
		# In the State of Oregon zip code file there are some zips that don't begin with a '9', these seem
		# to be invalid and are being excluded
		elif or_zip != '' and fnmatch.fnmatch(or_zip, '9*'):
			final_zip = or_zip
		elif tiger_zip != '':
			final_zip = tiger_zip

		cursor.updateRow((final_zip, rlis_zip, or_zip, tiger_zip))

# Dissolve zip code boundaries based on the unified 'zip' field
zip_final = os.path.join(env.workspace, 'data/or_wa_zip_codes.shp')
dissolve_field = final_zip_field
arcpy.management.Dissolve(zip_union_clip, zip_final, dissolve_field)