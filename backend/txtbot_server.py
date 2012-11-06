from flask import Flask, request, redirect, g, jsonify
from functools import wraps
import twilio.twiml, requests, time, sqlite3, json, hashlib

### GLOBAL INITIALIZATIONS ETC ###

DATABASE = "messages.db"
ROULETTE_DATABASE = "roulette.db"
app = Flask(__name__)

roulette = True
offset = 1 # delay 3 texts in response
blacklist = ["nichols"]
min_length = 3

# allow jsonP
# mostly via https://gist.github.com/1094140
def jsonp(f):
  global app
  @wraps(f)
  def decorated_function(*args, **kwargs):
    callback = request.args.get('callback', False)
    if callback:
      content = str(callback) + '(' + str(f(*args,**kwargs).data) + ')'
      return app.response_class(content, mimetype='application/javascript')
    else:
      return f(*args, **kwargs)
  return decorated_function

### REQUEST METHODS ###

@app.before_request
def before():
  global roulette
  if roulette:
    g.db = sqlite3.connect(ROULETTE_DATABASE)
  else:
    g.db = sqlite3.connect(DATABASE)

@app.teardown_request
def teardown(exception):
  g.db.close()

@app.route("/", methods=['GET', 'POST'])
def handle_sms():
  global roulette
  # receive and handle incoming data
  txt = request.values.get('Body', None)
  if not txt:
    return "No data received!"
  origin = request.values.get('From', None)
  reply = get_recent(origin) if roulette else get_random()
  # add it
  add_entry(txt, origin)
  # form response
  resp = twilio.twiml.Response()
  if reply:
    if roulette:
      resp.sms(txt, to=reply['origin'])
    else:
      resp.sms(reply)
  return str(resp)

@app.route("/text_count", methods=['GET', 'POST'])
@jsonp
def serve_text_count():
  cur = g.db.cursor()
  cur.execute("select count(*) from entries")
  count = int(cur.fetchone()[0])
  return jsonify({'count': count})

@app.route("/number_count", methods=['GET', 'POST'])
@jsonp
def serve_number_count():
  cur = g.db.cursor()
  cur.execute("select count(distinct origin) from entries")
  count = int(cur.fetchone()[0])
  return jsonify({'count': count})

@app.route("/entries", methods=['GET', 'POST'])
@jsonp
def serve_messages():
  # params
  to_get = int(request.values.get('n', '10'))
  lower_bound = int(request.values.get('after', '-1'))
  upper_bound = int(request.values.get('before', '999999999999'))

  # get data
  cur = g.db.cursor()
  data = {}
  cur.execute("select * from entries where id > ? and id < ? order by time desc limit ?", [lower_bound, upper_bound, to_get + offset])
  vals = cur.fetchall()

  # parse data
  for row in vals[offset:]:
    # hash the number for anonymity
    h = hashlib.sha1()
    h.update(str(row[2]))
    color = '#' + str(h.hexdigest()[:6])

    data[row[0]] = {
      'text': row[1],
      'color': color,
      'time': row[3]
    }

  # return data
  return jsonify(data)

### HELPER METHODS ###

def is_valid(s):
  global roulette
  return roulette \
      or all(ord(c) < 128 for c in s) \
      and not any(w in s.lower() for w in blacklist) \
      and len(s) >= min_length

def get_random():
  cur = g.db.cursor()
  # check if table has entries
  cur.execute("select case when exists (select * from entries limit 1) then 1 else 0 end")
  if not int(cur.fetchone()[0]):
    return None
  # get a random entry
  cur.execute("select text from entries order by random() limit 1")
  r = str(cur.fetchone()[0])
  return r

def get_recent(origin):
  cur = g.db.cursor()
  # check if table has entries
  cur.execute("select case when exists (select * from entries limit 1) then 1 else 0 end")
  if not int(cur.fetchone()[0]):
    return None
  # get the most recent entry not from origin
  cur.execute("select text,origin from entries where origin<>? order by time desc limit 1", [origin])
  e = cur.fetchone()
  return None if not e else {'text': e[0], 'origin': e[1]}

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