import sys
import argparse
from Set import *
from Clause import *
from PatternSolver import *
from InputReader import InputReader

# todo: handle if input has [x, -x]

# a class to represent the CNF graph
class CnfGraph:

    content = None    

    def __init__(self, content = None):
        self.content = content

    def print_node(self):
        print(self.content)


def Main(args):

    # determine input type/format
    input_type = None
    input_content = None
    
    if args.line_input:
        input_type = INPUT_SL
        input_content = args.line_input

    elif args.line_input_file:
        input_type = INPUT_SLF
        input_content = args.line_input_file

    elif args.dimacs:
        input_type = INPUT_DIMACS
        input_content = args.dimacs

    # begin logic
    CnfSet = None
    try:
        input_reader = InputReader(input_type, input_content)
        CnfSet = input_reader.get_cnf_set()

        # start processing the root set
        if len(CnfSet.clauses) > 0:
            PAT = PatternSolver()
            PAT.process_set(CnfSet)

    except Exception as e:
        logger.debug("Error - {0}".format(str(e)))
        


if __name__ == "__main__":        

    parser = argparse.ArgumentParser(description="NasserSatSolver [OPTIONS]")
    parser.add_argument("-v", "--verbos", help="Verbos", action="store_true")
    parser.add_argument("-q", "--quiet", help="Quiet mode. No stdout output.")
    parser.add_argument("-l", "--line-input", type=str, help="Represent the input set in one line. Format: a|b|c&d|e|f ...")
    parser.add_argument("-lf", "--line-input-file", type=argparse.FileType('r'), help="Represent the input set in one line stored in a file. Format: a|b|c&d|e|f ...")
    parser.add_argument("-d", "--dimacs", type=argparse.FileType('r'), help="File name to contain the set in DIMACS format. See http://bit.ly/dimcasf")
    parser.add_argument("-g", "--output-graph-file", type=str, help="Output graph file in Graphviz format")

    args = parser.parse_args()

    if args.quiet:
        logger.setLevel(logging.CRITICAL)
    
    # at least one input must be provided
    if args.line_input == None and args.line_input_file == None and args.dimacs == None:
        print("No input provided. Please provide any of the input arguments.")
        parser.print_help()
        sys.exit(3)

    # only one input must be provided
    if (args.line_input and args.line_input_file) or (args.line_input and args.dimacs) or (args.dimacs and args.line_input_file):
        print("Please provide only one input.")
        parser.print_help()
        sys.exit(3)

    Main(args)
    

        
        



        

