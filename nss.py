from queue import SimpleQueue
from graphviz import Digraph

# config

# todo: handle if input has [x, -x]

# a class to represent the CNF graph
class CnfGraph:

    content = None
    

    def __init__(self, content = None):
        self.content = content

    def print_node(self):
        print(self.content)


class Set:

    clauses = []
    names_map = {}
    value = None    # unknown, not evaluated
    left = None
    right = None
    id = 0

    def __init__(self):
        self.names_map = {}
        return

    def sort_within_clauses(self):
        for i in range(0, len(self.clauses)):
            self.clauses[i].sort()

    def sort_clauses(self):
        self.clauses = sorted(self.clauses)


    def rename_vars(self):
        # start from 0
        id = 1
        self.names_map = {}
        for cl in self.clauses:
            for i in range(0, len(cl.raw)):
                sign = (int) (cl.raw[i] / abs(cl.raw[i]))
                new = self.names_map.get(abs(cl.raw[i]), None)
                if new == None:
                    new = id
                    self.names_map[abs(cl.raw[i])] = new
                    id = id + 1
                    
                cl.raw[i] = new * sign

    # when all clauses in a set get evaluated, then the set has a final value
    def set_value(self, val):
        self.value = val

    # l.o. state as in "Constructive patterns of logical truth", or "#2SAT is in P" p. 23:
        # 1- variables within clauses are in ascending order.
        # 2- clauses are in ascending ordered in the Set
        # 3- All new Names/Indices of literals occurring for the first time in any clause of S are strictly greater than all the Literal Names/Indices occurring before them in S.
        # 4- each clause is unique in the set. (this was already done on input parsing)
    def is_in_lo_state(self):

        # condition 1
        self.sort_within_clauses()

        # condition 2
        self.sort_clauses()

        # condition 3
        seen_vars = {}
        if len(self.clauses) > 0 and len(self.clauses[0].raw) > 0:
            min_var = abs(self.clauses[0].raw[0])
            seen_vars[min_var] = True

            for cl in self.clauses:
                for var in cl.raw:
                    var = abs(var)
                    if var < min_var and not seen_vars.get(var, None):
                        return False

                    if not seen_vars.get(var, None):
                        seen_vars[var] = True
                        min_var = var


        return True

        
    # convert to L.O. condition
    def to_lo_condition(self):
        i = 0
        # check L.O. conditions
        while not self.is_in_lo_state():        
            # rename
            print('Renaming...')
            self.rename_vars()
            # self.print_set()
            print('===========')

            # i = i + 1
            # if i > 4:
            #     break


    # evaluate the set and produce two branches
    def evaluate(self):
        # sanity check
        if len(self.clauses) <= 0 or len(self.clauses[0].raw) <= 0: 
            return (None, None)

        # always pick the left most variable and evaluate based on it.
        pivot = abs(self.clauses[0].raw[0])

        # Left Set: iterate through clauses, for each clause check if it has pivot, set it to True. If it has -pivot, remove the variable from the set
        # Right Set: opposite of left
        left_set = Set()
        right_set = Set()

        left_clauses = []
        right_clauses = []
        for cl in self.clauses:
            # remove clause, i.e. set the var to true
            if pivot == cl.raw[0]:
                # for left branch, the clause will be set to true. i.e. removed. (will not be addd to left_clauses)
                
                # for right branch, remove the var from the clause
                cl.raw.pop(0)
                if len(cl.raw) > 0:
                    right_clauses.append(cl)
                # if it's the last variable, then the clause will be evaluated to False, then all the Set will be False
                else:
                    right_set.set_value(False)
            # if it's negated, remove it from the clause and return the rest
            elif pivot == -cl.raw[0]:
                # for right branch, the clause will be set to true. i.e. removed.

                # for left branch, remove the var from the clause
                cl.raw.pop(0)
                if len(cl.raw) > 0:
                    left_clauses.append(cl)
                # if it's the last variable, then the clause will be evaluated to False
                else:
                    left_set.set_value(False)

            else:
                left_clauses.append(cl)
                right_clauses.append(cl)

        
        
        left_set.clauses = left_clauses
        right_set.clauses = right_clauses

        if len(left_clauses) == 0 and left_set.value == None:
            left_set.set_value(True)

        if len(right_clauses) == 0 and right_set.value == None:
            right_set.set_value(True)
            
        return (left_set, right_set)


    def to_string(self):

        # if the set evaluates to a value
        if self.value != None:
            res = str(self.value)[0]
            return res

        # This shouldn't ever happen. If the set doesn't have a value, then it must has clauses
        if len(self.clauses) == 0:
            raise ValueError('A set with empty clauses and no evaluated values!')

        res_arr = []
        for cl in self.clauses:
            if len(cl.raw):
                res_arr.append('(' + ' | '.join(map(str, cl.raw)) + ')')

        res = ' & '.join(res_arr)
        return res
        

    def print_set(self):
        print(self.to_string())



