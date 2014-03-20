# Copyright 2011, TriMet
#
# Licensed under the GNU Lesser General Public License 3.0 or any
# later version. See lgpl-3.0.txt for details.
#
import psycopg2
import os
import sys
import time

from osm_abbr_parser import OsmAbbrParser
import pgdb

MAX=999999999999
#MAX=20

class RenameStreets():
    """ Fixup the street labels from various osm streets table(s) in a pgsql database
    """
    def __init__(self, osm_table=('cross_streets'), schema=pgdb.dbschema, debug=True):
        self.debug = debug
        parser = OsmAbbrParser()
        
        table = schema + "." + osm_table
        self.add_columns(pgdb.getConnection(), table)
        self.rename_streets(pgdb.getConnection(), table, parser)


    def rename_streets(self, conn, table, parser):
        """ query the database table for osm_name entries, then update the given column with a parsed set of name, prefix, suffix, type, etc...
        """
        cursor = conn.cursor()
        try:
            # step 1a - add an index to the oid column of the table to improve performance (delete it if it already exists)
            schema = table.split('.')[0]
            base_table = table.split('.')[1]
            oid_index = base_table + '_oid_idx'
            
            q = "DROP INDEX IF EXISTS " + schema + '.' + oid_index + " CASCADE"
            cursor.execute(q)

            q = "CREATE INDEX " + oid_index + " ON " + table + " USING BTREE (oid)"
            cursor.execute(q)

            conn.commit()

            # step 1b - query database for osm_names/unique row id 
            q = "SELECT street_1, street_2, oid FROM " + table
            #q += " where osm_name like '%Tom\\'s%' " # for testing minimal set of row updates
            if self.debug:
                print q
            cursor.execute(q)

            # step 2a - iterate each row in the database
            c = cursor.rowcount
            k = 0
            rows = cursor.fetchall()
            for rec in rows:
                k += 1
                if k > c or k > MAX:
                    break         # something strange happened, let's get out of here

                street_names = ((rec[0], 's1_'), (rec[1], 's2_'))
                oid = rec[2]
                for name, col_prefix in street_names:
                    if name:
                        try:
                            # step 2b - parse the osm_name into its descrete parts
                            data = parser.dict(name)

                            # step 2c - update the given database row 
                            sql  = pgdb.sql_update_str(table, data, col_prefix)
                            sql += " WHERE oid=%s"%oid
                            cursor.execute(sql)

                        except Exception, e:
                            print "PARSE EXCEPTION: %s: %s" % (e.__class__.__name__, e)
                            print name, "\n", oid, "\n", data, "\n", sql, "\n\n"

                # step 2d - commit things every so often (and write a tic mark to show things still running)
                if k % 5000 == 0:
                    conn.commit()
                    if self.debug:
                        knum = " {0} of {1} ".format(k, c)
                        sys.stdout.write(knum)

                elif self.debug and k % 100 == 0:
                    sys.stdout.write('.')
                    sys.stdout.flush()                   

                            
        except Exception, e:
            print "SQL EXCEPTION: %s: %s" % (e.__class__.__name__, e)

        # step 3 - cleanup
        conn.commit()
        cursor.close()
        if self.debug:
            print "\nfinished table", table, "\n"


    def add_columns(self, conn, table):
        ''' renames name col in the street tables, and then adds new columns for RLIS like name attributes
            - rename name to osm_name = Southeast Lambert Street
            - name = Lambert
            - prefix = SE
            - suffix = ''
            - type = St
            - label = BOOLEAN
            - label_text = SE Lambert St
        '''
        cursor = conn.cursor()

        # step 1: create a tuple with all new column names
        new_cols = ('s1_name', 's1_prefix', 's1_suffix', 's1_type', 's1_label_text', 's1_label',
                        's2_name', 's2_prefix', 's2_suffix', 's2_type', 's2_label_text', 's2_label')

        # step 2: delete these columns if they already exsit
        for c in new_cols:
            q = "ALTER TABLE " + table + " DROP COLUMN IF EXISTS " + c + " CASCADE"
            cursor.execute(q)

        # step 3: add the columns to the cross streets table
        for c in new_cols:
            if c in ('s1_label', 's2_label'):
                col_type = 'BOOLEAN'
            else:
                col_type = 'TEXT'

            q = "ALTER TABLE " + table + " ADD " + c + " " + col_type
            cursor.execute(q)

        # step 4: commit
        conn.commit()
        cursor.close()

def main():
    if len(sys.argv) > 1:
        RenameStreets(('_line', '_roads'), 'osm')
    else:
        RenameStreets()


if __name__ == '__main__':
    start_seconds = time.time()
    start_time = time.localtime()
    print time.strftime('begin time: %H:%M:%S', start_time)

    main()

    end_time = time.localtime()
    print time.strftime('end time: %H:%M:%S', end_time)
    process_time = time.time() - start_seconds
    print 'processing time: %.0f seconds' %(process_time)
