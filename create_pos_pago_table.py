import sqlite3

sql = '''
CREATE TABLE IF NOT EXISTS pos_pago (
    id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    monto decimal NOT NULL,
    metodo varchar(3) NOT NULL,
    referencia varchar(50),
    fecha datetime NOT NULL,
    venta_id integer NOT NULL,
    FOREIGN KEY(venta_id) REFERENCES pos_venta(id)
);
'''

conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()
cur.executescript(sql)
conn.commit()
print('pos_pago table created or already existed')
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pos_pago'")
print('exists:', cur.fetchall())
conn.close()
