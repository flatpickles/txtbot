from util import *

from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

from flask import Flask, request, redirect, g, jsonify
from functools import wraps
from time import gmtime, strftime
import twilio.twiml, requests, sqlite3, json, hashlib

### GLOBAL INITIALIZATIONS ETC ###

DATABASE = "messages.db"
ROULETTE_DATABASE = "roulette.db"
JOIN_TIME = 10
CONCAT_SMS_LEN = 153
app = Flask(__name__)

roulette = True
offset = 3 # don't publish the most recent texts
blacklist = ["nichols"]
min_length = 3

cred_file = open("creds")
twilio_sid = cred_file.readline().replace('\n', '')
cred_file.close()

voice_output = """
  Thanks for calling text bot! When you send a text message to this number,
  it will be forwarded anonymously to whoever texted directly before you.
  You will then receive the next person's message. So hang up, give it a shot,
  and see what happens.
  """

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
  # make sure it's a valid request (from Twilio)
  if request.values.get('AccountSid', None) != twilio_sid:
    print "%s Received invalid/non-Twilio request at root" % get_time_s()
    return "Invalid request."
  # carry on
  global roulette
  # receive and handle incoming data
  txt = request.values.get('Body', None)
  if not txt:
    print "%s Received malformed request at root" % get_time_s()
    return "No data received"
  origin = request.values.get('From', None)
  resp = twilio.twiml.Response()
  # reject if blocked
  if origin and is_blocked(origin, g.db):
    print "%s Received text from blocked number: %s" % (get_time_s(), origin)
    resp.sms("Your number has been blocked on account of shenanigans. Please email support@txtbot.me if you've got beef.")
    return str(resp)
  # yup
  reply = get_recent(origin, g.db) if roulette else get_random()
  # add it, merge if necessary
  if new_message(txt, origin): add_entry(txt, origin, g.db, roulette)
  check_top()
  # form response
  if reply:
    if roulette:
      resp.sms(txt, to=reply['origin'])
    else:
      resp.sms(reply)
  print "%s Received SMS: \"%s\", returning with response" % (get_time_s(), txt.encode('ascii', 'ignore'))
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
  if request.values.has_key('after') and request.values.has_key('before'):
    to_get = max(to_get, upper_bound - lower_bound)
  upper_bound = min(latest - offset + 1, upper_bound)

  # get data
  data = {}
  cur.execute("select * from entries where id > ? and id < ? order by id desc limit ?", [lower_bound, upper_bound, to_get])

  # parse data
  for row in cur.fetchall():
    # hash the number for anonymity
    h = hashlib.sha1()
    h.update(str(row[2]))
    color = '#' + str(h.hexdigest()[-6:])

    data[row[0]] = {
      'text': row[1],
      'color': color,
      'time': row[3]
    }

  # return data
  print "%s Returning request for entries" % get_time_s()
  return jsonify(data)

@app.route("/best", methods=['GET', 'POST'])
@jsonp
def serve_best():
  # get params
  to_get = int(request.values.get("n", "5"))
  before = int(request.values.get("before", "-1"))
  # get data
  data = {}
  cur = g.db.cursor()
  if before == -1:
    cur.execute("select * from best order by id desc limit ?", [to_get])
  else:
    cur.execute("select * from best where id<? order by id desc limit ?", [before, to_get])
  # parse data
  for row in cur.fetchall():
    data[row[0]] = {
      'first': row[1],
      'last': row[2]
    }
  # return data
  print "%s Returning request for best" % get_time_s()
  return jsonify(data)

@app.route("/favicon.ico", methods=['GET', 'POST'])
def favicon():
  # avoid 404s with direct requests, return empty
  return ""

@app.route("/voice", methods=['GET', 'POST'])
def voice_response():
  print "%s Receiving a phone call?!?!" % get_time_s()
  resp = twilio.twiml.Response()
  resp.say(voice_output, language="en-gb", voice="female")
  return str(resp)

### HELPER METHODS ###

def new_message(txt, origin):
  cur = g.db.cursor()
  cur.execute("select text,origin from entries order by id desc limit 1")
  last = cur.fetchone()
  return not (last[0] == txt and str(last[1]) == origin)

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

def get_time_s():
  return strftime("[%m/%d %H:%M]", gmtime())

# checks for possible multiple messages from the same sender w/in a second
def check_top():
  cur = g.db.cursor()
  cur.execute("select * from entries order by id desc limit 2")
  last = cur.fetchall()
  if last[0][2] == last[1][2] \
      and len(last[1][1]) % CONCAT_SMS_LEN == 0 \
      and last[1][3] + JOIN_TIME >= last[0][3]:
    return cat_entries(last[1][0], last[0][0], g.db)
  return False

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
