import os,sys
import time
import argparse, textwrap
from Set import *
from Clause import *
from PatternSolver import *
from InputReader import InputReader
import configs
import traceback

# todo: 
# - Handle if input has [x, -x]. What I did now is to normalize the clause once it get read. However, this will not enable us to 
#   view the initial set provided. Will see only the normalized version. The solution is to write normalize() method in each Clause and Set classes.
#   and in the evaluation loop, we call the method normalize() before to_lo_condition(). However, do we need to normalize each set? or it's just the root set?
#   This needs to be thought of well because we don't want to add extra time in the evaluation loop if we won't need normalization except for the root set.
#   Currently it works fine with the current implementation as it focuses only on root, but we just don't save the unnormalized version for the root set.

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
        if len(CnfSet.clauses) > 0 or CnfSet.value != None:
            PAT = PatternSolver(args=args, problem_id=CnfSet.get_hash().hex())
            PAT.solve_set(CnfSet)

            # save solution in a file
            if args.output_solution_file and PAT.solution:
                solution = PAT.format_solution(PAT.solution)
                file_name = PAT.problem_id

                # if input is a file
                if input_type != args.line_input:
                    file_name = os.path.splitext(input_content.name)[0]

                file_name += '_' + args.mode
                file_name += '.sol'
                fout = open(file_name, 'w')
                fout.write(solution)
                fout.close()
                logger.info(f"Solution written to: {file_name}")

            # verify the solution
            if args.verify and PAT.solution:
                if args.line_input: original_input = args.line_input
                else: original_input = open(input_content.name, 'r')
                input_reader = InputReader(input_type, original_input)
                CnfSet = input_reader.get_cnf_set()
                if PAT.verify_solution(CnfSet, PAT.solution):
                    logger.info("The solution is VERIFIED!")
                else:
                    logger.info("The solution is NOT correct! ****")
            

    except Exception as e:
        logger.critical("Error - {0}".format(str(e)))
        logger.critical("Error - {0}".format(traceback.format_exc()))
        


