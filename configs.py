import logging

MIN_LITERAL = 1

# input file format
INPUT_SL = 1
INPUT_SLF = 2
INPUT_DIMACS = 3

# database
DB_HOST="localhost"
DB_PORT=5432
DB_NAME="patternsolvers"
DB_USER="mesaleh"
DB_PASSWORD="951753saleh"

# constants
NODE_UNIQUE = 0
NODE_REDUNDANT = 1
NODE_EVALUATED = 2


# logging
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logger = logging.getLogger('NSS')
logger.setLevel(logging.WARNING)

# util functions
def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)
