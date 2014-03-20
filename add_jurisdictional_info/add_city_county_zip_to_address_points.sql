--add spatial index on cross streets geometry column
drop index if exists osm.cross_streets_geom_idx cascade;
create index cross_streets_geom_idx on osm.cross_streets using GIST(geom);

alter table osm.cross_streets drop column if exists city cascade;
alter table osm.cross_streets add city text;

update osm.cross_streets as cs
	set city = coalesce(cty.cityname, '')
		from load.city cty
		where ST_Intersects(cs.geom, cty.geom);

update osm.cross_streets as cs
	set city = coalesce('Unincorporated ' || co.county || ' County', '')
		from load.county co
		where cs.city = ''
		and ST_Intersects(cs.geom, co.geom, 4326);

alter table osm.cross_streets drop column if exists zip cascade;
alter table osm.cross_streets add zip int;

update osm.cross_streets as cs
	set zip = coalesce(zc.zipcode, null)
		from load.zip_code zc
		where ST_Intersects(cs.geom, zc.geom, 4326);