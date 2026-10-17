import sqlite3
from pathlib import Path
DEFAULT_DB = "data/bi_events.sqlite"

def connect(db_path=DEFAULT_DB):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn=sqlite3.connect(db_path)
    conn.execute("""CREATE TABLE IF NOT EXISTS events (
      event_id INTEGER PRIMARY KEY, event_time TEXT NOT NULL, category TEXT NOT NULL,
      campus TEXT NOT NULL, amount REAL NOT NULL)""")
    conn.commit(); return conn

def reset_db(db_path=DEFAULT_DB):
    c=connect(db_path); c.execute("DELETE FROM events"); c.commit(); c.close()

def upsert_events(rows, db_path=DEFAULT_DB):
    c=connect(db_path)
    c.executemany("""INSERT INTO events(event_id,event_time,category,campus,amount)
      VALUES(:event_id,:event_time,:category,:campus,:amount)
      ON CONFLICT(event_id) DO UPDATE SET event_time=excluded.event_time,
      category=excluded.category,campus=excluded.campus,amount=excluded.amount""", rows)
    c.commit(); count=c.execute("SELECT COUNT(*) FROM events").fetchone()[0]; c.close()
    return count

def summary(db_path=DEFAULT_DB):
    c=connect(db_path)
    total, amount=c.execute("SELECT COUNT(*),COALESCE(SUM(amount),0) FROM events").fetchone()
    rows=c.execute("SELECT category,COUNT(*),ROUND(AVG(amount),2) FROM events GROUP BY category ORDER BY category").fetchall()
    c.close()
    return {"total_events":total,"total_amount":round(amount,2),
      "by_category":[{"category":x,"count":n,"average_amount":avg} for x,n,avg in rows]}
