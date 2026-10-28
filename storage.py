import json, os
from datetime import datetime

CHATS_FILE = "/tmp/chats.json"
CONTROL_FILE = "/tmp/control.json"

def get_control_data():
    if os.path.exists(CONTROL_FILE):
        try:
            with open(CONTROL_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"paused_customers": [], "global_pause": False}

def save_control_data(data):
    with open(CONTROL_FILE, 'w') as f:
        json.dump(data, f)

def is_bot_paused(from_num):
    control = get_control_data()
    return from_num in control.get("paused_customers", [])

def save_chat(business_id, customer_number, role, text):
    if not business_id or not customer_number or not text:
        return
    data = {}
    if os.path.exists(CHATS_FILE):
        try:
            with open(CHATS_FILE, 'r') as f:
                data = json.load(f)
        except:
            data = {}
    
    if business_id not in data:
        data[business_id] = {}
    if customer_number not in data[business_id]:
        data[business_id][customer_number] = []
    
    data[business_id][customer_number].append({
        "role": role,
        "msg": text,
        "time": datetime.now().strftime("%H:%M %d/%m")
    })
    data[business_id][customer_number] = data[business_id][customer_number][-30:]
    
    with open(CHATS_FILE, 'w') as f:
        json.dump(data, f)

def get_all_chats():
    if os.path.exists(CHATS_FILE):
        try:
            with open(CHATS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}
