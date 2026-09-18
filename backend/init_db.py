import psycopg2
import os

DB_URI = os.environ.get("DATABASE_URL", "postgresql://postgres:YOUR_ACTUAL_PASSWORD@db.example:5432/postgres")

with open('create_tables.sql') as f:
    sql = f.read()

conn = psycopg2.connect(DB_URI)
cur = conn.cursor()
cur.execute(sql)
conn.commit()
cur.close()
conn.close()
print('Tables created')
