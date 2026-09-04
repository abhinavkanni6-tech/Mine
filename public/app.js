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
    async function fetchUsers(){
      const r = await fetch('/api/admin/users');
      if(!r.ok) return null;
      return r.json();
    }

    async function renderAdminArea(){
      if(who.user.role !== 'admin'){
        document.getElementById('adminArea').innerHTML = '<p class="muted">Admin features hidden</p>';
        return;
      }

      const data = await fetchUsers();
      if(!data){ document.getElementById('adminArea').innerHTML = '<p class="muted">Failed to load users</p>'; return; }

      const users = data.users || [];

      const tableRows = users.map(u=>`
        <tr data-username="${u.username}">
          <td class="mono">${u.username}</td>
          <td>
            <select class="roleSelect">
              <option value="user" ${u.role==='user'?'selected':''}>user</option>
              <option value="admin" ${u.role==='admin'?'selected':''}>admin</option>
            </select>
          </td>
          <td>
            <input class="pwInput" placeholder="new password" />
          </td>
          <td class="actions">
            <button class="saveBtn">Save</button>
            <button class="delBtn">Delete</button>
          </td>
        </tr>
      `).join('');

      const html = `
        <div class="admin-grid">
          <div class="admin-panel">
            <h4>Create user</h4>
            <form id="createUser" class="create-form">
              <input name="username" placeholder="new username" required />
              <input name="password" placeholder="password" required />
              <select name="role"><option value="user">user</option><option value="admin">admin</option></select>
              <button type="submit" class="primary">Create User</button>
            </form>
          </div>
          <div class="admin-panel users-panel">
            <h4>Manage users</h4>
            <table class="user-table">
              <thead><tr><th>Username</th><th>Role</th><th>Reset password</th><th>Actions</th></tr></thead>
              <tbody>
                ${tableRows}
              </tbody>
            </table>
          </div>
        </div>
      `;

      document.getElementById('adminArea').innerHTML = html;

      // create user handler
      document.getElementById('createUser').addEventListener('submit', async (e)=>{
        e.preventDefault();
        const f = Object.fromEntries(new FormData(e.target).entries());
        const res = await postJSON('/api/admin/create-user', f);
        if(res.ok){ alert('User created'); e.target.reset(); renderAdminArea(); } else alert('Error: '+JSON.stringify(res));
      });

      // attach row handlers
      document.querySelectorAll('.user-table tbody tr').forEach(row=>{
        const username = row.dataset.username;
        const saveBtn = row.querySelector('.saveBtn');
        const delBtn = row.querySelector('.delBtn');
        const roleSel = row.querySelector('.roleSelect');
        const pwInput = row.querySelector('.pwInput');

        saveBtn.addEventListener('click', async ()=>{
          const payload = { role: roleSel.value };
          if(pwInput.value) payload.password = pwInput.value;
          const res = await fetch('/api/admin/user/'+encodeURIComponent(username), { method:'PUT', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
          if(res.ok){ alert('Updated'); renderAdminArea(); } else { const j = await res.text(); alert('Error: '+j); }
        });

        delBtn.addEventListener('click', async ()=>{
          if(!confirm('Delete user '+username+'?')) return;
          const res = await fetch('/api/admin/user/'+encodeURIComponent(username), { method:'DELETE' });
          if(res.ok){ alert('Deleted'); renderAdminArea(); } else { const j = await res.text(); alert('Error: '+j); }
        });
      });
    }

    // render admin area once
    await renderAdminArea();

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