class Clause:

    raw = []
    value = None
    def __init__(self, inp):
        if type(inp) is list or type(inp) is frozenset:
            self.raw = list(inp)
            self.sort()

        elif type(inp) is bool:
            self.value = inp
        
    def __lt__(self, other):
        selflen = len(self.raw)
        otherlen = len(other.raw)

        # in case one of them is shorter, return the shorter
        if selflen != otherlen:
            return selflen < otherlen
               
        # case where both are of equal length
        for i in range(0, selflen):

            if self.raw[i] == other.raw[i]:
                continue

            # only if two number with different signs, ex. -5 and 5, are compared, consider -5 is less
            if self.raw[i] != other.raw[i] and abs(self.raw[i]) == abs(other.raw[i]):
                return self.raw[i] < other.raw[i]
            
            # do absolute value comparison, so that -5 is greater than 3, for example.
            return abs(self.raw[i]) <= abs(other.raw[i])

        # in case both are identical lengths and values
        return 0 < 1
    

    def sort(self):
        x = sorted(self.raw, key = abs)
        self.raw = x




def draw_graph(dot):
    print(dot.source)
    #dot.render('out.svg', view=True)


def process_set(root_set):

    # cnf_set.print_set()
    # print('===========')
    
    # print('In L.O condition:')
    # cnf_set.print_set()
    
    # graph drawing
    node_id = 1
    dot = Digraph(comment='The CNF Tree', format='svg')

    nodes_queue = SimpleQueue()
    nodes_queue.put(root_set)
    root_set.id = node_id    
    dot.node(str(root_set.id), root_set.to_string())
    node_id += 1

    while not nodes_queue.empty():
        cnf_set = nodes_queue.get()

        # to l.o. condition
        setbefore = cnf_set.to_string()
        cnf_set.to_lo_condition()
        setafter = cnf_set.to_string()
        dot.node(str(cnf_set.id), setbefore + "\\n" + setafter)

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
    draw_graph(dot)
    




    # when the set reaches l.o. condition, we update the global sets record


if __name__ == "__main__":
        
    # input set has to be all in one line
    with open("in.txt", "r") as f:
        seq = f.readline()
        
        # generate objects
        CnfSet = Set()
        try:
            clauses = seq.split('&')
            clauses_set = set()            
            for cl in clauses:
                s = cl.split('|')
                # remove duplicates within clause
                s = frozenset(map(int, s))
                
                # adding in a set container will remove duplicate clauses    
                clauses_set.add(s)


            # create clauses objects
            for cl in clauses_set:                
                # a clause gets sorted automatically when the clause object is created
                CnfSet.clauses.append(Clause(cl))

        except Exception as e:
            print("Error: " + str(e))

        # start processing the root set
        if len(CnfSet.clauses) > 0:
            process_set(CnfSet)

        
        



        

