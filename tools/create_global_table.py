import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
#sys.path.append('..')
import DbAdaptor

table_name = "GlobalSetsTable"
table_name = "queue_" + "4fb7aa4e244a8b3f3d2f0f139afe0fbf8d4e507e"
db_adaptor = DbAdaptor.DbAdapter()
db_adaptor.gs_create_table(table_name)