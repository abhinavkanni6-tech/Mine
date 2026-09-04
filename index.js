const express = require('express');
const session = require('express-session');
const bodyParser = require('body-parser');
const bcrypt = require('bcrypt');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const EventEmitter = require('events');
const { v4: uuidv4 } = require('uuid');

const app = express();
const PORT = process.env.PORT ? parseInt(process.env.PORT, 10) : 3000;
const SESSION_SECRET = process.env.SESSION_SECRET || 'change-this-secret';
const ADMIN_USER = process.env.ADMIN_USER || 'admin';
const ADMIN_PASS = process.env.ADMIN_PASS || 'admin';
const PYTHON_CMD = process.env.PYTHON_CMD || (process.platform === 'win32' ? 'python' : 'python3');

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(require('cors')());

app.use(session({
  secret: SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
}));

const USERS_FILE = path.join(__dirname, 'users.json');
function loadUsers(){
  try{ return JSON.parse(fs.readFileSync(USERS_FILE,'utf8')||'{}'); }catch(e){ return {users:[]}; }
}
function saveUsers(u){ fs.writeFileSync(USERS_FILE, JSON.stringify(u, null, 2)); }

// Ensure default admin exists (use ENV values)
let users = loadUsers();
if(!users.users) users = { users: [] };
if(!users.users.find(x=>x.username===ADMIN_USER)){
  const salt = bcrypt.genSaltSync(10);
  const hash = bcrypt.hashSync(ADMIN_PASS, salt);
  users.users.push({ username: ADMIN_USER, password: hash, role: 'admin' });
  saveUsers(users);
  console.log(`Created default admin user: ${ADMIN_USER}`);
} else {
  console.log(`Admin user ${ADMIN_USER} already exists (not overwritten)`);
}

// Simple auth middleware
function requireAuth(req, res, next){
  if(req.session && req.session.user) return next();
  return res.status(401).json({ error: 'unauthenticated' });
}
function requireAdmin(req, res, next){
  if(req.session && req.session.user && req.session.user.role === 'admin') return next();
  return res.status(403).json({ error: 'forbidden' });
}

// Serve static UI
app.use('/', express.static(path.join(__dirname, 'public')));

// Auth routes
app.post('/api/login', (req, res) => {
  const { username, password } = req.body;
  const db = loadUsers();
  const u = db.users.find(x=>x.username===username);
  if(!u) return res.status(400).json({ error: 'invalid' });
  if(!bcrypt.compareSync(password, u.password)) return res.status(400).json({ error: 'invalid' });
  req.session.user = { username: u.username, role: u.role };
  res.json({ ok: true, user: req.session.user });
});

app.post('/api/logout', (req, res) => {
  req.session.destroy(()=>res.json({ ok: true }));
});

app.post('/api/admin/create-user', requireAdmin, (req, res) => {
  const { username, password, role } = req.body;
  if(!username || !password) return res.status(400).json({ error: 'missing' });
  const db = loadUsers();
  if(db.users.find(x=>x.username===username)) return res.status(400).json({ error: 'exists' });
  const salt = bcrypt.genSaltSync(10);
  const hash = bcrypt.hashSync(password, salt);
  db.users.push({ username, password: hash, role: role||'user' });
  saveUsers(db);
  res.json({ ok: true });
});

app.get('/api/whoami', (req, res) => {
  res.json({ user: req.session.user || null });
});

// Job management
const jobs = {}; // jobId -> { proc, emitter, logs }

function startPythonJob(scriptPath, payload) {
  return new Promise((resolve, reject) => {
    try {
      const runner = spawn(PYTHON_CMD, [scriptPath], { stdio: ['pipe','pipe','pipe'] });
      const emitter = new EventEmitter();
      const jobId = uuidv4();
      jobs[jobId] = { proc: runner, emitter, logs: [] };

      runner.stdout.on('data', (d) => {
        const s = d.toString();
        jobs[jobId].logs.push(s);
        emitter.emit('log', s);
      });
      runner.stderr.on('data', (d) => {
        const s = d.toString();
        jobs[jobId].logs.push(s);
        emitter.emit('log', s);
      });
      runner.on('close', (code) => {
        emitter.emit('end', code);
      });

      // send payload via stdin as JSON
      runner.stdin.write(JSON.stringify(payload));
      runner.stdin.end();

      resolve(jobId);
    } catch (err) {
      reject(err);
    }
  });
}

app.post('/api/run-nuke', requireAuth, async (req, res) => {
  const { token, guild_id, cfg } = req.body;
  if(!token || !guild_id) return res.status(400).json({ error: 'missing token or guild_id' });
  try {
    const jobId = await startPythonJob(path.join(__dirname, 'run_nuke_web.py'), { token, guild_id, cfg });
    res.json({ jobId });
  } catch (err) {
    res.status(500).json({ error: 'failed_to_start', detail: String(err) });
  }
});

app.post('/api/run-clone', requireAuth, async (req, res) => {
  const { token, src_id, dst_id } = req.body;
  if(!token || !src_id || !dst_id) return res.status(400).json({ error: 'missing' });
  try {
    const jobId = await startPythonJob(path.join(__dirname, 'run_clone_web.py'), { token, src_id, dst_id });
    res.json({ jobId });
  } catch (err) {
    res.status(500).json({ error: 'failed_to_start', detail: String(err) });
  }
});

// SSE stream for logs
app.get('/api/stream/:jobId', requireAuth, (req, res) => {
  const id = req.params.jobId;
  const job = jobs[id];
  if(!job) return res.status(404).end('Not found');
  res.setHeader('Content-Type','text/event-stream');
  res.setHeader('Cache-Control','no-cache');
  res.setHeader('Connection','keep-alive');
  const send = (d) => res.write(`data: ${d.replace(/\n/g,'\ndata: ')}\n\n`);
  // send existing logs
  job.logs.forEach(l => send(l));
  const onLog = (d) => send(d);
  const onEnd = (code) => { res.write(`event: end\ndata: ${code}\n\n`); res.end(); };
  job.emitter.on('log', onLog);
  job.emitter.once('end', onEnd);
  req.on('close', () => {
    job.emitter.removeListener('log', onLog);
  });
});

// simple list users for admin
app.get('/api/admin/users', requireAdmin, (req,res)=>{
  const db = loadUsers();
  res.json({ users: db.users.map(u=>({ username: u.username, role: u.role })) });
});

app.listen(PORT, () => console.log(`Server started on http://localhost:${PORT} (admin: ${ADMIN_USER}, python: ${PYTHON_CMD})`));
