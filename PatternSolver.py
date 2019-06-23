import os, gc
import sys
import time, math
import psutil
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
    use_db = False

    def __init__(self, args=None, problem_id=PROBLEM_ID):
        self.setmap.clear()
        self.args = args
        if problem_id:
            self.problem_id = problem_id

        if args.use_db:
            self.use_db = True
            self.db_adaptor = DbAdapter()        

    def draw_graph(self, dot, outputfile):
        fg = open(outputfile, "w")
        fg.write(dot.source)
        fg.close()

    def load_set_records(self, setobj):
        #if self.use_db:
            # select from db table, all sets hashes of # clauses <= # of clauses of input set
        return
            
    def is_set_seen(self, set_hash):
        return self.setmap.get(set_hash, False)
        
        #return self.db_adaptor.does_exist(self.problem_id, set_hash)


    def update_set_seen_count(self, set_hash):
        #if not self.use_db:
        self.setmap[set_hash] += 1

        #return self.db_adaptor.update_count(self.problem_id, set_hash)


    def add_encountered_set(self, set_hash):
        self.setmap[set_hash] = 1

        #return self.db_adaptor.insert_row(self.problem_id, set_hash)

        
    def process_child_node(self, child_set, dot):

        node_status = None
        nodecolor = 'black'

        # check if the set is already evaluated to boolean value            
        setbefore = child_set.to_string()
        if child_set.value != None:
            if self.args.output_graph_file:
                dot.node(str(child_set.id), str(child_set.id) + "\\n" + setbefore)
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
            
            else:                
                # when the set reaches l.o. condition, we update the global sets record
                node_status = NODE_UNIQUE
                self.add_encountered_set(setafterhash)

            if self.args.output_graph_file:
                setafter = child_set.to_string()
                dot.node(str(child_set.id), str(child_set.id) + "\\n" + setbefore + "\\n" + setafter, color=nodecolor)

        return node_status


    def process_set(self, root_set):
        
        start_time = time.time()
        uniques = redundants = leaves = 0
        # graph drawing
        node_id = 1
        root_set.id = node_id
        dot = Digraph(comment='The CNF Tree', format='svg')
        uniques += 1

        logger.debug("Set #{} - to root set to {} mode".format(root_set.id, self.args.mode))
        setbefore = root_set.to_string()
        root_set.to_lo_condition(self.args.mode)
        setafterhash = root_set.get_hash()
        self.add_encountered_set(setafterhash)
        try:
            squeue = SuperQueue.SuperQueue(use_db=self.use_db, problem_id=self.problem_id)        
            squeue.insert(root_set)
        except (Exception, error) as error:
            logger.error("DB Error: " + str(error))
            return False
            
        if self.args.output_graph_file:
            setafter = root_set.to_string()
            dot.node(str(root_set.id), str(root_set.id) + "\\n" + setbefore + "\\n" + setafter, color='black')

        while not squeue.is_empty():            
            cnf_set = squeue.pop()            
            logger.debug("Set #{0}".format(cnf_set.id))            

            # evaluate
            (s1, s2) = cnf_set.evaluate()
            
            for child in (s1, s2):
                node_id += 1
                child.id = node_id
                
                if self.args.output_graph_file:
                    dot.edge(str(cnf_set.id), str(child.id))

                node_status = self.process_child_node(child, dot)
                if node_status == NODE_UNIQUE:
                    uniques += 1
                    squeue.insert(child)
                elif node_status == NODE_REDUNDANT:
                    redundants += 1
                elif node_status == NODE_EVALUATED:
                    leaves += 1

            if self.args.verbos:
                print("Nodes so far: {:,}".format(node_id), end='\r')

            
        print("\n")
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

