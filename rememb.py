import json, os, time
from collections import OrderedDict

FILE = "memory.json"

# Data zote 3 muhimu
chat = {}
profiles = {}
paused_users = {}
seen = OrderedDict()

# 1. SOMA FILE KAMA IPO
if os.path.exists(FILE):
    try:
        data = json.load(open(FILE, "r", encoding="utf-8"))
        chat = data.get("chats", {})
        profiles = data.get("profiles", {})
        paused_users = data.get("paused_users", {})
        print(f"✅ Memory loaded: {len(chat)} users")
    except Exception as e:
        print(f"⚠️ Error kusoma memory: {e}")
        chat = {}
        profiles = {}
        paused_users = {}
else:
    print("ℹ️ memory.json haipo, tunaunda mpya")

def save():
    """Save vitu vyote 3, watu wote generaly"""
    try:
        # Andika kwenye temp file kwanza ili usiharibu file kama umeme ukikatika
        temp_file = FILE + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump({
                "chats": chat,
                "profiles": profiles,
                "paused_users": paused_users
            }, f, ensure_ascii=False, indent=2)
        os.replace(temp_file, FILE)
    except Exception as e:
        print(f"❌ Save failed: {e}")

def is_dup(mid):
    """Zuia message moja isijirudie mara 2"""
    if not mid:
        return False
    if mid in seen:
        return True
    seen[mid] = 1
    if len(seen) > 500:
        seen.popitem(last=False)
    return False

def get_history(uid):
    """Rudisha history yote ya huyu user, AI atasoma zote"""
    # Tunamrudishia zote, sio 15 tu, ili akumbuke vizuri
    return chat.get(uid, [])
    
def get_history_text(uid):
    """Hii ndio AI itaitumia kukumbuka sms 5-6 za mwisho"""
    history = chat.get(uid, [])[-12:]  # 12 = sms 6 za mteja + 6 za bot
    lines = []
    for h in history:
        jina = "Mteja" if h["role"] == "user" else "Bot"
        lines.append(f"{jina}: {h['text']}")
    return "\n".join(lines)    

def add(uid, role, text, source="BOT"):
    """Save chat ya mtu yeyote generally"""
    if not uid or not text:
        return
    if uid not in chat:
        chat[uid] = []
    
    chat[uid].append({
        "role": role,
        "text": text,
        "source": source,
        "time": time.time()
    })
    # Zuia isijaze sana, weka max 200 per user ili file isijaze GB
    if len(chat[uid]) > 200:
        chat[uid] = chat[uid][-200:]
    
    save()

def get_all_chats():
    """Hii ndio admin panel inaita kuona wateja wote"""
    return chat

def get_all_users():
    """Rudisha list ya namba zote"""
    return list(chat.keys())

def pause_user(uid):
    paused_users[uid] = True
    save()

def unpause_user(uid):
    paused_users.pop(uid, None)
    save()

# Hii ndio object ambayo ninga.py inaita kama memory.add, memory.get_history
memory = type("", (), {
    "is_duplicate": staticmethod(is_dup),
    "get_history": staticmethod(get_history),
    "add_message": staticmethod(add),
    "get_history_text": staticmethod(get_history_text),
    "get_all_chats": staticmethod(get_all_chats),
    "get_all_users": staticmethod(get_all_users),
    "pause_user": staticmethod(pause_user),
    "unpause_user": staticmethod(unpause_user),
    "chats": chat,
    "paused_users": paused_users
})()
