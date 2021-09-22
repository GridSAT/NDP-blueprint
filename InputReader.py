# InputReader.py
#
# Copyright © 2016 - 2021 EasyXPS, Inc. <info@easyxps.com>
# All rights reserved.
# Simply Efficient. is a trademark of EasyXPS, Inc.
#

# SLF: Single Line Format, is where the input CNF in represented in one line only in the form:
#    a | b | c & d | -e | f & ...
# DIMAC: DIMACS (the Center for Discrete Mathematics and Theoretical Computer Science) at Rutgers university format
# Information about the format can be found at https://people.sc.fsu.edu/~jburkardt/data/cnf/cnf.html

import os
import sys
from configs import *
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

        # generate object
        CnfSet = Set(str_input)
        return CnfSet


    # DIMACS parser
    # Assumptions:
    #   Only one 0 in a particular line
    def __parse_dimacs_file(self, dimacs_file):

        logger.debug("Reading DIMACS file...")

        # first line is the header
        dline = dimacs_file.readline()
        lcnt = 1
        clause = []
        # Initially I added the clauses in a set data structure to remove duplicates, then we add them in Set object at end of the method
        # However, this altered the input ordered of the clauses, which will violate the -lou option. Hence, I made it a list but accepted the fact
        # that there could be an input with duplicate clauses, in rare cases, however, that won't affect the final outcome.
        clauses_set = []
        CnfSet = Set()

        while dline:
            dline = dimacs_file.readline().strip()
            lcnt += 1

            # if line is empty
            if not dline:
                continue

            # skip comments, a comment line starts with 'c'
            if dline.startswith('c'):
                continue

            try:
                # problem statement line
                if dline.startswith('p'):
                    p, problem, varnum, clausnum = dline.split()
                    logger.debug("DIMACS: problem is {0} with {1} variables and {2} clauses.".format(problem, varnum, clausnum))

                # read clause
                else:
                    # this is developed based on the assumption that an ugly file is being provided that could has more than one 0 in the same line
                    elems = dline.split(' ')
                    for el in elems:
                        if not el:
                            continue

                        iel = int(el)

                        if iel == 0 and len(clause) == 0:
                            continue

                        # if clause already has element, close it and start a new one
                        if iel == 0:
                            if len(clause) > 3:
                                logger.critical("Error parsing DIMACS file at line {0}. A clause has more than 3 literals".format(lcnt))
                                raise Exception("Error parsing DIMACS file at line {0}. A clause has more than 3 literals".format(lcnt))

                            clauses_set.append(frozenset(clause))
                            clause = []

                        else:
                            clause.append(iel)

            except Exception as e:
                raise Exception("Error parsing DIMACS file at line {0} \n Exception: {1}".format(lcnt, str(e)))

        # end of reading the file
        # if clause has elements, then close it
        if len(clause):
            clauses_set.append(frozenset(clause))

        # create clauses objects
        for cl in clauses_set:
            # a clause gets sorted automatically when the clause object is created
            CnfSet.add_clause(Clause(cl))

        dimacs_file.close()
        return CnfSet



    # read the input file and return a CNF set
    def get_cnf_set(self):

        # input set has to be all in one line
        if self.input_type == INPUT_SLF:
            seq = self.input.readline()
            self.input.close()

        if self.input_type in [INPUT_SL, INPUT_SLF]:
            return self.__parse_single_line_input(seq)

        if self.input_type == INPUT_DIMACS:
            return self.__parse_dimacs_file(self.input)

        else:
            raise Exception("Unknown input source")
