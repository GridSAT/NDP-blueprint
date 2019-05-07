# config


class Set:

    clauses = []
    def __init__(self):
        return

    def sort_clauses(self):
        self.clauses = sorted(self.clauses)

    def print_set(self):
        for cl in self.clauses:
            print(cl.raw)

class Clause:

    raw = []
    def __init__(self, arr):
        x = sorted(list(arr), key = abs)
        self.raw = x
        
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
    

def process_set(Set):


    # sort the clauses
    Set.sort_clauses()
    Set.print_set()

    # rename

    # check L.O. conditions


if __name__ == "__main__":
        
    # input set has to be all in one line
    with open("in.txt", "r") as f:
        seq = f.readline()
        
        # generate objects
        CnfSet = Set()
        try:
            clauses = seq.split('&')            
            for cl in clauses:
                s = cl.split('|')
                s = set(map(int, s))
                
                # create clauses
                # a clause gets sorted automatically when the clause object is created
                CnfSet.clauses.append(Clause(s))
        except Exception as e:
            print("Error: " + str(e))

        # start processing the root set
        if len(CnfSet.clauses) > 0:
            process_set(CnfSet)

        
        



        

