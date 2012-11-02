import requests, json, sqlite3

DATABASE = "messages.db"
FIREBASE = "https://gamma.firebase.com/overheard"

db = None

def db_connect():
  global db
  db = sqlite3.connect(DATABASE)

def db_shutdown():
  global db
  db.close()

def remove_entry(with_text):
  global db
  # remove all in firebase
  fb_nodes = firebase_find(with_text)
  for n in fb_nodes:
    requests.delete(FIREBASE + "/" + n + ".json")
  # remove all in sqlite
  cur = db.cursor()
  cur.execute("select count(*) from entries where text like '%?%'", with_text)
  db_num = int(cur.fetchone()[0])
  cur.execute("delete from entries where text like '%?%'", with_text)
  return [len(fb_nodes), db_num]

def firebase_find(text):
  returns = []
  r = requests.get(FIREBASE + ".json")
  j = json.loads(r.text)
  for k, v in j.iteritems():
    if text in v[u'body']:
      returns.append(k)
  return returns