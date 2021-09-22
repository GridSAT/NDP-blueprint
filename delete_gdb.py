# delete_gdb.py
#
# Copyright © 2016 - 2021 EasyXPS, Inc. <info@easyxps.com>
# All rights reserved.
# Simply Efficient. is a trademark of EasyXPS, Inc.
#

from configs import *
from DbAdaptor import DbAdapter

db = DbAdapter()
#db.gs_drop_all()
tables = ["globalsetstable_lou", "globalsetstable_lo", "globalsetstable_flo", "globalsetstable_flop"]

if len(sys.argv) > 1 and sys.argv[1] in tables:
    db.gs_drop_table(sys.argv[1])
else:
    print(f"Please provide table name from {tables}")
