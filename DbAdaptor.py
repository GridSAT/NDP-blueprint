import time
import psycopg2
from configs import *
import hashlib
from psycopg2 import sql

# helpful query: select id, cid1 is null as cid1_is_null, cid2 is null as cid2_is_null from cnf_1560847944_097688;

class DbAdapter:


    def __init__(self):
        self.conn_string = "host={} port={} dbname={} user={} password={}".format(DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)
        self.conn = None
        self.cur = None
        
        try:
            # connect to the PostgreSQL server
            self.conn = psycopg2.connect(self.conn_string)
            self.cur = self.conn.cursor()
            
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error("DB Error: " + str(error))

    def __del__(self):
        try:
            # close communication with the PostgreSQL database server
            self.cur.close()
            # commit the changes
            self.conn.commit()
            # close the connection
            if self.conn is not None:
                self.conn.close()
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error("DB Error: " + str(error))

    ### GlobalSetsTable methods ###
    
    def gs_create_table(self, table_name):
        """ create tables in the PostgreSQL database"""
        table_command = """
                CREATE TABLE {0} (
                hash BYTEA PRIMARY KEY,
                body TEXT,
                cid1 BYTEA,
                cid2 BYTEA,
                mapping INTEGER[],
                count INTEGER DEFAULT 1,
                num_of_clauses INTEGER DEFAULT 0,
                num_of_vars INTEGER DEFAULT 0
            )
            """.format(table_name)

        # be aware that creating an index on table with exaustive inserts can slow it down. Check the speed without the index and compare.
        index_command1 = "CREATE INDEX num_clauses ON {0} (num_of_clauses)".format(table_name)
        index_command2 = "CREATE INDEX num_vars ON {0} (num_of_vars)".format(table_name)

        try:
            # create table 
            self.cur.execute(table_command)
            self.cur.execute(index_command1)
            self.cur.execute(index_command2)
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error("DB Error: " + str(error))
 
 
    def gs_insert_row(self, table_name, value):

        """ insert a row item into the table """
        success = False
        try:            
            # execute the INSERT statement
            #self.cur.execute(sql.SQL("insert into {} values (%s, %s)").format(sql.Identifier('my_table')), [10, 20])
            self.cur.execute(sql.SQL("INSERT INTO {0}(hash, cid1, cid2) VALUES(%s, %s, %s)").format(sql.Identifier(table_name)), (value, None, None ))
            
            success = True
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error("DB Error: " + str(error))
            success = False
    
        return success

    def gs_does_exist(self, table_name, value):
        
        result = False
        try:
            self.cur.execute(sql.SQL("SELECT 1 FROM {0} WHERE hash = %s LIMIT 1").format(sql.Identifier(table_name)), (value, ))
            result = bool(self.cur.rowcount)
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error("DB Error: " + str(error))
            result = False

        return result


    def gs_update_count(self, table_name, value):
        result = False
        try:
            self.cur.execute(sql.SQL("UPDATE {0} SET count = count + 1 WHERE hash = %s").format(sql.Identifier(table_name)), (value, ))
            # get result
            result = bool(self.cur.rowcount)
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error("DB Error: " + str(error))
            result = False

        return result


    ### RunTimeQueue methods ###

    def rtq_create_table(self, table_name):
        """ create tables in the PostgreSQL database"""
        table_command = """
                CREATE TABLE {0} (
                id INTEGER PRIMARY KEY,
                body TEXT
            )
            """.format(table_name)

        try:
            # create table 
            self.cur.execute(table_command)            
            self.conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error("DB Error: " + str(error))
            return False
            
        return True
 
 
    def rtq_insert_set(self, table_name, id, body):

        """ insert a new row into the table """
        success = False
        try:            
            # execute the INSERT statement
            self.cur.execute(sql.SQL("INSERT INTO {0}(id, body) VALUES(%s, %s)").format(sql.Identifier(table_name)), (id, body))            
            success = True
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error("DB Error: " + str(error))
            success = False
    
        return success

    def rtq_get_set(self, table_name, id):
        
        result = None
        try:
            self.cur.execute(sql.SQL("SELECT id, body FROM {0} WHERE id = %s LIMIT 1").format(sql.Identifier(table_name)), (id, ))
            result = self.cur.fetchone()
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error("DB Error: " + str(error))

        return result


    def rtq_cleanup(self, table_name):
        success = False
        try:
            self.cur.execute(sql.SQL("DROP table {0}").format(sql.Identifier(table_name)))
            # get result
            success = True
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error("DB Error: " + str(error))

        return success

