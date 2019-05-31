from Set import *
from Clause import *
from PatternSolver import *

### config
# the min id of a literal in a set


# todo: handle if input has [x, -x]

# a class to represent the CNF graph
class CnfGraph:

    content = None    

    def __init__(self, content = None):
        self.content = content

    def print_node(self):
        print(self.content)



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
            PAT = PatternSolver()
            PAT.process_set(CnfSet)

        
        



        

