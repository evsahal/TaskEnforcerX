import json
import sqlite3
from datetime import datetime, timedelta
from sqlite3 import Error


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)
        return False
    return conn


def execute_query(conn, query, values):
    # with conn: for auto commit
    try:
        c = conn.cursor()
        c.execute(query, values)
    except Error as e:
        print(e)
        return False
    return c


def execute_query_no_param(conn, query):
    # with conn: for auto commit
    try:
        c = conn.cursor()
        c.execute(query)
    except Error as e:
        print(e)
        return False
    return c


def select_query_no_param(conn, query):
    try:
        c = conn.cursor()
        c.execute(query)
        return c
    except Error as e:
        print(e)
        return False


def select_query(conn, query, condition):
    try:
        c = conn.cursor()
        c.execute(query, condition)
        return c
    except Error as e:
        print(e)
        return False


conn = create_connection("../../main.db")
conn.execute("PRAGMA foreign_keys = ON")

add_collective_query = """insert into collective(type,boss_monster_id,normal_monster_id,scoutables_id,coordinates,
show_scan,expires_at) values(:type,:b_id,:m_id,:s_id,:cords, :show_scan, :expires_at)"""

# check_collective_item = """select collective.id from collective where collective.type = :type and
# collective.coordinates = :cords and collective.boss_monster_id = :b_id and collective.normal_monster_id = :m_id
# and collective.scoutables_id = :s_id"""

check_collective_item = """select collective.id from collective where collective.coordinates = :cords and 
collective.boss_monster_id = :b_id"""

# values = {'type': 'boss', 'b_id': 25, 'm_id': None, 's_id': None, 'cords': json.dumps({'x': 123, 'y': 345}),
#           'show_scan': True, 'expires_at': datetime.now() + timedelta(hours=8)}
#
# execute_query(conn, add_collective_query, values)
values = {'cords': json.dumps({'x': 123, 'y': 345}), 'b_id': 25}
print(select_query(conn, check_collective_item, values).fetchone())

# conn.commit()
