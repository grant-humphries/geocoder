--Grant Humphries for TriMet, 2014
--PostGIS Version: 2.1
--PostGreSQL Version: 9.3
---------------------------------

--Create a list of node id's for all nodes that are a part two or more ways that all have a tag
--with the key 'name'
drop table if exists named_intersections cascade;
create temp table named_intersections as
	select node_id 
	from osm.way_nodes wn
	where exists (select null from osm.way_tags wt
					where wn.way_id = wt.way_id
					and wt.k = 'name')
	group by node_id having count(way_id) > 1;

--Grab the node geometry for the all of the nodes in the list created above and create a distinct
--node object for each name associated with an intesection node
drop table if exists intersection_points cascade;
create temp table intersection_points as
	select n.geom, n.id::text as int_id, wn.way_id, wt.v as name
	from osm.nodes n, osm.way_nodes wn, osm.way_tags wt
	where n.id in (select node_id from named_intersections)
		and n.id = wn.node_id
		and wn.way_id = wt.way_id
		and wt.k = 'name'
	group by n.geom, n.id, wn.way_id, wt.v;

--Insert points with their 'name_1' names into the intersection_points table
insert into intersection_points
	select n.geom, n.id::text, wn.way_id, wt.v
	from osm.nodes n, osm.way_nodes wn, osm.way_tags wt
	where n.id in (select node_id from named_intersections)
		and n.id = wn.node_id
		and wn.way_id = wt.way_id
		and wt.k = 'name_1'
	group by n.geom, n.id, wn.way_id, wt.v;

--Insert points with their 'alt_name' names
insert into intersection_points
	select n.geom, n.id::text, wn.way_id, wt.v
	from osm.nodes n, osm.way_nodes wn, osm.way_tags wt
	where n.id in (select node_id from named_intersections)
		and n.id = wn.node_id
		and wn.way_id = wt.way_id
		and wt.k = 'alt_name'
	group by n.geom, n.id, wn.way_id, wt.v;


--Now intesections that have roundabout at the center and which don't meet at a single point
--must be added to the intersection point table

--Assemble segments that are roundabouts from deconstructed osmosis schema
drop table if exists roundabout_segs cascade;
create temp table roundabout_segs as
	select wt.way_id, 
		ST_MakeLine(array(select (select geom from osm.nodes n 
									where n.id = wn.node_id) 
							from osm.way_nodes wn 
							where wn.way_id = wt.way_id
							order by sequence_id)) as geom, v
		from osm.way_tags wt
		where k = 'junction'
			and v = 'roundabout';

--Some roundabouts are split into pieces, these are merged into a single geometry below (and
--unsplit roundabouts are inserted into this table as well)
drop table if exists merged_roundabouts cascade;
create temp table merged_roundabouts as 
	select (ST_Dump(geom)).geom as geom
	from (select ST_LineMerge(ST_Collect(geom)) as geom
			from roundabout_segs
			group by v) as collected_roundabouts;

--Find the id's of all ways that share a node with a roundabout and that have a 'name' tags and put
--them in an array in the same row as the centroid of the roundabout geometry
drop table if exists roundabout_pts cascade;
create temp table roundabout_pts with oids as
	select ST_Centroid(mr.geom) as geom, array_agg(distinct wn.way_id order by wn.way_id) as way_ids
	from osm.nodes n, osm.way_nodes wn, merged_roundabouts mr
	where ST_Contains(mr.geom, n.geom)
		and n.id = wn.node_id
		and exists (select null from osm.way_tags wt
					where wt.way_id = wn.way_id
						and wt.k = 'name')
		--this clause drops any roundabouts for which some or all of their underlying segments are
		--named.  In these cases the intersection points will be generated using the standard method
		--Ladd's circle is a prime example of this
		and not exists (select null from roundabout_segs rs, osm.way_tags wt
						where ST_Covers(mr.geom, rs.geom)
							and rs.way_id = wt.way_id
							and wt.k = 'name')
	group by mr.geom;

--Create an individual entry for each named street that adjoins a roundabout by dumping the way_id
--arrays into to individual rows.  However only do so if the arrays have two or more entries (as this
--ensures that a named cross-street pair exists at the junction) if array contains 1 or fewer entries
--discard that row
drop table if exists dumped_roundabout_pts cascade;
create temp table dumped_roundabout_pts as
	select geom, oid as roundabout_id, unnest(way_ids) as way_id
	from roundabout_pts rp
	--the second parameter in the array_length is the dimension to measure, 
	--these arrays only have one dimension
	where array_length(way_ids, 1) > 1
	order by roundabout_id, way_id;


--Now that all of the neccessay information has been gathered about the roundabout intersections insert
--the roundbout intersection points into table with all of the other standard intersection points
insert into intersection_points
	--Because there isn't a central point at which all of the streets meet at roundabout intersection
	--a 'roundabout_id' is being used where standard intersection use osm node id's.  The 'j' is being
	--appended to the roundabout_id to ensure that it is different from all osm node ids
	select rp.geom, 'j' || rp.roundabout_id::text , rp.way_id, wt.v
	from dumped_roundabout_pts rp, osm.way_tags wt
	where rp.way_id = wt.way_id
		and wt.k = 'name'
	group by rp.geom, rp.roundabout_id, rp.way_id, wt.v;

--Add secondary and tertiary names for rounabout intersections to the point table
insert into intersection_points
	select rp.geom, 'j' || rp.roundabout_id::text , rp.way_id, wt.v
	from dumped_roundabout_pts rp, osm.way_tags wt
	where rp.way_id = wt.way_id
		and wt.k = 'name_1'
	group by rp.geom, rp.roundabout_id, rp.way_id, wt.v;

insert into intersection_points
	select rp.geom, 'j' || rp.roundabout_id::text , rp.way_id, wt.v
	from dumped_roundabout_pts rp, osm.way_tags wt
	where rp.way_id = wt.way_id
		and wt.k = 'alt_name'
	group by rp.geom, rp.roundabout_id, rp.way_id, wt.v;


--Add indices to speed the join below
create index int_points_way_id_ix on intersection_points using btree(way_id);
create index int_points_name_ix on intersection_points using btree(name);

--Join intersection points, if the ways they map to don't share any common names, based on their
--intersection id to create cross street pairs
drop table if exists osm.cross_streets cascade;
create table osm.cross_streets with oids as
	select ST_Transform(ip1.geom, 2913) as geom, ST_X(ST_Transform(ip1.geom, 2913)) as x, 
		ST_Y(ST_Transform(ip1.geom, 2913)) as y, ip1.int_id, ip1.name as street_1, ip2.name as street_2
	from intersection_points ip1, intersection_points ip2
	where ip1.int_id = ip2.int_id
		and ip1.name not in (select name 
							from intersection_points
							where way_id = ip2.way_id )
	group by ip1.geom, ip1.int_id, ip1.name, ip2.name
	order by ip1.name, ip2.name;

--Drop temporary tables
drop table named_intersections cascade;
drop table roundabout_segs cascade;
drop table merged_roundabouts cascade;
drop table roundabout_pts cascade;
drop table dumped_roundabout_pts cascade;
drop table intersection_points cascade;

--Ran in 15,192 ms on 7/16/14