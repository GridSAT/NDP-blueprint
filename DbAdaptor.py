import time
import psycopg2
from configs import *
import hashlib
from psycopg2 import sql

# helpful query: select id, cid1 is null as cid1_is_null, cid2 is null as cid2_is_null from cnf_1560847944_097688;

class DbAdapter:

    conn_string = "host={} port={} dbname={} user={} password={}".format(DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)

    def create_table(self, table_name):
        """ create tables in the PostgreSQL database"""
        command = """
                CREATE TABLE {0} (
                id BYTEA PRIMARY KEY,
                body TEXT,
                cid1 BYTEA,
                cid2 BYTEA,
                mapping INTEGER[],
                count INTEGER DEFAULT 1
            )
            """.format(table_name)
        conn = None
        try:
            # connect to the PostgreSQL server
            conn = psycopg2.connect(self.conn_string)
            cur = conn.cursor()
            # create table 
            cur.execute(command)
            # close communication with the PostgreSQL database server
            cur.close()
            # commit the changes
            conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error("DB Error: " + str(error))
        finally:
            if conn is not None:
                conn.close()
 
 
    def insert_row(self, table_name, value):

        """ insert a new vendor into the vendors table """
        conn = None
        success = False
        try:
            # connect to the PostgreSQL database
            conn = psycopg2.connect(self.conn_string)
            # create a new cursor
            cur = conn.cursor()
            # execute the INSERT statement
            #cur.execute(sql.SQL("insert into {} values (%s, %s)").format(sql.Identifier('my_table')), [10, 20])
            cur.execute(sql.SQL("INSERT INTO {0}(id, cid1, cid2) VALUES(%s, %s, %s)").format(sql.Identifier(table_name)), (value, None, None ))
            # commit the changes to the database
            conn.commit()
            # close communication with the database
            cur.close()
            success = True
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error("DB Error: " + str(error))
            success = False
        finally:
            if conn is not None:
                conn.close()
    
        return success

    def does_exist(self, table_name, value):

        conn = None
        result = False
        try:
            conn = psycopg2.connect(self.conn_string)
            cur = conn.cursor()
            cur.execute(sql.SQL("SELECT 1 FROM {0} WHERE id = %s LIMIT 1").format(sql.Identifier(table_name)), (value, ))
            result = bool(cur.rowcount)
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error("DB Error: " + str(error))
            result = False
        finally:
            if conn is not None:
                conn.close()

        return result


    def update_count(self, table_name, value):
        conn = None
        result = False
        try:
            conn = psycopg2.connect(self.conn_string)
            cur = conn.cursor()
            cur.execute(sql.SQL("UPDATE {0} SET count = count + 1 WHERE id = %s").format(sql.Identifier(table_name)), (value, ))
            # commit the changes to the database
            conn.commit()
            # get result
            result = bool(cur.rowcount)
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error("DB Error: " + str(error))
            result = False
        finally:
            if conn is not None:
                conn.close()

        return result


if __name__ == '__main__':
    db = DbAdapter()
    table_name = "cnf_{}".format(str(time.time()).replace(".", "_"))
    print("table: " + table_name)
    db.create_table(table_name)
    # insert
    x = hashlib.sha1(bytes("hello", "ascii")).digest()
    db.insert_row(table_name, x)
    # check existence
    if db.does_exist(table_name, x):
        print("yes, exists")
    else:
        print("doesn't exist")

    db.update_count(table_name, x)
    