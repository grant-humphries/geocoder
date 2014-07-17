#Data Sources
for Intersection City, County, and Zip Code Attributes.  The bounding box for which coverage is needed is 44.68000, -123.80000, 45.80000, -121.50000 (in lat, lon), this area extends south past Salem and North past Vancouver.  Data sets are listed in order of percieved accuracy and features will only be utilized from sources lower in the list if they are not present in the items above.

##City Boundaries
| Source | Name (linked to metadata) | Coverage Area | Creation or Publication Date | Last Update Check |
| ---------- | ---------- | ---------- | ---------- | ---------- |
| RLIS | [City Limits (Poly)](http://rlisdiscovery.oregonmetro.gov/?action=viewDetail&layerID=123) | Portland, OR--WA Metro Area | 05/2014 | 05/2014 |
| Oregon Spatial Data Library | [Oregon City Limits and City Annexations 2010](http://spatialdata.oregonexplorer.info/geoportal/catalog/search/resource/details.page?uuid={7D53B5F0-EE51-43C4-A868-6B7EB19A3339}) | State of Oregon | 09/2010 | 07/2014 |
| Washington State Department of Transportation | [City Limits at 24K](http://www.wsdot.wa.gov/mapsdata/geodatacatalog/Maps/24K/DOT_Cartog/city.htm) | State of Washington | 06/2014 | 07/2014 |

##County Boundaries
| Source | Name (linked to metadata) | Coverage Area | Creation or Publication Date | Last Update Check |
| ---------- | ---------- | ---------- | ---------- | ---------- |
| RLIS | [County Lines (Poly)](http://rlisdiscovery.oregonmetro.gov/?action=viewDetail&layerID=155#) | Portland, OR--WA Metro Area | 05/2014 | 05/2014 |
| TIGER/Line 2013 Shapefiles* | [County and Equivalent](http://www.census.gov/cgi-bin/geo/shapefiles2013/main) | United States | 05/2013 | 07/2014 |

*The Oregon Spatial Data Library has a layer for counties for the State of Oregon, but based on the metadata that I read the Census layer is more up-to-date at this time (03/2014)

##Zip Code Area
| Source | Name (linked to metadata) | Coverage Area | Creation or Publication Date | Last Update Check |
| ---------- | ---------- | ---------- | ---------- | ---------- |
| RLIS | [Zip Codes](http://rlisdiscovery.oregonmetro.gov/?action=viewDetail&layerID=179) | Portland, OR--WA Metro Area | 05/2014 | 05/2014 |
| Oregon Spatial Data Library | [Oregon Zip Code Areas](http://spatialdata.oregonexplorer.info/geoportal/catalog/search/resource/details.page?uuid={153112D4-386B-4300-8B06-AD2EC3D84694}) | State of Oregon | 11/2004 | 07/2014 |
| TIGER/Line 2013 Shapefiles | [Zip Code Tabulation Areas](http://www.census.gov/cgi-bin/geo/shapefiles2013/main)** | United States |  05/2013 | 07/2014 |

**Zip Code Tabulation Areas are not the same as zip code areas.  ZCTA's are formulated by looking at Census Blocks and assigning the zip code most common with the Block to the unit then merging any contiguous blocks within the same zip code attribute.  For this reason this data set is only being used when no other data is available.