async function postJSON(url, data){
  const r = await fetch(url, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(data) });
  return r.json();
}

async function whoami(){
  const r = await fetch('/api/whoami');
  return r.json();
}

// login page
if(location.pathname === '/' || location.pathname.endsWith('login.html')){
  document.querySelector('#loginForm').addEventListener('submit', async (e)=>{
    e.preventDefault();
    const f = Object.fromEntries(new FormData(e.target).entries());
    const res = await postJSON('/api/login', f);
    if(res.ok) location.href = '/dashboard.html'; else alert('Login failed');
  });
}

if(location.pathname.endsWith('dashboard.html')){
  (async ()=>{
    const who = await whoami();
    if(!who.user) { location.href = '/login.html'; return; }
    document.getElementById('who').innerText = who.user.username + ' (' + who.user.role + ')';

    document.getElementById('logout').addEventListener('click', async ()=>{ await postJSON('/api/logout',{}); location.href='/login.html'; });

    // admin area
    if(who.user.role === 'admin'){
      const html = `
        <form id="createUser">
          <input name="username" placeholder="new username" required />
          <input name="password" placeholder="password" required />
          <select name="role"><option value="user">user</option><option value="admin">admin</option></select>
          <button type="submit">Create User</button>
        </form>
      `;
      document.getElementById('adminArea').innerHTML = html;
      document.getElementById('createUser').addEventListener('submit', async (e)=>{
        e.preventDefault();
        const f = Object.fromEntries(new FormData(e.target).entries());
        const res = await postJSON('/api/admin/create-user', f);
        if(res.ok){ alert('User created'); e.target.reset(); } else alert('Error: '+JSON.stringify(res));
      });
    } else {
      document.getElementById('adminArea').innerHTML = '<p class="muted">Admin features hidden</p>';
    }

    const output = document.getElementById('output');

    async function streamJob(jobId){
      const es = new EventSource('/api/stream/'+jobId);
      es.onmessage = (e)=>{ output.textContent += e.data + '\n'; output.scrollTop = output.scrollHeight; };
      es.addEventListener('end', (ev)=>{ output.textContent += '\n--- PROCESS ENDED ---\n'; es.close(); });
    }

    document.getElementById('nukeForm').addEventListener('submit', async (e)=>{
      e.preventDefault();
      const data = Object.fromEntries(new FormData(e.target).entries());
      const cfg = {
        delete: e.target.delete.checked,
        create: e.target.create.checked,
        spam: e.target.spam.checked,
        ban: e.target.ban.checked,
        ch_name: data.ch_name,
        ch_count: parseInt(data.ch_count)||0,
        spam_msg: data.spam_msg,
        spam_count: parseInt(data.spam_count)||0,
      };
      const body = { token: data.token, guild_id: data.guild_id, cfg };
      const res = await postJSON('/api/run-nuke', body);
      if(res.jobId){ output.textContent = ''; streamJob(res.jobId); }
      else alert('Error starting job');
    });

    document.getElementById('cloneForm').addEventListener('submit', async (e)=>{
      e.preventDefault();
      const data = Object.fromEntries(new FormData(e.target).entries());
      const res = await postJSON('/api/run-clone', { token: data.token, src_id: data.src_id, dst_id: data.dst_id });
      if(res.jobId){ output.textContent = ''; streamJob(res.jobId); } else alert('Error');
    });

  })();
}
