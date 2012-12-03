from twilio.rest import TwilioRestClient
import time

def is_valid(s, db, roulette):
  # anything goes with roulette
  if roulette:
    return True
  # check if exists in sqlite db
  cur = db.cursor()
  cur.execute("select case when exists (select * from entries where text=? limit 1) then 1 else 0 end", [entry])
  duplicate = int(cur.fetchone()[0])
  # return proper value
  return not duplicate \
      and all(ord(c) < 128 for c in s) \
      and not any(w in s.lower() for w in blacklist) \
      and len(s) >= min_length

def get_recent(origin, db):
  cur = db.cursor()
  # check if table has entries
  cur.execute("select case when exists (select * from entries limit 1) then 1 else 0 end")
  if not int(cur.fetchone()[0]):
    return None
  # get the most recent entry not from origin
  cur.execute("select text,origin from entries where origin<>? order by id desc limit 1", [origin])
  e = cur.fetchone()
  return None if not e else {'text': e[0], 'origin': e[1]}

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

def add_entry(entry, origin, db, roulette):
  timestamp = round(time.time())
  cur = db.cursor()
  if not is_valid(entry, db, roulette):
    return
  # add to sqlite DB
  db.execute('insert into entries (text, origin, time) values (?, ?, ?)',
               [entry, origin, timestamp])
  db.commit()

def send_sms(txt, destination):
  creds_file = open("creds")
  creds = creds_file.read().split("\n")
  creds_file.close()
  client = TwilioRestClient(creds[0], creds[1])
  message = client.sms.messages.create(to=destination, from_=creds[2], body=txt)
  return message