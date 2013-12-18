create temp table intersections as
	select node_id from osm.way_nodes wn
	where exists (select null from osm.way_tags wt
					where k = 'name'
					and wn.way_id = wt.way_id)
	group by node_id having count(way_id) > 1;

create temp table named_ints as
	select n.geom, n.id as node_id, wt.v as name
		from osm.nodes n, osm.way_nodes wn, osm.way_tags wt
		where n.id in (select node_id from intersections)
			and n.id = wn.node_id
			and wn.way_id = wt.way_id
			and wt.k = 'name'
		group by n.geom, n.id, wt.v
		order by n.id, wt.v;

drop table if exists osm.cross_streets cascade;
create table osm.cross_streets with oids as
	select ST_X(ni1.geom) as x, ST_Y(ni1.geom) as y, ni1.node_id, ni1.name as street_1, ni2.name as street_2
		from named_ints ni1, named_ints ni2
		where ni1.node_id = ni2.node_id
			and ni1.name != ni2.name
		order by ni1.name, ni2.name;

drop table intersections;
drop table named_ints;

-- ran in 7401 ms on 12/18/2013