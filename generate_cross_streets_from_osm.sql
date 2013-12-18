create table as osm.cross_streets(
	X numeric,
	Y numeric,
	osm_node_id bigint,
	street_1 text,
	street_2 text
);

CREATE TEMP TABLE intersections(node_id bigint);
insert into intersections 
	select node_id from osm.way_nodes wn
	where exists (select null from osm.way_tags wt
					where k = 'name'
					and wn.way_id = wt.way_id)
	group by node_id having count(way_id) > 1;

CREATE TEMP TABLE named_ints(geom geometry, node_id bigint, name text);
insert into named_ints
	select n.geom, n.id, wt.v
		from osm.nodes n, osm.way_nodes wn, osm.way_tags wt
		where n.id in (select node_id from intersections)
			and n.id = wn.node_id
			and wn.way_id = wt.way_id
			and wt.k = 'name'
		group by n.geom, n.id, wt.v
		order by n.id, wt.v;

insert into osm.cross_streets
	select ST_X(ni1.geom), ST_Y(ni1.geom), ni1.node_id, ni1.name, ni2.name
		from named_ints ni1, named_ints ni2
		where ni1.node_id = ni2.node_id
			and ni1.name != ni2.name
		order by ni1.name, ni2.name;

drop table intersections;
drop table named_ints;