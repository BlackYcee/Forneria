import sqlite3

conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cur.fetchall()
print('tables:', tables)
cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name LIKE 'pos_%';")
pos = cur.fetchall()
print('pos_tables:')
for name, sql in pos:
    print(' -', name)
    print(sql)
conn.close()
