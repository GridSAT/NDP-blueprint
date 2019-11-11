import os, gc
import sys
import time, math
import psutil
import binascii
from collections import defaultdict
from graphviz import Digraph
from queue import Queue
from configs import *
from DbAdaptor import DbAdapter
import SuperQueue
from Set import Set

# TODO:
#
# 1- The check if a node exist in the global DB, I need to implement it with another option to issue a query to gdb to check existice of the node,
# instead of loading all the nodes from the gdb and occupy lots of memory.
#
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


TRUE_SET_HASH = Set.calculate_hash('T')
FALSE_SET_HASH = Set.calculate_hash('F')

# An object represent a node in the graph
class Node:
    
    def __init__(self):
        self.seen_count = 1
        self.parents = []
        self.seen_count = 1
        self.status = NODE_UNIQUE
        self.subgraph_uniques = 1
        self.subgraph_redundants = 0

        # one of its decendants is a redundant, but it could be redundant with another subgraph
        # has_potential_redundant is a flag that bubbles up from decendants to the parent.
        # if a parent node found two children with the flag set to True, it means it has a redundant node in its subgraph
        self.has_potential_redundant = False     


class PatternSolver:

    # the dictionary that holds processed set
    # currently each key is the string represenation of the set, i.e. set.to_string()
    seen_sets = {}          # stores all nodes in global db
    solved_sets = {}                        # stores solved sets pulled from global db
    graph = {}                              # stores the nodes as we solve them
    args = None
    db_adaptor = None
    problem_id = None
    use_runtime_db = False
    global_table_name = GLOBAL_SETS_TABLE

    def __init__(self, args=None, problem_id=PROBLEM_ID):
        self.seen_sets.clear()
        self.args = args
        self.leaves = []
        # populate nodes_stats with defaults
        self.nodes_stats = defaultdict(lambda: [0,0])

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
            # load solved hashes
            solve_hashes = self.db_adaptor.gs_load_solved_sets(self.global_table_name, num_clauses)
            self.solved_sets = {el:1 for el in solve_hashes}
            # load unsolved hashes
            unsolve_hashes = self.db_adaptor.gs_load_unsolved_sets(self.global_table_name, num_clauses)
            self.seen_sets = {el:1 for el in unsolve_hashes}
            # combine solved and unsolved in seen_sets map
            self.seen_sets.update(self.solved_sets)
            
    def get_children_from_gdb(self, set_hash):
        result = ()
        children = self.db_adaptor.gs_get_children(self.global_table_name, set_hash)        
        for child_hash in children:
            if child_hash == None:
                return (None, None)

            child = Set()
            if child_hash == TRUE_SET_HASH:
                child.value = True
            elif child_hash == FALSE_SET_HASH:
                child.value = False
            else:
                # get the body from the db
                set_body = self.db_adaptor.gs_get_body(self.global_table_name, child_hash)
                if set_body == None:
                    return (None, None)

                child = Set(set_body)
            
            result = result + (child, )

        return result

    def is_in_graph(self, set_hash):
        return self.graph.get(set_hash, False)

    def is_set_in_gdb(self, set_hash):
        return self.seen_sets.get(set_hash, False)

    def is_set_solved(self, set_hash):
        return self.solved_sets.get(set_hash, False)

    def update_graph_node_count(self, set_hash):
        # self.graph[set_hash].seen_count += 1
        # self.graph[set_hash].status = NODE_REDUNDANT
        self.seen_sets[set_hash] += 1 

    def save_unique_node(self, set_hash, set_id):
        # self.graph[set_hash] = Node()
        self.graph[set_hash] = set_id

    def save_parent_children(self, cnf_set, child1_hash, child2_hash):        
        cnf_hash = cnf_set.get_hash()
        # save to the graph. The only case where child hash wouldn't be in the graph is when it's for a leaf (true or false)
        # if child1_hash not in (TRUE_SET_HASH, FALSE_SET_HASH):
        #     self.graph[child1_hash].parents.append(cnf_set)
        # if child2_hash not in (TRUE_SET_HASH, FALSE_SET_HASH):
        #     self.graph[child2_hash].parents.append(cnf_set)
        
        # add to global sets table
        num_of_vars = 0
        if len(cnf_set.clauses):
            num_of_vars = abs(cnf_set.clauses[-1].raw[-1])

        # save the set in global DB if it's not there already
        if self.args.use_global_db and not self.is_set_in_gdb(cnf_hash):
            return self.db_adaptor.gs_insert_row(self.global_table_name,
                                         cnf_hash,              # set hash
                                         cnf_set.to_string(pretty=False),   # set body
                                         child1_hash,           # child 1 hash
                                         child2_hash,           # child 2 hash
                                         [],                    # mapping, to be added
                                         len(cnf_set.clauses),  # count of clauses
                                         num_of_vars)  
                                         
        return SUCCESS

    def get_node_subgraph_stats(self, node_id, nodes_children, node_descendants, node_redundants):

        if node_descendants.get(node_id, False):
            node_redundants[node_id] += 1
            return
        else:
            node_descendants[node_id] = 1
            
        for child_id in nodes_children[node_id]:
            self.get_node_subgraph_stats(child_id, nodes_children, node_descendants, node_redundants)


    def construct_graph_stats(self, root_id, nodes_children):
        root_node_redundants = {}

        for node_id in range(1, len(self.graph)+1):
            node_descendants = {}
            node_redundants = defaultdict(int)
            self.get_node_subgraph_stats(node_id, nodes_children, node_descendants, node_redundants)
            self.nodes_stats[node_id][UNIQUE_COUNT]      = len(node_descendants)
            self.nodes_stats[node_id][REDUNDANT_COUNT]   = len(node_redundants)

            if node_id == 1:
                root_node_redundants = node_redundants

        return root_node_redundants
    
    def save_in_global_db(self, root_redundants):
        # construct a dict of node_ids => hash
        id_to_hash = {}
        for k,v in self.graph.items():
            id_to_hash[v] = k

        for node_id in range(1, len(self.nodes_stats)):
            unique_nodes = self.nodes_stats[node_id][UNIQUE_COUNT]
            redundant_nodes = self.nodes_stats[node_id][REDUNDANT_COUNT]
            hash = id_to_hash[node_id]
            self.db_adaptor.gs_update_count(self.global_table_name, unique_nodes, redundant_nodes, hash)            
            
        # saving redundants hits
        for red_id, redundant_hits  in root_redundants.items():
            hash = id_to_hash[red_id]
            self.db_adaptor.gs_update_redundant_hits(self.global_table_name, redundant_hits, hash)


    def process_child_node(self, child_set, dot):
        node_status = None

        # check if the set is already evaluated to boolean value            
        if child_set.value != None:            
            node_status = NODE_EVALUATED

        else:
            # if user input mode is MODE_LO, it means only root is LO and the rest are LOU, and since this is a child node, then pass LOU argument
            if self.args.mode == MODE_LO:                
                logger.debug("Set #{} - convert to {} mode".format(len(self.graph), MODE_LOU))
                child_set.to_lo_condition(MODE_LOU)
            else:
                logger.debug("Set #{} - convert to {} mode".format(len(self.graph), self.args.mode))
                child_set.to_lo_condition(self.args.mode)

            setafterhash = child_set.get_hash()
            # check if we have processed the set before
            if self.is_in_graph(setafterhash):
                child_set.id = self.graph[setafterhash]
                #self.update_graph_node_count(setafterhash)
                node_status = NODE_REDUNDANT
            
            else:                
                # when the set reaches l.o. condition, we update the global sets record
                node_status = NODE_UNIQUE

        return node_status


    def process_set(self, root_set):
        
        start_time = time.time()
        uniques = redundants = leaves = 0

        # vars to calculate graph size at the end
        redundant_ids = {}  # ids of redundant nodes
        nodes_parents = {}  # for every id, there's an array of parents
        nodes_children = {} # children ids for every node
        
        # use global sets table
        if self.args.use_global_db:
            # create the table if not exist
            self.db_adaptor.gs_create_table(self.global_table_name)
            self.load_set_records(len(root_set.clauses))

        # graph drawing
        uniques += 1
        root_set.id = uniques
        graph_attr={}
        graph_attr["splines"] = "polyline"
        dot = Digraph(comment='The CNF Tree', format='svg', graph_attr=graph_attr)
        
        logger.debug("Set #{} - to root set to {} mode".format(root_set.id, self.args.mode))
        setbefore = root_set.to_string()
        root_set.to_lo_condition(self.args.mode)
        setafterhash = root_set.get_hash()
        
        # check if we have processed the CNF before
        if not self.is_set_solved(setafterhash):
            self.save_unique_node(setafterhash, root_set.id)
            nodes_parents[root_set.id] = []

            try:
                squeue = SuperQueue.SuperQueue(use_runtime_db=self.use_runtime_db, problem_id=self.problem_id)        
                squeue.insert(root_set)
            except (Exception, error) as error:
                logger.error("DB Error: " + str(error))
                logger.critical("Error - {0}".format(traceback.format_exc()))
                return False
                
            if self.args.output_graph_file:
                setafter = root_set.to_string()
                dot.node(str(root_set.id), str(root_set.id) + "\\n" + setbefore + "\\n" + setafter, color='black')

            while not squeue.is_empty():
                cnf_set = squeue.pop()
                nodes_children[cnf_set.id] = []
                logger.debug("Set #{0}".format(cnf_set.id))

                ## Evaluate
                ## check first if the set is unsolved in the global db. If so, just grab the children from there.
                ## if it's solved in gdb, it wouldn't be here in this loop at the first place.
                s1 = s2 = None
                ## although this step is working fine, but it slower down the program, so there's no need.
                if self.args.use_global_db and self.is_set_in_gdb(cnf_set.get_hash()) and not self.is_set_solved(cnf_set.get_hash()):
                    (s1, s2) = self.get_children_from_gdb(cnf_set.get_hash())
                
                if s1 == None or s2 == None:
                    (s1, s2) = cnf_set.evaluate()
                
                for child in (s1, s2):
                    child_str_before = child.to_string()
                    
                    child.status = self.process_child_node(child, dot)

                    child_str_after = child.to_string()
                    child_hash = child.get_hash()
                    
                    if child.status == NODE_UNIQUE:
                        uniques += 1 
                        child.id = uniques
                        self.save_unique_node(child_hash, child.id)
                        # add parent
                        nodes_parents[child.id] = [cnf_set.id]
                        nodes_children[cnf_set.id].append(child.id)

                        if self.args.output_graph_file:
                            dot.node(str(child.id), str(child.id) + "\\n" + child_str_before + "\\n" + child_str_after, color='black')

                    elif child.status == NODE_REDUNDANT:
                        redundants += 1
                        redundant_ids[child.id] = 1
                        nodes_parents[child.id].append(cnf_set.id)
                        nodes_children[cnf_set.id].append(child.id)

                        if self.args.output_graph_file:
                            dot.node(str(child.id), color='red')

                    elif child.status == NODE_EVALUATED:
                        leaves += 1
                        if self.args.output_graph_file:
                            child.id = child.to_string()
                            dot.node(child.id, child.to_string())

                    if self.args.output_graph_file:
                        dot.edge(str(cnf_set.id), str(child.id))

                # cnf nodes in this loop are all unique, if they weren't they wouldn't be in the queue
                # if insertion in the global table is successful, save children in the queue, 
                # otherwise, the cnf_set is already solved in the global DB table
                global_save_status = self.save_parent_children(cnf_set, s1.get_hash(), s2.get_hash())
                if global_save_status == SUCCESS:
                    for child in (s1, s2):
                        if child.status == NODE_UNIQUE and not self.is_set_solved(child.get_hash()):
                            squeue.insert(child)
                elif global_save_status == DB_UNIQUE_VIOLATION:
                    logger.info("Node #{} is already found 'during execution' in global DB.".format(cnf_set.id))
                
                # if both children are boolean, then cnf_set is a leaf node
                if s1.value != None and s2.value != None:
                    self.leaves.append(cnf_set.id)

                if self.args.verbos:
                    print("Nodes so far: {:,} uniques and {:,} redundants...".format(uniques, redundants), end='\r')

            
            ### Solving the set is done, let's get the number of unique and redundant nodes
            if self.args.verbos:
                print()
                print("=== Set has been solved successfully.")
                print("=== Getting statistics of all subgraphs...")

            root_redundants = self.construct_graph_stats(root_set.id, nodes_children)
    
            if self.args.verbos:
                print("=== Done getting the statistics.")
            
            if self.args.use_global_db:
                if self.args.verbos:
                    print("=== Saving the final result in the global DB...")

                self.save_in_global_db(root_redundants)

                redundants = len(redundant_ids)

        else:
            if self.args.verbos:
                print("Input set is found in the global DB")
                print("Pulling Set's data from the DB...")
                set_data = self.db_adaptor.gs_get_set_data(self.global_table_name, setafterhash)
                uniques = set_data["unique_nodes"]
                redundants = set_data["redundant_nodes"]

            
        #print("\n")
        process = psutil.Process(os.getpid())
        memusage = process.memory_info().rss  # in bytes
        stats = 'Input set processed in %.3f seconds' % (time.time() - start_time)
        stats += '\\n' + "Problem ID: {0}".format(self.problem_id)
        stats += '\\n' + "Solution mode: {0}".format(self.args.mode.upper())
        stats += '\\n' + "Number of unique nodes: {0}".format(uniques)
        stats += '\\n' + "Number of redundant subtrees: {0}".format(redundants)
        #stats += '\\n' + "Total number of nodes in a complete binary tree for the problem: {0}".format(int(math.pow(2, math.ceil(math.log2(node_id)))-1))
        stats += '\\n' + "Current memory usage: {0}".format(sizeof_fmt(memusage))

        # draw graph
        if self.args.output_graph_file:
            dot.node("stats", stats, shape="record", style="dotted")
            self.draw_graph(dot, self.args.output_graph_file)

        if self.args.quiet == False:
            print("\nExecution finished!")
            print(stats.replace("\\n", "\n"))


    # update the size of sub graphs
    # def update_subgraph_sizes(id_leaves, id_pid, id_size):
    #     # starting for leaf nodes, set the number of nodes under each node
    #     for child_id in id_leaves:
    #         for parent in id_pid[child_id]:

