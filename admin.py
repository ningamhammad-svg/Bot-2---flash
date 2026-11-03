import time
from flask import render_template_string, request, redirect, jsonify

ADMIN_PASSWORD = "Nigro433"

ADMIN_HTML = '''
<!DOCTYPE html>
<html>
<head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family:Arial;background:#f0f2f5;margin:0;padding:10px}
.card{background:white;border-radius:10px;padding:15px;max-width:600px;margin:auto}
.item{display:block;text-decoration:none;color:black;border-bottom:1px solid #eee;padding:12px 5px}
.item:hover{background:#f5f5f5}
.badge{padding:2px 8px;border-radius:10px;font-size:11px;color:white}
.red{background:red} .green{background:green}
</style>
</head>
<body>
<div class="card">
<h2>📨 Wateja Wote ({{ customers|length }})</h2>
<input type="text" id="search" placeholder="Tafuta namba..." onkeyup="filter()" style="width:100%;padding:10px;margin-bottom:10px">
{% for c in customers %}
<a class="item" href="/admin/chat/{{ c.uid }}?p={{ pwd }}">
  <b>{{ c.name }}</b> <span style="float:right">{{ c.count }} msg</span><br>
  <small>{{ c.last_text }}</small><br>
  {% if c.is_paused %}<span class="badge red">🔴 UMEZUIA BOT - Wewe unajibu</span>
  {% else %}<span class="badge green">🟢 BOT ANAFANYA KAZI</span>{% endif %}
</a>
{% endfor %}
{% if not customers %}<p>Hakuna mteja bado.</p>{% endif %}
</div>
<script>
function filter(){
  let q=document.getElementById('search').value.toLowerCase();
  document.querySelectorAll('.item').forEach(el=>{
    el.style.display = el.innerText.toLowerCase().includes(q) ? 'block' : 'none';
  });
}
setTimeout(()=>{ location.reload(); }, 5000);
</script>
</body>
</html>
'''

CHAT_HTML = """
<!DOCTYPE html>
<html>
<head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family:Arial;background:#e5ddd5;margin:0}
.header{background:#075e54;color:white;padding:10px;position:sticky;top:0;z-index:10}
.chat{height:75vh;overflow:auto;padding:15px;display:flex;flex-direction:column;gap:8px}
.msg{max-width:75%;padding:8px 12px;border-radius:8px;font-size:14px;word-wrap:break-word}
.user{background:white;align-self:flex-start}
.bot{background:#dcf8c6;align-self:flex-end}
.owner{background:#a0e7ff;align-self:flex-end;border:1px solid #0084ff}
.form{background:white;padding:10px;display:flex;gap:5px;position:sticky;bottom:0}
input[type=text]{flex:1;padding:12px;border-radius:20px;border:1px solid #ccc}
button{padding:10px 15px;border:none;border-radius:20px;cursor:pointer}
</style>
</head>
<body>
<div class="header">
  <a href="/admin?p={{ pwd }}" style="color:white;text-decoration:none">⬅ Rudi</a> 
  &nbsp;&nbsp; <b>Chat na {{ uid }}</b><br>
  {% if is_paused %}<small style="color:#ffbaba">🔴 BOT AMEZUIWA - Wewe ndio unajibu</small>
  {% else %}<small style="color:#b7ffbf">🟢 BOT ANAFANYA KAZI</small>{% endif %}
</div>
<div class="chat" id="chat">
{% for m in msgs %}
  <div class="msg {% if m.get('source')=='OWNER' %}owner{% elif m.get('role')=='user' %}user{% else %}bot{% endif %}">
    <b style="font-size:10px">{{ m.get('role','') }} {{ '(Wewe)' if m.get('source')=='OWNER' else '' }}</b><br>
    {{ m.get('text','') }}
  </div>
{% endfor %}
</div>
<form method="POST" class="form" id="sendForm">
  <input type="text" name="text" id="textInput" placeholder="Jibu kama mmiliki..." required autocomplete="off">
  <button name="reply" value="reply" style="background:#075e54;color:white">Tuma</button>
</form>
<div style="background:white;padding:10px;display:flex;gap:10px;justify-content:center">
  <form method="POST"><button name="reply" value="pause" style="background:red;color:white">⏸️ ZUIA BOT</button></form>
  <form method="POST"><button name="reply" value="resume" style="background:green;color:white">▶️ RUHUSU BOT</button></form>
</div>
<script>
let chatDiv = document.getElementById('chat');
chatDiv.scrollTop = chatDiv.scrollHeight;

// AUTO-REFRESH KILA SEKUNDE 3 - HII NDIO INASOLVE KULAZIMIKA KUBONYEZA F5
setInterval(()=>{
  fetch(window.location.href)
    .then(r=>r.text())
    .then(html=>{
      let parser = new DOMParser();
      let doc = parser.parseFromString(html, 'text/html');
      let newChat = doc.getElementById('chat').innerHTML;
      if(newChat !== chatDiv.innerHTML){
        chatDiv.innerHTML = newChat;
        chatDiv.scrollTop = chatDiv.scrollHeight;
      }
    });
}, 3000);
</script>
</body>
</html>
"""

def register_admin(app, memory, send_whatsapp_reply):
    @app.route("/admin", methods=["GET"])
    def admin():
        if request.args.get("p") != ADMIN_PASSWORD: 
            return "Password mbaya ?p=Nigro433"

        chats = memory.chats
        paused = memory.paused_users

        customers = []
        for uid, msgs in chats.items():
            if not msgs:
                continue
            # Tafuta msg ya mwisho ya mteja, sio yako, ili last_text ionyeshe ya mteja
            last_user_msg = next((m for m in reversed(msgs) if m.get('role')=='user'), msgs[-1])
            last = msgs[-1]
            customers.append({
                "uid": uid,
                "name": uid,
                "last_text": last_user_msg.get("text", "")[:35],
                "count": len(msgs),
                "is_paused": uid in paused,
            })
        customers.sort(key=lambda x: (not x['is_paused'], -x['count']))

        return render_template_string(ADMIN_HTML, customers=customers, pwd=ADMIN_PASSWORD)

    @app.route("/admin/chat/<uid>", methods=["GET", "POST"])
    def admin_chat(uid):
        if request.args.get("p") != ADMIN_PASSWORD: 
            return "Password mbaya"

        if request.method == "POST":
            action = request.form.get("reply")

            if action == "pause":
                memory.pause_user(uid)
                return redirect(f"/admin/chat/{uid}?p={ADMIN_PASSWORD}")

            elif action == "resume":
                memory.unpause_user(uid)
                return redirect(f"/admin/chat/{uid}?p={ADMIN_PASSWORD}")

            elif action == "reply":
                text = request.form.get("text")
                if text and text not in ["pause", "resume", "reply"]:
                    send_whatsapp_reply(uid, text)
                    # MUHIMU: Tumia memory.add_message, sio append kwenye dict
                    memory.add_message(uid, "model", text, source="OWNER")
                    memory.pause_user(uid)
                return redirect(f"/admin/chat/{uid}?p={ADMIN_PASSWORD}")

        msgs = memory.get_history(uid)
        is_paused = uid in memory.paused_users

        return render_template_string(CHAT
