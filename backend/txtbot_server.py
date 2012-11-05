from flask import Flask, request, redirect, g
from threading import Thread
import twilio.twiml, requests, json, time, sqlite3

DATABASE = "messages.db"
FIREBASE = "https://gamma.firebase.com/overheard.json"
app = Flask(__name__)

blacklist = ["nichols"]
min_length = 3

def is_valid(s):
  return all(ord(c) < 128 for c in s) \
     and not any(w in s.lower() for w in blacklist) \
     and len(s) >= min_length

@app.route("/", methods=['GET', 'POST'])
def handle_sms():
  # receive and handle incoming data
  txt = request.values.get('Body', None)
  if not txt:
    return "No data received!"
  reply = get_entry()
  # create a thead to add it (so we don't timeout)
  t = Thread(target=add_entry, args=(txt, request.values.get('From', None),))
  t.start()
  # form response
  resp = twilio.twiml.Response()
  if reply:
    resp.sms(reply)
  return str(resp)

@app.route("/count", methods=['GET', 'POST'])
def serve_count():
  db = sqlite3.connect(DATABASE)
  cur = db.cursor()
  cur.execute("select count(*) from entries")
  count = str(cur.fetchone()[0])
  db.close()
  return count

def get_entry():
  db = sqlite3.connect(DATABASE)
  cur = db.cursor()
  # check if table has entries
  cur.execute("select case when exists (select * from entries limit 1) then 1 else 0 end")
  if not int(cur.fetchone()[0]):
    return None
  # get a random entry
  cur.execute("select text from entries order by random() limit 1")
  r = str(cur.fetchone()[0])
  db.close()
  return r

def add_entry(entry, origin):
  timestamp = round(time.time())
  # get DB in this thread context
  db = sqlite3.connect(DATABASE)
  cur = db.cursor()
  # if exists in sqlite db, exit
  cur.execute("select case when exists (select * from entries where text=? limit 1) then 1 else 0 end", [entry])
  if int(cur.fetchone()[0]) or not is_valid(entry):
    return
  # add to sqlite DB
  db.execute('insert into entries (text, origin, time) values (?, ?, ?)',
               [entry, origin, timestamp])
  db.commit()
  # add to Firebase
  payload = {'time': timestamp, 'origin': origin, 'body': entry}
  requests.post(FIREBASE, data=json.dumps(payload))

  # close DB
  db.close()

if __name__ == "__main__":
  app.run(host="0.0.0.0", port=6288, debug=True)