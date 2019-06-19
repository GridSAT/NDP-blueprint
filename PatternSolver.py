import os, gc
import sys
import time, math
import psutil
from graphviz import Digraph
from queue import Queue
from configs import *
from DbAdaptor import DbAdapter

class PatternSolver:

    # the dictionary that holds processed set
    # currently each key is the string represenation of the set, i.e. set.to_string()
    setmap = {}
    args = None
    db_adaptor = None
    problem_name = "cnf_{}".format(str(time.time()).replace(".", "_"))
    use_db = False

    def __init__(self, args=None, problem_name=None):
        self.setmap.clear()
        self.args = args
        if problem_name:
            self.problem_name = problem_name

        if args.use_db:
            self.use_db = True
            self.db_adaptor = DbAdapter()            
            self.db_adaptor.create_table(self.problem_name)
        

    def draw_graph(self, dot, outputfile):
        fg = open(outputfile, "w")
        fg.write(dot.source)
        fg.close()

    def is_set_seen(self, set_hash):
        if not self.use_db:
            return self.setmap.get(set_hash, False)
        
        return self.db_adaptor.does_exist(self.problem_name, set_hash)


    def update_set_seen_count(self, set_hash):
        if not self.use_db:
            self.setmap[set_hash] += 1
            return

        return self.db_adaptor.update_count(self.problem_name, set_hash)


    def add_encountered_set(self, set_hash):
        if not self.use_db:
            self.setmap[set_hash] = 1
            return

        return self.db_adaptor.insert_row(self.problem_name, set_hash)

        
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
        uniques = 0
        redundants = 0
        # graph drawing
        node_id = 1
        dot = Digraph(comment='The CNF Tree', format='svg')
        nodes_queue = []
        nodes_queue.append(root_set)
        root_set.id = node_id
        uniques += 1

        logger.debug("Set #{} - to root set to {} mode".format(root_set.id, self.args.mode))
        setbefore = root_set.to_string()
        root_set.to_lo_condition(self.args.mode)
        setafterhash = root_set.get_hash()
        self.add_encountered_set(setafterhash)
        if self.args.output_graph_file:
            setafter = root_set.to_string()
            dot.node(str(root_set.id), str(root_set.id) + "\\n" + setbefore + "\\n" + setafter, color='black')

        while len(nodes_queue):            
            cnf_set = nodes_queue.pop(0)

            # evaluate
            logger.info("Set #{0}".format(cnf_set.id))
            (s1, s2) = cnf_set.evaluate()
                        
            for child in (s1, s2):
                node_id += 1
                child.id = node_id
                
                if self.args.output_graph_file:
                    dot.edge(str(cnf_set.id), str(child.id))

                node_status = self.process_child_node(child, dot)
                if node_status == NODE_UNIQUE:
                    uniques += 1
                    nodes_queue.append(child)
                elif node_status == NODE_REDUNDANT:
                    redundants += 1
            

        process = psutil.Process(os.getpid())
        memusage = process.memory_info().rss  # in bytes
        stats = 'Input set processed in %.3f seconds' % (time.time() - start_time) 
        stats += '\\n' + "Solution mode: {0}".format(self.args.mode)
        stats += '\\n' + "Total number of unique nodes: {0}".format(uniques)
        stats += '\\n' + "Total number of redundant subtrees: {0}".format(redundants)
        stats += '\\n' + "Total number of nodes in a complete binary tree for the problem: {0}".format(int(math.pow(2, math.ceil(math.log2(node_id+1)))-1))
        stats += '\\n' + "Current memory usage: {0}".format(sizeof_fmt(memusage))

        # draw graph
        if self.args.output_graph_file:
            dot.node("stats", stats, shape="record", style="dotted")
            self.draw_graph(dot, self.args.output_graph_file)

        if self.args.quiet == False:
            print("Execution finished!")
            print(stats.replace("\\n", "\n"))

