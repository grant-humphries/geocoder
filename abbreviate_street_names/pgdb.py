# Copyright 2012, OpenPlans / TriMet
# Code by Frank Purcell, OpenPlans adapted to this project by Grant Humphries
#
# Licensed under the GNU Lesser General Public License 3.0 or any
# later version. See lgpl-3.0.txt for details.
#
# Python Version: 2.7.5
# psycopg2 Version: 2.5.2
#-----------------------------------------

import psycopg2
import os

# DB connection with env_var override / default values
dbhost = 'maps2.trimet.org'
dbname = 'trimet'
dbuser = 'tmpublic'
dbpass = 'tmpublic'
dbschema = 'osm'
conn = psycopg2.connect(host=dbhost, database=dbname, user=dbuser, password=dbpass)

def getConnection():
    return psycopg2.connect(host=dbhost, database=dbname, user=dbuser, password=dbpass)


def escape_str(v):
    ret_val=v
    if isinstance(v, str) and v.find("'") >= 0:
        ret_val=v.replace("'", "\\'")
    return ret_val


def dict_2_str(dict, col_prefix='', joiner=','):
    """returns a string that looks like "key='value', key2='value2', ... "
    """
    tmplist=[]
    for k, v in dict.items():
        if isinstance(v, str) and len(v) < 1:
           continue

        if isinstance(v, (list, tuple)):
            tmp = col_prefix + str(k)+' in ('+ ','.join(map(lambda x:'\''+str(escape_str(x))+'\'',v)) +') '
        else:
            tmp = col_prefix + str(k)+'='+'\''+str(escape_str(v))+'\''
            tmplist.append(' '+tmp+' ')

    return joiner.join(tmplist)


def sql_update_str(table, dict, col_prefix=''):
    """returns a string that looks like "UPDATE table SET key='value', key2='value2', ... "
       based on this example: http://code.activestate.com/recipes/577605-auto-generate-simple-sql-statements/
    """
    sql  = ''
    sql += 'UPDATE %s '%table
    sql += ' SET %s'%dict_2_str(dict, col_prefix)
    return sql
