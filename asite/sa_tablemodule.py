# LZY custom table definitions with function to create it
#     using direct django.db.connection

lzy_table00_def = """
CREATE TABLE lzy_table00 (
    version TEXT,
    notes   TEXT
);
"""

lzy_table01_def = """
"""

from django.db import connection

def lzy_custom_sql(sql_str):
    # Execute an sql and return the result
    with connection.cursor() as cursor:
        cursor.execute(sql_str)


def lzy_open_txtfile(filename):
    # Open a textfile, return the whole content as string
    # No check on filesize! Only use to read small textfile
    read_data = "[Empty]"
    with open(filename, 'rt', encoding="utf-8") as f:
        read_data = f.read()
    return read_data
