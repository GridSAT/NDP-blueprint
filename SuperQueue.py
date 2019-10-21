import time
import Set
from DbAdaptor import DbAdapter
from configs import PROBLEM_ID

''' Queue that uses both memory and database to hold big number of object efficiently '''
# will save ids in memory, while the objects will be saved in DB

# tip: a nice command to get the size of a table in bytes: SELECT pg_size_pretty(pg_relation_size('foo'));

class SuperQueue:

    objqueue = []   # queue of objects
    idsqueue = []   # queue of objects ids
    qhead = -1
    db = None
    table_name = None
    use_runtime_db = False

    def __init__(self, use_runtime_db=False, problem_id=PROBLEM_ID):
        self.db = DbAdapter()
        self.table_name = "queue_{}_{}".format(problem_id, str(time.time()).replace(".", ""))
        self.use_runtime_db = use_runtime_db
        if use_runtime_db:
            self.db.rtq_create_table(self.table_name)
        

    def __del__(self):        
        #drop table
        if self.use_runtime_db:
            self.db.rtq_cleanup(self.table_name)

    def insert(self, item):
               
        if self.use_runtime_db:
            self.idsqueue.append(item.id)
            self.db.rtq_insert_set(self.table_name, item.id, item.to_string(pretty=False))
        else:
            self.objqueue.append(item) 
        
        return True

    def pop(self):
        item = None
        if self.use_runtime_db:
            objid = self.idsqueue.pop(0)
            id, body = self.db.rtq_get_set(self.table_name, objid)
            item = Set.Set(body)
            item.id = id

        else:
            item = self.objqueue.pop(0)

        return item

    def is_empty(self):
        size = 0
        if self.use_runtime_db:
            size = len(self.idsqueue)
        else:
            size = len(self.objqueue)

        return not bool(size) #not bool(len(self.queue))