import sqlite3

conn = sqlite3.connect('cultura.db')
c = conn.cursor()

# Create the submissions table
c.execute('''
    CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        country TEXT NOT NULL,
        problem TEXT NOT NULL,
        solution TEXT NOT NULL,
        advice TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
''')

conn.commit()
conn.close()
print("Database and table created successfully.")
