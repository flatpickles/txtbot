import sqlite3, sys
ROULETTE_DATABASE = "roulette.db"

# concatenates the "text" field of two entries, stores back in id1
def cat_entries(id1, id2, db):
  cur = db.cursor()
  cur.execute("select * from entries where id=?", [id2])
  e2 = cur.fetchone()
  cur.execute("select * from entries where id=?", [id1])
  e1 = cur.fetchone()
  if not (e2 and e1): return False
  db.execute('delete from entries where id=? or id=?', [id1, id2])
  db.execute('insert into entries (id, text, origin, time) values (?, ?, ?, ?)',
               [e2[0], e1[1] + e2[1], e2[2], e2[3]])
  db.commit()
  return True

if __name__ == "__main__":
  db = sqlite3.connect(ROULETTE_DATABASE)
  if len(sys.argv) > 1 and sys.argv[1] == "cat":
    if len(sys.argv) == 4:
      print "concatenating %s and %s" % (sys.argv[2], sys.argv[3])
      if cat_entries(int(sys.argv[2]), int(sys.argv[3]), db):
        print "success"
      else:
        print "no dice"
    else:
      print "arguments invalid for cat"
  else:
    print "no valid arguments specified"
  # cat_entries(3, 1, db)
  db.close()