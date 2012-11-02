from flask import Flask, request, redirect, g
import twilio.twiml, requests, json, time, sqlite3

DATABASE = "messages.db"
FIREBASE = "https://gamma.firebase.com/overheard.json"
app = Flask(__name__)

@app.before_request
def before():
  g.db = sqlite3.connect(DATABASE)

@app.teardown_request
def teardown(exception):
  g.db.close()

@app.route("/", methods=['GET', 'POST'])
def handle_sms():
  # receive and handle incoming data
  txt = request.values.get('Body', None)
  if not txt:
    return "No data received!"
  reply = get_entry()
  add_entry(txt, request.values.get('From', None))
  # form response
  resp = twilio.twiml.Response()
  if reply:
    resp.sms(reply)
  return str(resp)

def get_entry():
  cur = g.db.cursor()
  # check if table has entries
  cur.execute("select case when exists (select * from entries limit 1) then 1 else 0 end")
  if not int(cur.fetchone()[0]):
    return None
  # get a random entry
  cur.execute("select text from entries order by random() limit 1")
  return str(cur.fetchone()[0])

def add_entry(entry, origin):
  timestamp = round(time.time())
  cur = g.db.cursor()
  # if exists in sqlite db, exit
  cur.execute("select case when exists (select * from entries where text=? limit 1) then 1 else 0 end", [entry])
  if int(cur.fetchone()[0]):
    return
  # add to sqlite DB
  g.db.execute('insert into entries (text, origin, time) values (?, ?, ?)',
               [entry, origin, timestamp])
  g.db.commit()
  # add to Firebase
  payload = {'time': timestamp, 'origin': origin, 'body': entry}
  requests.post(FIREBASE, data=json.dumps(payload))

if __name__ == "__main__":
  app.run(host="0.0.0.0", port=6288, debug=True)