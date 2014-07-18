--Grant Humphries for TriMet, 2014
--PostGIS Version: 2.1
--PostGreSQL Version: 9.3
---------------------------------

drop table if exists cross_street_export cascade;
create table cross_street_export with oids as
	select geom, s1_prefix as "FDPRE1", s1_name as "FDNAME1", s1_type as "FDTYPE1", 
		s1_suffix as "FDSUF1", region as "LCITY1", s2_prefix as "FDPRE2", s2_name as "FDNAME2",
		s2_type as "FDTYPE2", s2_suffix as "FDSUF2", region as "LCITY2", zip_code as "ZIPCODE",
		x::int as "X_COORD", y::int as "Y_COORD"
	--change table name to osm.cross_streets table is in osm schema rather than public
	from osm.cross_streets;

alter table cross_street_export add "INTERSECTI" serial;