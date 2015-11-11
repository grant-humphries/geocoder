--Grant Humphries, 2014
--PostGIS Version: 2.1
--PostGreSQL Version: 9.3
---------------------------------

--add spatial index on cross streets geometry column
drop index if exists osm.cross_streets_gix cascade;
create index cross_streets_gix on osm.cross_streets using GIST(geom);

cluster osm.cross_streets using cross_streets_gix;
vacuum analyze osm.cross_streets;

--Assign each address point to a city or county using and aggregated layer that was created in previous
--steps of this project
alter table osm.cross_streets drop column if exists region cascade;
alter table osm.cross_streets add region text;

cluster or_wa_city_county using or_wa_city_county_geom_gist;
analyze or_wa_city_county;

update osm.cross_streets as cs
	set region = coalesce(reg.reg_name, '')
		from or_wa_city_county reg
		where ST_Within(cs.geom, reg.geom);

--Assign each address point a zip code based on an aggregated zip code layer
alter table osm.cross_streets drop column if exists zip_code cascade;
alter table osm.cross_streets add zip_code text;

cluster or_wa_zip_codes using or_wa_zip_codes_geom_gist;
analyze or_wa_zip_codes;

update osm.cross_streets as cs
	set zip_code = coalesce(zc.zip_code, '')
		from or_wa_zip_codes zc
		where ST_Within(cs.geom, zc.geom);

--ran in 777,986 ms (~13 minutes) on 3/26/14