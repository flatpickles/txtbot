from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

from flask import Flask, request, redirect, g, jsonify
from functools import wraps
from time import gmtime, strftime
import twilio.twiml, requests, time, sqlite3, json, hashlib

### GLOBAL INITIALIZATIONS ETC ###

DATABASE = "messages.db"
ROULETTE_DATABASE = "roulette.db"
app = Flask(__name__)

roulette = True
offset = 3 # don't publish the most recent texts
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
  if hasattr(g, 'db'):
    g.db.close()

@app.route("/", methods=['GET', 'POST'])
def handle_sms():
  global roulette
  # receive and handle incoming data
  txt = request.values.get('Body', None)
  if not txt:
    print "%s Received malformed request at root" % get_time_s()
    return "No data received"
  origin = request.values.get('From', None)
  reply = get_recent(origin) if roulette else get_random()
  # add it, merge if necessary
  add_entry(txt, origin)
  check_top()
  # form response
  resp = twilio.twiml.Response()
  if reply:
    if roulette:
      resp.sms(txt, to=reply['origin'])
    else:
      resp.sms(reply)
  print "%s Received SMS: \"%s\", returning with response" % (get_time_s(), txt)
  return str(resp)

@app.route("/text_count", methods=['GET', 'POST'])
@jsonp
def serve_text_count():
  cur = g.db.cursor()
  cur.execute("select count(*) from entries")
  count = int(cur.fetchone()[0])
  print "%s Returning request for text_count" % get_time_s()
  return jsonify({'count': count})

@app.route("/number_count", methods=['GET', 'POST'])
@jsonp
def serve_number_count():
  cur = g.db.cursor()
  cur.execute("select count(distinct origin) from entries")
  count = int(cur.fetchone()[0])
  print "%s Returning request for number_count" % get_time_s()
  return jsonify({'count': count})

@app.route("/entries", methods=['GET', 'POST'])
@jsonp
def serve_messages():
  cur = g.db.cursor()
  # most recent ID
  cur.execute("select id from entries order by id desc limit 1");
  latest = int(cur.fetchone()[0])

  # params
  to_get = int(request.values.get('n', '10'))
  lower_bound = int(request.values.get('after', '-1'))
  upper_bound = int(request.values.get('before', str(latest + 1)))
  upper_bound = min(latest - offset + 1, upper_bound)

  # get data
  data = {}
  cur.execute("select * from entries where id > ? and id < ? order by id desc limit ?", [lower_bound, upper_bound, to_get])
  vals = cur.fetchall()

  # parse data
  for row in vals:
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
  print "%s Returning request for entries" % get_time_s()
  return jsonify(data)

@app.route("/favicon.ico", methods=['GET', 'POST'])
def favicon():
  # avoid 404s with direct requests, return empty
  return ""

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
  cur.execute("select text,origin from entries where origin<>? order by id desc limit 1", [origin])
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

def get_time_s():
  return strftime("[%m/%d %H:%M]", gmtime())

# checks for possible multiple messages from the same sender w/in a second
def check_top():
  cur = g.db.cursor()
  cur.execute("select id, origin, time from entries order by id desc limit 2")
  last = cur.fetchall()
  if last[0][1] == last[1][1] and last[1][2] + 1 >= last[0][2]:
    return cat_entries(last[1][0], last[0][0])
  return False

# concatenates the "text" field of two entries, stores back in id1
def cat_entries(id1, id2):
  cur = g.db.cursor()
  cur.execute("select text from entries where id=?", [id2])
  t2 = cur.fetchone()
  if t2: t2 = t2[0]
  cur.execute("select * from entries where id=?", [id1])
  e1 = cur.fetchone()
  if not (t2 and e1): return False
  g.db.execute('delete from entries where id=? or id=?', [id1, id2])
  g.db.execute('insert into entries (id, text, origin, time) values (?, ?, ?, ?)',
               [e1[0], e1[1] + t2, e1[2], e1[3]])
  g.db.commit()
  return True

### MAIN ###

if __name__ == "__main__":
  try:
    print "%s ------------ BEGIN ------------" % get_time_s()
    # run as Tornado server
    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(6288)
    IOLoop.instance().start()
  except KeyboardInterrupt:
    print "\n%s ------- KILLED BY USER --------" % get_time_s()
