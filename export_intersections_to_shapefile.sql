drop table if exists cross_street_export cascade;
create table cross_street_export with oids as
	select geom, s1_prefix as "FDPRE1", s1_name as "FDNAME1", s1_type as "FDTYPE1", 
		s1_suffix as "FDSUF1", region as "LCITY1", s2_prefix as "FDPRE2", s2_name as "FDNAME2",
		s2_type as "FDTYPE2", s2_suffix as "FDSUF2", region as "LCITY2", zip_code as "ZIPCODE",
		x::int as "X_COORD", y::int as "Y_COORD"
	--change table name to osm.cross_streets table is in osm schema rather than public
	from cross_streets;

alter table cross_street_export add "INTERSECTI" serial;

/**
To export to shapefile first set tmpublic as the owner of the table with the psql console in pgAdmin
when logged into maps2 as geoserve with the following command:
ALTER TABLE cross_street_export OWNER TO tmpublic;

Then in the command prompt use the following command
pgsql2shp -k -u tmpublic -P tmpublic -h maps2.trimet.org -f G:\PUBLIC\GIS_Projects\Geocoding\TriMet_Geocoder\cross_streets_file\intersection.shp trimet cross_street_export
the 'k' parameter preserves the case of the column names, schema only needs to be entered if different than 'public'
**/