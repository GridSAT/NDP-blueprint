# This is InputReader class
# SLF: Single Line Format, is where the input CNF in represented in one line only in the form:
#    a | b | c & d | -e | f & ...
# DIMAC: DIMACS (the Center for Discrete Mathematics and Theoretical Computer Science) at Rutgers university format
# Information about the format can be found at https://people.sc.fsu.edu/~jburkardt/data/cnf/cnf.html

import os
import sys
from configs import INPUT_SL, INPUT_SLF, INPUT_DIMACS
from Set import Set
from Clause import Clause

class InputReader:

    input = None
    input_type = None

    def __init__(self, intype, input):
        
        # sanity checks
        if input == None or input == "":
            raise Exception("InputReader Error: Null input provided!")

        if intype not in [INPUT_SL, INPUT_SLF, INPUT_DIMACS]:
            raise Exception("InputReader Error: Input type is not a recognized type")

        # if the input is file, the passed argument is a file object opened in 'read' mode
        # if intype in [INPUT_SLF, INPUT_DIMACS]:
        #     if not os.path.isfile(input):
        #         raise FileNotFoundError("InputReader Error: File {0} is not found.".format(input))

        if intype == INPUT_SL:
            input = input.strip()

        self.input = input
        self.input_type = intype
    

    # Parsing Single Line format
    def __parse_single_line_input(self, str_input):
        
        seq = str_input
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
        
        return CnfSet


    # read the input file and return a CNF set
    def get_cnf_set(self):
        
        # input set has to be all in one line
        if self.input_type == INPUT_SLF:          
            seq = self.input.readline()
        
        if self.input_type in [INPUT_SL, INPUT_SLF]:
            return self.__parse_single_line_input(seq)
            
            

