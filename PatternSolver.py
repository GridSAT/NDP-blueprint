import os, gc
import sys
import time, math
import psutil
import binascii
from graphviz import Digraph
from queue import Queue
from configs import *
from DbAdaptor import DbAdapter
import SuperQueue


# TODO:
# We will have two DB tables:
# * GlobalSetsTable: Which will contain all the sets we've encoutered. Each row has:
#       - set_hash
#       - set_body (string repr. of the set)
#       - child 1 id
#       - child 2 id
#       - mapping (after lo cond.)
#       - num of clauses
#       - num of vars
#
# * RunTimeQueue_{random int}: Which will contain the queue of nodes to be processed. This is an ephermal table that will be dropped at the end of execution. Each row has:
#       - set_id   // PRIMARY, a number represent the order of the set to maintain breadth first evaluation
#       - set_body (string repr. of the set)
#       

# - Upon execution, load list of hashes from GlobalSetsTable for sets of no. of clauses <= no. of clauses of root input set. This would be "nodes seen" dict,
# any new node will be add to the dict.
# - new nodes will also be added to another structure in memory called to be purged later into the database when it reach a reasonable big size 
# to batch insert operations in GlobalSetsTable


class PatternSolver:

    # the dictionary that holds processed set
    # currently each key is the string represenation of the set, i.e. set.to_string()
    setmap = {}
    args = None
    db_adaptor = None
    problem_id = None
    use_runtime_db = False
    global_table_name = GLOBAL_SETS_TABLE

    def __init__(self, args=None, problem_id=PROBLEM_ID):
        self.setmap.clear()
        self.args = args
        if problem_id:
            self.problem_id = problem_id

        if args.use_runtime_db:
            self.use_runtime_db = True

        if args.use_runtime_db or args.use_global_db:
            self.db_adaptor = DbAdapter()

        if args.mode:
            self.global_table_name = GLOBAL_SETS_TABLE_PREFIX + args.mode.lower()

    def draw_graph(self, dot, outputfile):
        fg = open(outputfile, "w")
        fg.write(dot.source)
        fg.close()

    def load_set_records(self, num_clauses):
        if self.args.use_global_db:
            hashes = self.db_adaptor.gs_load_sets(self.global_table_name, num_clauses)
            self.setmap = {el:1 for el in hashes}     
            
    def is_set_seen(self, set_hash):
        return self.setmap.get(set_hash, False)

    def update_set_seen_count(self, set_hash):
        self.setmap[set_hash] += 1

    def save_unique_node(self, set_hash):
        self.setmap[set_hash] = 1

    def save_parent_children(self, cnf_set, child1_hash, child2_hash):
        # add to global sets table
        num_of_vars = 0
        if len(cnf_set.clauses):
            num_of_vars = abs(cnf_set.clauses[-1].raw[-1])

        if self.args.use_global_db:
            return self.db_adaptor.gs_insert_row(self.global_table_name,
                                         cnf_set.get_hash(),    # set hash
                                         cnf_set.to_string(pretty=False),   # set body
                                         child1_hash,           # child 1 hash
                                         child2_hash,           # child 2 hash
                                         [],                    # mapping, to be added
                                         1,                     # occurrences                                         
                                         len(cnf_set.clauses),  # count of clauses
                                         num_of_vars)  
                                         
        return SUCCESS
        
    def process_child_node(self, child_set, dot):
        node_status = None
        nodecolor = 'black'

        # check if the set is already evaluated to boolean value            
        setbefore = child_set.to_string()
        if child_set.value != None:
            if self.args.output_graph_file:
                dot.node(binascii.hexlify(child_set.get_hash()).decode(), str(child_set.id) + "\\n" + setbefore)
            node_status = NODE_EVALUATED

        else:
            # if user input mode is MODE_LO, it means only root is LO and the rest are LOU, and since this is a child node, then pass LOU argument
            if self.args.mode == MODE_LO:                
                logger.debug("Set #{} - convert to {} mode".format(child_set.id, MODE_LOU))
                child_set.to_lo_condition(MODE_LOU)
            else:
                logger.debug("Set #{} - convert to {} mode".format(child_set.id, self.args.mode))
                child_set.to_lo_condition(self.args.mode)

            setafterhash = child_set.get_hash()

            # check if we have processed the set before
            if self.is_set_seen(setafterhash):
                self.update_set_seen_count(setafterhash)
                node_status = NODE_REDUNDANT
                if self.args.output_graph_file:
                    nodecolor = 'red'

                if self.args.output_graph_file:
                    dot.node(binascii.hexlify(child_set.get_hash()).decode(), color=nodecolor)
            
            else:                
                # when the set reaches l.o. condition, we update the global sets record
                node_status = NODE_UNIQUE
                self.save_unique_node(setafterhash)

                if self.args.output_graph_file:
                    setafter = child_set.to_string()
                    dot.node(binascii.hexlify(child_set.get_hash()).decode(), setbefore + "\\n" + setafter, color=nodecolor)

        return node_status


    def process_set(self, root_set):
        
        start_time = time.time()
        uniques = redundants = leaves = 0

        # vars to calculate graph size at the end
        id_leaves = set()   # node ids of leaf nodes
        id_pid = {}         # id to [parent ids]
        id_size = {}        # id to subgraph size

        
        # use global sets table
        if self.args.use_global_db:
            # create the table if not exist
            self.db_adaptor.gs_create_table(self.global_table_name)
            self.load_set_records(len(root_set.clauses))

        # graph drawing
        node_id = 1
        root_set.id = node_id
        graph_attr={}
        graph_attr["splines"] = "polyline"
        dot = Digraph(comment='The CNF Tree', format='svg', graph_attr=graph_attr)
        uniques += 1

        logger.debug("Set #{} - to root set to {} mode".format(root_set.id, self.args.mode))
        setbefore = root_set.to_string()
        root_set.to_lo_condition(self.args.mode)
        setafterhash = root_set.get_hash()

        # check if we have processed the CNF before
        if not self.is_set_seen(setafterhash):
            try:
                squeue = SuperQueue.SuperQueue(use_runtime_db=self.use_runtime_db, problem_id=self.problem_id)        
                squeue.insert(root_set)
            except (Exception, error) as error:
                logger.error("DB Error: " + str(error))
                return False
                
            if self.args.output_graph_file:
                setafter = root_set.to_string()
                dot.node(binascii.hexlify(root_set.get_hash()).decode(), str(root_set.id) + "\\n" + setbefore + "\\n" + setafter, color='black')

            while not squeue.is_empty():
                cnf_set = squeue.pop()
                logger.debug("Set #{0}".format(cnf_set.id))            

                # evaluate
                (s1, s2) = cnf_set.evaluate()
                
                for child in (s1, s2):
                    node_id += 1
                    child.id = node_id
                    
                    child.status = self.process_child_node(child, dot)

                    if self.args.output_graph_file:
                        dot.edge(binascii.hexlify(cnf_set.get_hash()).decode(), binascii.hexlify(child.get_hash()).decode())

                    if child.status == NODE_UNIQUE:
                        uniques += 1                        
                    elif child.status == NODE_REDUNDANT:
                        redundants += 1
                    elif child.status == NODE_EVALUATED:
                        leaves += 1

                # cnf nodes in this loop are all unique, if they weren't they wouldn't be in the queue
                # if insertion in the global table is successful, save children in the queue, 
                # otherwise, the cnf_set is already solved in the global DB table
                global_save_status = self.save_parent_children(cnf_set, s1.get_hash(), s2.get_hash())
                if global_save_status == SUCCESS:
                    for child in (s1, s2):
                        if child.status == NODE_UNIQUE:
                            squeue.insert(child)
                elif global_save_status == DB_UNIQUE_VIOLATION:
                    logger.info("Node #{} is already found 'during execution' in global DB.".format(cnf_set.id))

                # save parent id of children if not boolean
                if s1.value == None:
                    id_pid[s1.id] = cnf_set.id
                if s2.value == None:
                    id_pid[s2.id] = cnf_set.id

                # if both children are boolean, then cnf_set is a leaf node
                if s1.value != None and s2.value != None:
                    id_leaves.add(cnf_set.id)
                    id_size[cnf_set.id] = 1

                if self.args.verbos:
                    print("Nodes so far: {:,}".format(node_id), end='\r')

            
            # update the database with the graph size under each node
            #update_subgraph_sizes(id_leaves, id_pid, id_size)

        else:
            if self.args.verbos:
                print("Input set is found in the global DB")

            
        #print("\n")
        process = psutil.Process(os.getpid())
        memusage = process.memory_info().rss  # in bytes
        stats = 'Input set processed in %.3f seconds' % (time.time() - start_time)
        stats += '\\n' + "Problem ID: {0}".format(self.problem_id)
        stats += '\\n' + "Solution mode: {0}".format(self.args.mode.upper())
        stats += '\\n' + "Total number of nodes: {0}".format(node_id)
        stats += '\\n' + "Number of unique nodes: {0}".format(uniques)
        stats += '\\n' + "Number of redundant subtrees: {0}".format(redundants)
        stats += '\\n' + "Number of leaves nodes: {0}".format(leaves)
        #stats += '\\n' + "Total number of nodes in a complete binary tree for the problem: {0}".format(int(math.pow(2, math.ceil(math.log2(node_id)))-1))
        stats += '\\n' + "Current memory usage: {0}".format(sizeof_fmt(memusage))

        # draw graph
        if self.args.output_graph_file:
            dot.node("stats", stats, shape="record", style="dotted")
            self.draw_graph(dot, self.args.output_graph_file)

        if self.args.quiet == False:
            print("Execution finished!")
            print(stats.replace("\\n", "\n"))


    # update the size of sub graphs
    # def update_subgraph_sizes(id_leaves, id_pid, id_size):
    #     # starting for leaf nodes, set the number of nodes under each node
    #     for child_id in id_leaves:
    #         for parent in id_pid[child_id]:

