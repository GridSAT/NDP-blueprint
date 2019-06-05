import sys
import time
from graphviz import Digraph
from queue import Queue
from configs import *

class PatternSolver:

    # the dictionary that holds processed set
    # currently each key is the string represenation of the set, i.e. set.to_string()
    setmap = {}
    args = None
    def __init__(self, args=None):
        self.setmap.clear()        
        self.args = args
        return

    def draw_graph(self, dot, outputfile):
        #print(dot.source)
        fg = open(outputfile, "w")
        fg.write(dot.source)
        fg.close()


    def process_set(self, root_set):
        
        start_time = time.time()
        redundants = 0

        # graph drawing
        node_id = 0
        
        dot = Digraph(comment='The CNF Tree', format='svg')
        nodes_queue = Queue()
        nodes_queue.put(root_set)
        root_set.id = node_id
        
        if self.args.output_graph_file:            
            dot.node(str(root_set.id), root_set.to_string())
        
        node_id += 1

        while not nodes_queue.empty():
            nodecolor = 'black'
            cnf_set = nodes_queue.get()

            # check if the set is already evaluated to boolean value            
            if cnf_set.value != None:
                if self.args.output_graph_file:     
                    setbefore = cnf_set.to_string()
                    dot.node(str(cnf_set.id), setbefore)
                continue

            # to l.o. condition
            logger.debug("Set #{0} - to L.O. condition".format(node_id))   
            cnf_set.to_lo_condition()            
            setafterhash = cnf_set.get_hash()

            # check if we have processed the set before
            if self.setmap.get(setafterhash, None):
                self.setmap[setafterhash] += 1
                redundants += 1
                if self.args.output_graph_file:     
                    nodecolor = 'red'
                    setafter = cnf_set.to_string()
                    dot.node(str(cnf_set.id), setbefore + "\\n" + setafter, color=nodecolor)
                continue
            else:
                # when the set reaches l.o. condition, we update the global sets record
                self.setmap[setafterhash] = 1

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


        # draw graph
        if self.args.output_graph_file:     
            self.draw_graph(dot, self.args.output_graph_file)

        print("Execution finished!")
        print('Input set processed in %.3f seconds' % (time.time() - start_time))
        print("Total number of unique nodes: {0}".format(len(self.setmap)))
        print("Total number of redundant nodes: {0}".format(redundants))

