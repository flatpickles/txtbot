from flask import Flask, request, redirect, g, jsonify
from functools import wraps
import twilio.twiml, requests, time, sqlite3

### GLOBAL INITIALIZATIONS ETC ###

DATABASE = "messages.db"
app = Flask(__name__)

blacklist = ["nichols"]
min_length = 3

# allow jsonP
def jsonp(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            data = str(func(*args, **kwargs).data)
            content = str(callback) + '(' + data + ')'
            mimetype = 'application/javascript'
            return current_app.response_class(content, mimetype=mimetype)
        else:
            return func(*args, **kwargs)
    return decorated_function

### REQUEST METHODS ###

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
  # add it
  add_entry(txt, request.values.get('From', None))
  # form response
  resp = twilio.twiml.Response()
  if reply:
    resp.sms(reply)
  return str(resp)

@app.route("/count", methods=['GET', 'POST'])
@jsonp
def serve_count():
  cur = g.db.cursor()
  cur.execute("select count(*) from entries")
  count = int(cur.fetchone()[0])
  return jsonify({'count': count})

@app.route("/entries", methods=['GET', 'POST'])
@jsonp
def serve_messages():
  # params
  to_get = int(request.values.get('n', '10'))
  lower_time_bound = int(request.values.get('after', '0'))
  upper_time_bound = int(request.values.get('before', '999999999999'))

  # get data
  cur = g.db.cursor()
  data = {}
  cur.execute("select * from entries where time > ? and time < ? order by time desc limit ?", [lower_time_bound, upper_time_bound, to_get])
  vals = cur.fetchall()

  # parse data
  for row in vals:
    data[row[0]] = {
      'text': row[1],
      'origin': row[2],
      'time': row[3]
    }

  # return data
  return jsonify(data)

### HELPER METHODS ###

def is_valid(s):
  return all(ord(c) < 128 for c in s) \
     and not any(w in s.lower() for w in blacklist) \
     and len(s) >= min_length

def get_entry():
  cur = g.db.cursor()
  # check if table has entries
  cur.execute("select case when exists (select * from entries limit 1) then 1 else 0 end")
  if not int(cur.fetchone()[0]):
    return None
  # get a random entry
  cur.execute("select text from entries order by random() limit 1")
  r = str(cur.fetchone()[0])
  return r

def add_entry(entry, origin):
  timestamp = round(time.time())
  cur = g.db.cursor()
  # if exists in sqlite db, exit
  cur.execute("select case when exists (select * from entries where text=? limit 1) then 1 else 0 end", [entry])
  if int(cur.fetchone()[0]) or not is_valid(entry):
    return
  # add to sqlite DB
  g.db.execute('insert into entries (text, origin, time) values (?, ?, ?)',
               [entry, origin, timestamp])
  g.db.commit()

### MAIN ###

if __name__ == "__main__":
  app.run(host="0.0.0.0", port=6288, debug=True)