import os, argparse, sys
import sqlite3

arglist = {'key' : 'key', 'user' : 'username', 'pwd' : 'password'}
auth_db_name = 'auth_info.db'

parser = argparse.ArgumentParser()
for item in arglist.keys():
    parser.add_argument('--' + item)

args = parser.parse_args()

create_table = False if os.path.isfile(auth_db_name) else True
conn = sqlite3.connect(auth_db_name)
conn.row_factory = sqlite3.Row
db = conn.cursor()

if create_table:
    db.execute('CREATE TABLE main (key VARCHAR(50) PRIMARY KEY, username VARCHAR(50), password VARCHAR(50))')

if args.key:
    args = {arglist[arg] : getattr(args, arg) for arg in vars(args) if getattr(args, arg)}
    param_list = lambda num, str='?': ','.join([str]*num)
    db.execute('INSERT OR REPLACE INTO main ({}) VALUES ({})'.format(', '.join(args.keys()), param_list(len(args))), args.values())
    conn.commit()
else:
    db.execute('SELECT * FROM main')
    for row in db.fetchall():
        print(dict(row))
conn.close()


