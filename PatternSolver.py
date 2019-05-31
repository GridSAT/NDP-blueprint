from graphviz import Digraph
from queue import Queue

class PatternSolver:

    # the dictionary that holds processed set
    # currently each key is the string represenation of the set, i.e. set.to_string()
    setmap = {}

    def __init__(self):
        self.setmap.clear()        
        return

    def draw_graph(self, dot):
        #print(dot.source)
        fg = open("graph.txt", "w")
        fg.write(dot.source)
        fg.close()
        #dot.render('out.svg', view=True)


    def process_set(self, root_set):

        # cnf_set.print_set()
        # print('===========')
        
        # print('In L.O condition:')
        # cnf_set.print_set()
        
        # graph drawing
        node_id = 1
        dot = Digraph(comment='The CNF Tree', format='svg')

        nodes_queue = Queue()
        nodes_queue.put(root_set)
        root_set.id = node_id    
        dot.node(str(root_set.id), root_set.to_string())
        node_id += 1

        while not nodes_queue.empty():
            nodecolor = 'black'
            cnf_set = nodes_queue.get()

            # check if the set is already evaluated to boolean value
            setbefore = cnf_set.to_string()
            if cnf_set.value != None:
                dot.node(str(cnf_set.id), setbefore)
                continue

            # to l.o. condition
            cnf_set.to_lo_condition()
            setafter = cnf_set.to_string()

            # check if we have processed the set before
            if self.setmap.get(setafter, None):
                nodecolor = 'red'
                dot.node(str(cnf_set.id), setbefore + "\\n" + setafter, color=nodecolor)
                continue
            else:
                self.setmap[setafter] = 1

            dot.node(str(cnf_set.id), setbefore + "\\n" + setafter, color=nodecolor)


            


            # evaluate
            cnf_set.print_set()
            (s1, s2) = cnf_set.evaluate()
            if s1 != None:
                s1.id = node_id            
                # dot.node(str(s1.id), s1.to_string())
                node_id += 1

                dot.edge(str(cnf_set.id), str(s1.id))            
                cnf_set.left = s1

                nodes_queue.put(s1)

            if s2 != None:
                s2.id = node_id            
                # dot.node(str(s2.id), s2.to_string())
                node_id += 1

                dot.edge(str(cnf_set.id), str(s2.id))
                cnf_set.right = s2

                nodes_queue.put(s2)


        # draw graph
        self.draw_graph(dot)