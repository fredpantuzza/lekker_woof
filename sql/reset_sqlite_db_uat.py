import sqlite3

DB_FILE_NAME = 'lekker_woof.db'

SCRIPTS = ['reset_uat.sql']

for script_filename in SCRIPTS:
    with open(script_filename, 'r') as sql_file:
        sql_script = sql_file.read()

    db = sqlite3.connect(DB_FILE_NAME)
    cursor = db.cursor()
    for sql_command in sql_script.split('\n\n'):
        print('--------------------------------------')
        print('Running SQL command:')
        print(sql_command)
        cursor.executescript(sql_command)
        print('Done!')
        print('--------------------------------------')
    db.commit()
    db.close()
