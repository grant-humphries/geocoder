--Grant Humphries for TriMet, 2014
--PostGIS Version: 2.1
--PostGreSQL Version: 9.3
---------------------------------

--Create a list of node id's for all nodes that are a part two or more ways that all have a tag
--with the key 'name'
create temp table named_intersections as
	select node_id 
	from osm.way_nodes wn
	where exists (select null from osm.way_tags wt
					where wn.way_id = wt.way_id
					and wt.k = 'name')
	group by node_id having count(way_id) > 1;

--Grab the node geometry for the all of the nodes in the list created above and create a distinct
--node object for each name associated with a node
create temp table intersection_points as
	select n.geom, n.id as node_id, wn.way_id, wt.v as name
	from osm.nodes n, osm.way_nodes wn, osm.way_tags wt
	where n.id in (select node_id from named_intersections)
		and n.id = wn.node_id
		and wn.way_id = wt.way_id
		and wt.k = 'name'
	group by n.geom, n.id, wn.way_id, wt.v;

--Add alternate names stored in the 'name_1' and 'alt_name' into the intersection_points table
--From the intersections table grab only node id's that are a part of a way with a 'name_1' tag
create temp table named_intersections_n1 as
	select node_id 
	from named_intersections i
	where exists (select null 
					from osm.way_nodes wn, osm.way_tags wt
					where i.node_id = wn.node_id
						and wn.way_id = wt.way_id
						and wt.k = 'name_1');

--Insert points with their 'name_1' names into the intersection_points table
insert into intersection_points
	select n.geom, n.id, wn.way_id, wt.v
	from osm.nodes n, osm.way_nodes wn, osm.way_tags wt
	where n.id in (select node_id from named_intersections_n1)
		and n.id = wn.node_id
		and wn.way_id = wt.way_id
		and wt.k = 'name_1'
	group by n.geom, n.id, wn.way_id, wt.v;

--Repeat the 'name_1' steps for 'alt_name'
create temp table named_intersections_an as
	select node_id 
	from named_intersections i
	where exists (select null 
					from osm.way_nodes wn, osm.way_tags wt
					where i.node_id = wn.node_id
						and wn.way_id = wt.way_id
						and wt.k = 'alt_name');

insert into intersection_points
	select n.geom, n.id, wn.way_id, wt.v
	from osm.nodes n, osm.way_nodes wn, osm.way_tags wt
	where n.id in (select node_id from named_intersections_an)
		and n.id = wn.node_id
		and wn.way_id = wt.way_id
		and wt.k = 'alt_name'
	group by n.geom, n.id, wn.way_id, wt.v;

create index int_points_way_id_ix on intersection_points using btree(way_id);
create index int_points_name_ix on intersection_points using btree(name);

--Join nodes, if the ways they are from don't share any common names, based on their node id to create 
--cross street pairs
drop table if exists osm.cross_streets cascade;
create table osm.cross_streets with oids as
	select ST_Transform(ip1.geom, 2913) as geom, ST_X(ST_Transform(ip1.geom, 2913)) as x, 
		ST_Y(ST_Transform(ip1.geom, 2913)) as y, ip1.node_id, ip1.name as street_1, ip2.name as street_2
	from intersection_points ip1, intersection_points ip2
	where ip1.node_id = ip2.node_id
		and ip1.name not in (select name 
							from intersection_points
							where way_id = ip2.way_id )
	group by ip1.geom, ip1.node_id, ip1.name, ip2.name
	order by ip1.name, ip2.name;

--Drop temporary tables
drop table named_intersections;
drop table named_intersections_n1;
drop table named_intersections_an;
drop table intersection_points;

--Ran in 50,466 ms on 3/17/14

--After this script runs the following command needs to be executed in order for the table to be further modified
--ALTER TABLE osm.cross_streets OWNER TO tmpublic;
--Note that the command above won't work in the psql window without the semi-colon