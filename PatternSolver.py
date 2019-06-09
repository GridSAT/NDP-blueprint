import sys
import time
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

        

    def process_set(self, root_set):
        
        start_time = time.time()
        uniques = 0
        redundants = 0

        # graph drawing
        node_id = 0
        dot = Digraph(comment='The CNF Tree', format='svg')
        nodes_queue = Queue()
        nodes_queue.put(root_set)
        root_set.id = node_id
        node_id += 1

        while not nodes_queue.empty():
            nodecolor = 'black'
            cnf_set = nodes_queue.get()

            setbefore = cnf_set.to_string()
            # check if the set is already evaluated to boolean value            
            if cnf_set.value != None:
                if self.args.output_graph_file:     
                    dot.node(str(cnf_set.id), setbefore)
                continue

            # to l.o. condition
            logger.debug("Set #{0} - to L.O. condition".format(node_id))   
            cnf_set.to_lo_condition()            
            setafterhash = cnf_set.get_hash()

            # check if we have processed the set before
            if self.is_set_seen(setafterhash):
                self.update_set_seen_count(setafterhash)
                redundants += 1
                if self.args.output_graph_file:     
                    nodecolor = 'red'
                    setafter = cnf_set.to_string()
                    dot.node(str(cnf_set.id), setbefore + "\\n" + setafter, color=nodecolor)
                continue
            

            # when the set reaches l.o. condition, we update the global sets record
            uniques += 1
            self.add_encountered_set(setafterhash)

            if self.args.output_graph_file:
                setafter = cnf_set.to_string()
                dot.node(str(cnf_set.id), setbefore + "\\n" + setafter, color=nodecolor)

            # evaluate
            logger.info("Set #{0}".format(node_id))
            (s1, s2) = cnf_set.evaluate()
            if s1 != None:
                s1.id = node_id            
                node_id += 1

                if self.args.output_graph_file:     
                    dot.edge(str(cnf_set.id), str(s1.id))            

                cnf_set.left = s1

                nodes_queue.put(s1)

            if s2 != None:
                s2.id = node_id            
                node_id += 1
                
                if self.args.output_graph_file:     
                    dot.edge(str(cnf_set.id), str(s2.id))
                
                cnf_set.right = s2

                nodes_queue.put(s2)


        stats = 'Input set processed in %.3f seconds' % (time.time() - start_time) 
        stats += '\\n' + "Total number of unique nodes: {0}".format(uniques)
        stats += '\\n' + "Total number of redundant nodes: {0}".format(redundants)

        # draw graph
        if self.args.output_graph_file:
            dot.node("stats", stats, shape="record", style="dotted")
            self.draw_graph(dot, self.args.output_graph_file)


        print("Execution finished!")
        print(stats.replace("\\n", "\n"))