if __name__ == "__main__":

    start_time = time.time()
    class Formatter(argparse.RawTextHelpFormatter, argparse.ArgumentDefaultsHelpFormatter): pass
    parser = argparse.ArgumentParser(description="NasserSatSolver [OPTIONS]", formatter_class=argparse.RawTextHelpFormatter)
    group1 = parser.add_mutually_exclusive_group()
    group1.add_argument("-v", "--verbos", help="Verbos", action="store_true")
    group1.add_argument("-vv", "--very-verbos", help="Very verbos", action="store_true")
    group1.add_argument("-q", "--quiet", help="Quiet mode. No stdout output.", action="store_true")
    group2 = parser.add_mutually_exclusive_group(required=True)
    group2.add_argument("-l", "--line-input", type=str, help="Represent the input set in one line. Format: a|b|c&d|e|f ...")
    group2.add_argument("-lf", "--line-input-file", type=argparse.FileType('r'), help="Represent the input set in one line stored in a file. Format: a|b|c&d|e|f ...")
    group2.add_argument("-d", "--dimacs", type=argparse.FileType('r'), help="File name to contain the set in DIMACS format. See http://bit.ly/dimcasf")
    parser.add_argument("-g", "--output-graph-file", type=str, help="Output graph file in Graphviz format")
    parser.add_argument("-s", "--output-solution-file", action="store_true", help="Output solution file.")
    parser.add_argument("-ns", "--no-stats", help="Short concise output. No stats about unique numbers and other information. This will disable the global database option.", action="store_true")
    parser.add_argument("-t", "--threads", type=int, help="Number of threads. Value 1 means no multithreading, 0 means max concurrent threads on the machine. This option will implicitly enable the global DB.", default=1)
    parser.add_argument("-e", "--exit-upon-solving", help="Exit whenever a solution is found.", action="store_true")
    parser.add_argument("-verify", "--verify", help="Verify the solution at the end, if any.", action="store_true")
    parser.add_argument("-rdb", "--use-runtime-db", help="Use database for set lookup in table established only for the current cnf", action="store_true")
    parser.add_argument("-gdb", "--use-global-db", help="Use database for set lookup in global sets table", action="store_true")
    parser.add_argument("-gnm", "--gdb-no-mem", help="Don't load hashes from global DB into memory. Use this only if gdb gets huge and doesn't fit in memory. (slower)", action="store_true")
    parser.add_argument("-m", "--mode", help=textwrap.dedent('''Solution mode. It's either:
    [LO condition is where all variables appear in the ascending order]
    flo: Linearily ordered, where all nodes in the tree will be brought to L.O. condition. (default)
    flop: Linearily ordered, where all nodes in the tree will be brought to L.O. condition, clauses are sorted per size.
    lo: Linearily ordered, where only the root node will be brought to L.O. condition while the rest of the nodes will be brought to L.O.U. condition.
    lou: Linearily ordered universal, where all nodes in the tree will be brought to L.O.U. condition.
    normal: Don't use Nasser's algorithm and use a normal evaluation of the set with no preprocessing steps except for ascending sorting of vars within each clause.
            '''), choices=['flo', 'flop', 'lo', 'lou', 'normal'], default="flo")
    parser.add_argument('--version', action='version', version='%(prog)s ') # can use GitPython to automatically get latest tag here

    # The algorithm
    # --------------
    # START:
    # if FLOP:
    #     place unit clauses first
    # rename vars
    # sort within clauses
    # if FLO or FLOP or (LO root node only):
    #     sort clauses()

    # check if it meets LO condition, if not go to step START


    args = parser.parse_args()

    if args.quiet:
        logger.setLevel(logging.CRITICAL)
    
    # if threads is set, enable gdb
    # A long note regarding multithreading and gdb:
    #---------------------------------------------
    
    # When we solve a problem using multithreading/processes, each thread will process a subtree. 
    # All thread should check a common storage (gdb in this case) to check for common nodes. This check
    # will avoid processing of a subtree that's been already processed by another thread. This is a major 
    # contribution of the theory behind the solution of course. However, in order to achieve that, each 
    # thread need to check the DB for "every node" it processes. Let's call the time required for this 
    # operation D time, whereas if the thread the time required to process the node is P time. 
    # So without the checking of the common node, the thread will spend P x n (n is # of nodes in the tree)
    # to process the tree, whereas with common DB, it'll need (P + D) x n` (where n` is number of unique nodes)
    # So the idea here is that in order to make sense to have the DB of common nodes, the cost of processing the 
    # common subtree must be larger than D x n`. In other words, P x n`` > D x n`. Where n`` is the size of the 
    # common subtree(s). 
    # That being said, it's been found that almost always, the common subtrees are far less than unique ones. 
    # Also, for most of nodes, especially on LOU mode where bringing the node to LO condition requires only one
    # iteration, P is very small that it's less than D time. 
    # This concludes the fact that P x n`` < D x n` and the cost of having common storage "in the current implementation"
    # is bad.
    # Recommendations:
    # - We need another common nodes storage different than postgres when checking the existence of the node is less than processing it.
    # - The above conclution is valid by experiment for LOU, and partially for LO. We need to do more experiemnts for LO, FLO and FLOP 
    # where processing a node can take longer than LOU to draw the same conclusion, otherwise the flag to use gdb can be automatically set
    # with these modes and problem size.
    # - For now, let's disable the automatic activation of gdb with multithreading.
    #
    # otherwise if we want to use gdb, we can explicitly set the commandline option to do so.

    # if args.threads > 1:
    #     args.use_global_db = True


    if args.threads < 0:
        print("Option -t must be a positive number.")
        parser.print_help()
        sys.exit(3)

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

    # only use -gnm if -gdb is set
    if args.gdb_no_mem and not args.use_global_db:
        parser.error('-gnm/--gdb-no-mem MUST be used with -gdb/--use-global-db option')


    if args.verbos:
        logger.setLevel(logging.INFO)
    elif args.very_verbos:
        logger.setLevel(logging.DEBUG)
    elif args.quiet:
        logger.setLevel(logging.CRITICAL)

    Main(args)
    
    print('script took %.3f seconds' % (time.time() - start_time))

