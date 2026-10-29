import json, requests
import os
from datetime import datetime

MEMORY_DIR = "memory_data"
os.makedirs(MEMORY_DIR, exist_ok=True)
data = requests.get_json()
for entry in data.get("entry", []):
    entry_id = entry.get("id")
    business_id = None
    try:
        business_id = value.get('messages', {}).get('PHONE_NUMBER_ID')
    except:
        business_id = entry.get('id')
if not business_id:
    business_id = PHONE_NUMBER_ID
def _get_memory_file(business_id, from_num):
    safe_id = str(business_id).replace("/", "_")
    safe_num = str(from_num).replace("/", "_")
    return os.path.join(MEMORY_DIR, f"{safe_id}_{safe_num}.json")

def get_user_memory(business_id, from_num, limit=20):
    file_path = _get_memory_file(business_id, from_num)
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data[-limit:]
    except:
        return []

def save_to_memory(business_id, from_num, role, content):
    if not content or not content.strip():
        return
    file_path = _get_memory_file(business_id, from_num)
    history = []
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                history = json.load(f)
        except:
            history = []
    history.append({
        "role": role,
        "content": content.strip(),
        "time": datetime.now().isoformat()
    })
    if len(history) > 100:
        history = history[-100:]
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def format_memory_for_ai(business_id, from_num):
    history = get_user_memory(business_id, from_num, limit=10)
    if not history:
        return ""
    lines = []
    for h in history:
        role = "Mteja" if h["role"] == "customer" else "Wewe"
        lines.append(f"{role}: {h['content']}")
    return "\n".join(lines)

def clear_memory(business_id, from_num):
    file_path = _get_memory_file(business_id, from_num)
    if os.path.exists(file_path):
        os.remove(file_path)
