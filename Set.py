import hashlib
from configs import *
from Clause import *

class Set:
    

    def __init__(self, str_input=None):

        self.clauses = []
        self.value = None
        self.id = 0
        # create a Set object from input string
        if str_input:
            seq = str_input
            try:
                seq = seq.replace('(', '')
                seq = seq.replace(')', '')
                clauses = seq.split('&')
                clauses_set = []
                for cl in clauses:
                    s = cl.split('|')
                    # remove duplicates within clause
                    s = frozenset(map(int, s))
                    
                    # adding in a set container will remove duplicate clauses but will shuffle input order, so don't do it   
                    clauses_set.append(s)

                # create clauses objects
                for cl in clauses_set:
                    self.add_clause(Clause(cl))

            except Exception as e:
                print("Error: " + str(e))
            

    # when all clauses in a set get evaluated, then the set has a final value
    def set_value(self, val):
        self.value = val

    def add_clause(self, cl):
        # no need to add new clauses if the set is already evaluated previous to False
        if self.value == False:
            return

        if cl.value == False:
            self.set_value(False)
        elif cl.value == True and len(self.clauses) == 0:
            self.set_value(True)
        elif cl.value == None:
            self.clauses.append(cl)
            self.set_value(None)

        # if cl == True, then it has no meaning to add it

    def sort_within_clauses(self):
        for i in range(0, len(self.clauses)):
            self.clauses[i].sort()

    def sort_clauses(self):
        self.clauses = sorted(self.clauses)
        #self.clauses.sort()

    def rename_vars(self):
        # start from 1
        id = 1
        names_map = {}
        for cl in self.clauses:
            for i in range(0, len(cl.raw)):
                sign = (int) (cl.raw[i] / abs(cl.raw[i]))
                new = names_map.get(abs(cl.raw[i]), None)
                if new == None:
                    new = id
                    names_map[abs(cl.raw[i])] = new
                    id = id + 1
                    
                cl.raw[i] = new * sign
        

    # l.o. state as in "Constructive patterns of logical truth", or "#2SAT is in P" p. 23:
        # 1- variables within clauses are in ascending order.
        # 2- clauses are in ascending ordered in the Set
        # 3- All new Names/Indices of literals occurring for the first time in any clause of S are strictly greater than all the Literal Names/Indices occurring before them in S.
        # 4- each clause is unique in the set. (this was already done on input parsing)
        # 5- the minimum literal id in the set equals MIN_LITERAL (new rule not in the paper). This is to force renaming if previous conditions are met but IDs start from a large value.
    #@param: mode:
        # lo (linearly ordered), all conditions are met
        # lou (linearly ordered universal), is a state where condition# 2 is skipped
        # normal: only condition 1 is met
    def is_in_lo_state(self, mode=MODE_LO):

        # condition 1
        self.sort_within_clauses()

        # condition 2
        if mode != MODE_LOU and mode != MODE_NORMAL:
            self.sort_clauses()

        # condition 3
        if mode != MODE_NORMAL:
            seen_vars = {}
            if len(self.clauses) > 0 and len(self.clauses[0].raw) > 0:
                min_var = abs(self.clauses[0].raw[0])
                seen_vars[min_var] = True

                # condition 5 check
                if min_var > MIN_LITERAL:
                    logger.debug("Not in l.o.: min_var > MIN_LITERAL. min_var = {0}, MIN_LITERAL = {1}".format(min_var, MIN_LITERAL))
                    return False

                for cl in self.clauses:
                    for var in cl.raw:
                        var = abs(var)
                        if var < min_var and not seen_vars.get(var, None):
                            logger.debug("Not in l.o.: var < min_var and not seen before. var = {0}, min_var = {1}".format(var, min_var))
                            return False

                        if not seen_vars.get(var, None):
                            seen_vars[var] = True
                            min_var = var

        return True

        
    # convert to L.O. condition
    def to_lo_condition(self, mode=MODE_LO):
        # check L.O. conditions
        while not self.is_in_lo_state(mode):        
            # rename
            self.rename_vars()


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
                    right_clauses.append(Clause(cl.raw))
                # if it's the last variable, then the clause will be evaluated to False, then all the Set will be False
                else:
                    right_set.set_value(False)
            # if it's negated, remove it from the clause and return the rest
            elif pivot == -cl.raw[0]:
                # for right branch, the clause will be set to true. i.e. removed.

                # for left branch, remove the var from the clause
                cl.raw.pop(0)
                if len(cl.raw) > 0:
                    left_clauses.append(Clause(cl.raw))
                # if it's the last variable, then the clause will be evaluated to False
                else:
                    left_set.set_value(False)

            else:
                left_clauses.append(Clause(cl.raw))
                right_clauses.append(Clause(cl.raw))
        
        
        left_set.clauses = left_clauses
        right_set.clauses = right_clauses

        if len(left_clauses) == 0 and left_set.value == None:
            left_set.set_value(True)

        if len(right_clauses) == 0 and right_set.value == None:
            right_set.set_value(True)
            
        return (left_set, right_set)


    def to_string(self, pretty=True):

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
                if pretty:
                    res_arr.append('(' + ' | '.join(map(str, cl.raw)) + ')')
                else:                    
                    res_arr.append('|'.join(map(str, cl.raw)))

        if pretty:
            res = ' & '.join(res_arr)
        else:
            res = '&'.join(res_arr)
            
        return res
        
    def get_hash(self):
        # sha1 hash
        return hashlib.sha1(bytes(self.to_string(pretty=False), "ascii")).digest()


    def print_set(self):
        print(self.to_string())
