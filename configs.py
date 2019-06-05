import logging

MIN_LITERAL = 1

# input file format
INPUT_SL = 1
INPUT_SLF = 2
INPUT_DIMACS = 3



logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logger = logging.getLogger('NSS')
logger.setLevel(logging.CRITICAL)