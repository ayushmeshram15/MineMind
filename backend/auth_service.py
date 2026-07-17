import hashlib, hmac, json, os, secrets, sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from fastapi import Header, HTTPException

DB_PATH = Path(os.getenv('MINEMIND_DB_PATH', Path(__file__).with_name('minemind.db')))
TOKEN_TTL_HOURS = 72

def _db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
    return con

def init_db():
    with _db() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,email TEXT NOT NULL UNIQUE,password_hash TEXT NOT NULL,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS workspaces(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,slug TEXT NOT NULL UNIQUE,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS memberships(user_id INTEGER NOT NULL,workspace_id INTEGER NOT NULL,role TEXT NOT NULL DEFAULT 'OPERATOR',PRIMARY KEY(user_id,workspace_id),FOREIGN KEY(user_id) REFERENCES users(id),FOREIGN KEY(workspace_id) REFERENCES workspaces(id));
        CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY,user_id INTEGER NOT NULL,workspace_id INTEGER NOT NULL,expires_at TEXT NOT NULL,created_at TEXT NOT NULL,FOREIGN KEY(user_id) REFERENCES users(id),FOREIGN KEY(workspace_id) REFERENCES workspaces(id));
        CREATE TABLE IF NOT EXISTS ingestions(id INTEGER PRIMARY KEY AUTOINCREMENT,workspace_id INTEGER NOT NULL,name TEXT NOT NULL,row_count INTEGER NOT NULL,columns_json TEXT NOT NULL,sample_json TEXT NOT NULL,status TEXT NOT NULL,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS vision_events(id INTEGER PRIMARY KEY AUTOINCREMENT,workspace_id INTEGER NOT NULL,event_id TEXT NOT NULL,camera_id TEXT NOT NULL,severity TEXT NOT NULL,title TEXT NOT NULL,description TEXT NOT NULL,confidence REAL NOT NULL,detections_json TEXT NOT NULL,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS alert_reads(workspace_id INTEGER NOT NULL,alert_key TEXT NOT NULL,read_at TEXT NOT NULL,PRIMARY KEY(workspace_id,alert_key));
        ''')

def _now(): return datetime.now(timezone.utc)
def _hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 210000).hex()
    return f'{salt}${digest}'
def _verify(password, stored):
    salt, digest = stored.split('$',1)
    return hmac.compare_digest(_hash(password,salt).split('$',1)[1], digest)
def _slug(name):
    base=''.join(ch.lower() if ch.isalnum() else '-' for ch in name).strip('-') or 'mine-workspace'
    return f'{base[:40]}-{secrets.token_hex(3)}'
def _session(c,user_id,workspace_id):
    token=secrets.token_urlsafe(32); now=_now(); exp=now+timedelta(hours=TOKEN_TTL_HOURS)
    c.execute('INSERT INTO sessions VALUES(?,?,?,?,?)',(token,user_id,workspace_id,exp.isoformat(),now.isoformat()))
    return token

def signup(payload):
    name=(payload.get('name') or '').strip(); email=(payload.get('email') or '').strip().lower(); password=payload.get('password') or ''; mine=(payload.get('mine') or '').strip()
    if len(name)<2 or '@' not in email or len(password)<6 or len(mine)<2: raise HTTPException(400,'Name, valid email, 6+ character password and mine workspace are required')
    now=_now().isoformat()
    try:
        with _db() as c:
            uid=c.execute('INSERT INTO users(name,email,password_hash,created_at) VALUES(?,?,?,?)',(name,email,_hash(password),now)).lastrowid
            wid=c.execute('INSERT INTO workspaces(name,slug,created_at) VALUES(?,?,?)',(mine,_slug(mine),now)).lastrowid
            c.execute('INSERT INTO memberships(user_id,workspace_id,role) VALUES(?,?,?)',(uid,wid,'ADMIN'))
            token=_session(c,uid,wid)
    except sqlite3.IntegrityError: raise HTTPException(409,'An account with this email already exists')
    return session_payload(token)

def login(payload):
    email=(payload.get('email') or '').strip().lower(); password=payload.get('password') or ''
    with _db() as c:
        u=c.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
        if not u or not _verify(password,u['password_hash']): raise HTTPException(401,'Invalid email or password')
        m=c.execute('SELECT workspace_id FROM memberships WHERE user_id=? ORDER BY workspace_id LIMIT 1',(u['id'],)).fetchone()
        token=_session(c,u['id'],m['workspace_id'])
    return session_payload(token)

def current_session(authorization: str = Header(default='')):
    if not authorization.startswith('Bearer '): raise HTTPException(401,'Authentication required')
    token=authorization[7:]
    with _db() as c:
        row=c.execute('''SELECT s.token,s.expires_at,u.id user_id,u.name,u.email,w.id workspace_id,w.name mine,m.role FROM sessions s JOIN users u ON u.id=s.user_id JOIN workspaces w ON w.id=s.workspace_id JOIN memberships m ON m.user_id=u.id AND m.workspace_id=w.id WHERE s.token=?''',(token,)).fetchone()
        if not row or datetime.fromisoformat(row['expires_at']) < _now(): raise HTTPException(401,'Session expired')
        return dict(row)

def session_payload(token):
    s=current_session(f'Bearer {token}')
    return {'token':token,'user':{'id':s['user_id'],'name':s['name'],'email':s['email'],'role':s['role']},'workspace':{'id':s['workspace_id'],'name':s['mine']}}

def update_profile(session,payload):
    name=(payload.get('name') or '').strip(); mine=(payload.get('mine') or '').strip()
    if len(name)<2 or len(mine)<2: raise HTTPException(400,'Operator and workspace names are required')
    with _db() as c:
        c.execute('UPDATE users SET name=? WHERE id=?',(name,session['user_id']))
        c.execute('UPDATE workspaces SET name=? WHERE id=?',(mine,session['workspace_id']))
    return {'user':{'id':session['user_id'],'name':name,'email':session['email'],'role':session['role']},'workspace':{'id':session['workspace_id'],'name':mine}}

def logout(session):
    with _db() as c: c.execute('DELETE FROM sessions WHERE token=?',(session['token'],))
    return {'status':'SIGNED_OUT'}

init_db()
