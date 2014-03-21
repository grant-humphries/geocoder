###Project Summary

This repo presently contains scripts that run on an Osmosis export of OpenStreetMap data and generate cross street points that are 
used as an input for a SOLR based geocoder.  City, county and zip code information are added to each points based on RLIS data and open data sets from the States of Oregon and Washington as well as from the Census Bureau's TIGER data.  For more information on those sources see `add_jurisdictional_info/data_sources.md`.  At some point this repo may expand to contain the entire SOLR geocoder (thus the name).