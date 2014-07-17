#Data Sources
for Intersection City, County, and Zip Code Attributes.  The bounding box for which coverage is needed is 44.68000, -123.80000, 45.80000, -121.50000 (in lat, lon), this area extends south past Salem and North past Vancouver.  Data sets are listed in order of percieved accuracy and features will only be utilized from sources lower in the list if they are not present in the items above.

##City Boundaries
| Source | Name (linked to metadata) | Coverage Area |
| ---------- | ---------- | ---------- | 
| RLIS | [City Limits (Poly)](http://rlisdiscovery.oregonmetro.gov/?action=viewDetail&layerID=123) | Portland, OR--WA Metro Area |
| Oregon Spatial Data Library | [Oregon City Limits and City Annexations 2010](http://spatialdata.oregonexplorer.info/geoportal/catalog/search/resource/details.page?uuid={7D53B5F0-EE51-43C4-A868-6B7EB19A3339}) | State of Oregon |
| Washington State Department of Transportation | [City Limits at 24K](http://www.wsdot.wa.gov/Mapsdata/GeoDataCatalog/Maps/24k/DOT_Cartog/cityjpg.htm) | State of Washington |

##County Boundaries
| Source | Name (linked to metadata) | Coverage Area |
| ---------- | ---------- | ---------- | 
| RLIS | [County Lines (Poly)](http://rlisdiscovery.oregonmetro.gov/?action=viewDetail&layerID=155#) | Portland, OR--WA Metro Area |
| TIGER/Line 2013 Shapefiles* | [County and Equivalent](http://www.census.gov/cgi-bin/geo/shapefiles2013/main) | States of Oregon and Washington |

*The Oregon Spatial Data Library has a layer for counties for the State of Oregon, but based on the metadata that I read the Census layer is more up-to-date at this time (03/2014)

##Zip Code Area
| Source | Name (linked to metadata) | Coverage Area |
| ---------- | ---------- | ---------- | 
| RLIS | [Zip Codes](http://rlisdiscovery.oregonmetro.gov/?action=viewDetail&layerID=179) | Portland, OR--WA Metro Area |
| Oregon Spatial Data Library | [Oregon Zip Code Areas](http://spatialdata.oregonexplorer.info/geoportal/catalog/search/resource/details.page?uuid={153112D4-386B-4300-8B06-AD2EC3D84694}) | State of Oregon |
| TIGER/Line 2013 Shapefiles | [Zip Code Tabulation Areas](http://www.census.gov/cgi-bin/geo/shapefiles2013/main)** | State of Washington |

**Zip Code Tabulation Areas are not the same as zip code areas.  ZCTA's are formulated by looking at Census Blocks and assigning the zip code most common with the Block to the unit then merging any contiguous blocks within the same zip code attribute.  For this reason this data set is only being used when no other data is available.