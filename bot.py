from flask import Flask, jsonify, request, render_template_string 
import requests, os
import json
from datetime import datetime
from PIL import Image
import google.generativeai  as genai
from dotenv import load_dotenv
load_dotenv()


genai.configure(api_key=os.getenv("GEMINI_API_KEY")) 
SYSTEM_PROMPT = """
    Wewe ni NingaBot, bot wa biashara kutoka Dar es salaam Tanzania.
    Biashara unayofanya ni ya kuuza simu za aina zote.
    Brand ya biashara yako ni "NINGA TELLEPHONE ACCESSORIES".
    Boss wako ni huyu hapa anaitwa NINGA.
    NAMBA YAKE YA WHATSAPP NI +255 780244426.
    KAMA MTEJA ATAMUHITAJI AMTUMIE MESSAGE KWENYE NAMBA HIYO.
    Ongea kiingereza fasaha kama mteja kakuongelesha kiingereza na kiswahili fasaha, cha mtaani, na kifupi na chenye heshima na care ya juu ya huduma kwa wateja.
    KAZI YAKO KUBWA: Tambua nia (intent) ya mteja, usijibu neno kwa neno.
    Mfano:
    -Mteja akisema "mambo, vipi, hey, hello, habari, za asubuhi au za jion, wewe -> Jibu  poa au safi au salama na muulize anahitaji msaada gani?
    -Mteja akikuuliza mnafanya biashara gani  -> mjibu tunauza SIMU kwa bei rafiki kabisa boss wangu, KARIBU!.
    -Mteja akiuliza SIMU za aina gani -> Jibu za aina zote,  bei sawa na bure kabisa boss!Nakusikiliza..
    -Mteja akisema "bei gani, mnauzaje, zinaendaje, package, gharama" -> hizi ni bei:
           -samssung s9 = 200k
           -Samssung s20 = 230k
           -Iphone 11pro = 300
           -Iphone 17proMax = 550k
           na zingine unazozifahamu wewe mtajie na bei zake.
    -Mteja akisema"mko wapi,ad mnapatikana wapi, location, ofisi" ->usimjibu.
    -mteja akikuuliza kuhusu delivery,au mzigo napataje -> mjibu:  Delivery zinapatikana pia tunafanya kazi TZ nzima.
    -Kisema "nataka kulipia bidhaa yeyote katika hizo, au nalipiaje, au lipa au malipo" -> Hii ni lipa Airtel(+255 780244426) - Jina Mohamedi Musa.
    -Mteja akisema "nataka mtu , binadamu, wakala au Agent" -> Jibu: "Sawa boss, ngoja nimpe wakala wangu" then mtumie message boss wako WhatsApp number=(+255 780244426).
     KANUNI:
     1.Usitunge uongo, usijibu usichokijua.
     2.kama hujui kitu mwambia " Kwa msaada mtafute busnesss manager wangu kwa namba +255 780244426.
     3.jibu kwa ufupi.
     4.Kumbuka mteja alichosema hapo awali.
     5.usimsumbue mteja kwa kumtumia message nyingi kwa wakati mmoja.
     6.usimtumie message mteja kama hajakutafuta mwenyewe.
     7.usitume message nyinyi kwa wakati mmoja
     """
def get_ai_reply(user_message):
    try:
       model = genai.GenerativeModel(
           model_name="gemini-3.1-flash-lite",
           system_instruction=SYSTEM_PROMPT
       )
       response = model.generate_content(user_message)
       return response.text
    except Exception as e:
        print(f"ERROR: {e}")
        return "kuna hitilafu kidogo ya mtandao bosi"
def tuma_location(to):
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    payload = {"messaging_product": "whatsapp", "to": to, "type":"location", "location":{"latitude": -6.7924,"longitude": 39.2083,"name": "NINGA TELLEPHONE ACCESSORIES - Kariakoo", "address": "Mtaa wa Agrey & Likoma" }}
    r = requests.post(url, headers=headers, json=payload)
    print("Location imetumwa!")
def send_whatsapp_reply(to, text):
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    payload = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text}}
    r = requests.post(url, headers=headers, json=payload)
    print(f"SEND REPLY STATUS: {r.status_code} - {r.text}")
    return r
def tuma_alert_kwa_mmiliki(customer_num, customer_msg, aina):
    """
    aina = "ORDER" au "SHIDA"
    """
    try:
        if aina == "ORDER":
            text = f"🚨 *ORDER MPYA!* 🚨\n\n👤 Mteja: {customer_num}\n📝 Alisema: {customer_msg}\n\nMwangalie haraka kwenye WhatsApp!"
        else:
            text = f"⚠️ *SHIDA / MALALAMIKO* ⚠️\n\n👤 Mteja: {customer_num}\n❗ Tatizo: {customer_msg}\n\nInahitaji msaada wako."

        send_whatsapp_reply(OWNER_NUMBER, text)
        print(f">>> ALERT IMETUMWA KWA MMILIKI: {aina} kutoka {customer_num}")
    except Exception as e:
        print(f"ERROR ALERT MMILIKI: {e}")

def download_whatsapp_media(media_id):
    try:
        url = f"https://graph.facebook.com/v20.0/{media_id}"
        headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
        r = requests.get(url, headers=headers)
        media_url = r.json().get("url")
        r2 = requests.get(url, headers=headers)
        return r2.content
    except Exception as e:
        print(f"ERROR DOWNLOAD:N{e}")
        return None
def tuma_picha_local(to, file_path, caption=""):
    try:
        upload_url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/media"
        headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'image/jpeg')}
            data = {'messaging_product': 'whatsapp', 'type': 'image.jpeg'}
            upload_res = requests.post(upload_url, headers=headers, files=files, data=data)
        media_id =  upload_res.json().get("id")
        print(f"UPLOAD:{upload_res.text}")
        if not media_id:
            print(f"UPLOAD FAILED:{upload_res.text}")
            return
        send_url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
        headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
        payload = {
        "messaging_product": "whatsapp", "to": to,
        "type": "image", "image": {"id": media_id, "caption": caption}
        }
        r = requests.post(send_url, headers=headers, json=payload)
        print(f"SEND IMAGE: {r.text}")
    except Exception as e:
        print(f"ERROR TUMA LOCAL: {e}")


app = Flask(__name__)
processed_message = set()
PRODUCTS_FOLDER = "products"
def is_duplicate(message_id):
    if message_id in processed_message:
        return True
    processed_message.add(message_id)
    if len(processed_message) >100:
        processed_message.pop()
    return False
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "NEGRO343")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OWNER_NUMBER = os.getenv("OWNER_NUMBER", "255780244426")
@app.route("/")
def home():
    return "Ninga Bot is Live! ✅", 200

@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Verification failed", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print(f"INCOMING: {data}")  # <-- HII NDIO ULIYOZUNGUSHIA, IPO HAPA

    try:
        if data and data.get("object") == "whatsapp_business_account":
            for entry in data.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    messages = value.get("messages")
                    if messages:
                        for msg in messages:
                            from_num = msg.get("from")
                            msg_body = msg.get("text", {}).get("body", "") or msg.get("image", {}).get("caption", "")
    
                            if msg_body:
                                print(f"MESSAGE FROM {from_num}: {msg_body}")
                                msg_id = msg.get("id")
                                if is_duplicate(msg_id):
                                    print(f"DUPLICATE IMEZUIWA: {msg_id}")
                                    continue
                                from_num = msg.get("from")
                                msg_body = msg.get("text", {}).get("body", "")
                                if not msg_body and msg.get("image"):
                                    msg_body = msg.get("image", {}).get("caption", "")
                                    image_id = msg.get("image", {}).get("id")
                                if is_bot_paused(from_num):
                                   print(f"BOT AMELALA kwa {from_num} - Sijibu, bosi anaongea")
                                   save_chat(PHONE_NUMBER_ID, from_num, "customer", msg_body)
                                   return "OK" # usijibu
                                lower = msg_body.lower()
                                reply_text = ""
                                business_id = PHONE_NUMBER_ID
                                save_chat(business_id, from_num, "customer", msg_body)
                                save_chat(business_id, from_num, "bot", reply_text)
                                print(f"MESSAGE FROM {from_num}: {msg_body}")
                                order_keywords = ["order", "nitanunua", "namuhitaji boss", "nahitaji delivery", "nataka", "ninataka", "naomba", "nauza", "bei", "nitalipa", 
                                                  "nimeshalipa", "lipa", "nunua", "book", "agiza"] 
                                shida_keywords = ["shida", "haifanyi", "mbovu", "tatizo", "imekataa", "malalamiko", "mwizi", "haijafika",
                                                  "complaint", "help"]
                                if any(k in lower for k in order_keywords):
                                    tuma_alert_kwa_mmiliki(from_num, msg_body, "ORDER") 
                                elif any(k in lower for k in shida_keywords):
                                    tuma_alert_kwa_mmiliki(from_num, msg_body, "SHIDA") 
                                
                                keywords = ["location", "Google", "map","ziko","duka","mnako","mko","patikana","address","link", "ramani",
                                            "mko wapi", "mnakopatikana", "mko wapi", "duka liko wapi", "mahali mlipo" "ofisi zenu", "kufika",
                                           "where","locate","located","pin","come","direction","find you","office","shop"]
                                if any(k in lower for k in keywords):
                                    print(">>>NINATUMA LOCATION<<<")
                                    tuma_location(from_num)
                                elif "iPhone" in lower:
                                    tuma_picha_local(from_num, "products/iPhone.jpg", "iPhone Pro Max - Tsh. 780k, Original na warranty")
                                elif "picha" in lower or "katalogi" in lower or "bidhaa" in lower:
                                    tuma_picha_local(from_num, "products/iPhone.jpg", "Hizi hapa bidhaa zetu maarufu")
                                else:
                                    reply = get_ai_reply(msg_body)
                                    send_whatsapp_reply(from_num, reply)
    except Exception as e:
             print(f"ERROR: {e}")     
    return "OK", 200  

@app.route('/admin/<business_id>')
def admin_panel(business_id):
    token = request.args.get("token")
    if token != VERIFY_TOKEN:
        return "❌ Token si sahihi", 403
    
    data = {}
    if os.path.exists(CHATS_FILE):
        with open(CHATS_FILE, 'r') as f:
            data = json.load(f)
    
    control = get_control_data()
    
    all_chats = data.get(business_id, {})
    return render_template_string(ADMIN_TEMPLATE, 
                                  business_id=business_id,
                                  all_chats=all_chats,
                                  paused_list=control.get("paused_customers", []),
                                  is_global_paused=control.get("global_pause", False),
                                  token=token)

@app.route('/admin/<business_id>/control')
def admin_control(business_id):
    token = request.args.get("token")
    action = request.args.get("action")
    customer = request.args.get("customer")
    
    if token != VERIFY_TOKEN:
        return {"error": "token si sahihi"}, 403
    
    control = get_control_data()
    
    if action == "pause":
        pause_bot_for_customer(customer)
        return {"message": f"😴 Bot amelalazwa kwa {customer}. Sasa wewe ongea nae!"}
    
    elif action == "resume":
        resume_bot_for_customer(customer)
        return {"message": f"☀️ Bot ameamshwa kwa {customer}. Ataanza kujibu."}
    
    elif action == "pause_global":
        control["global_pause"] = True
        save_control_data(control)
        return {"message": "😴 BOT AMELALA GLOBAL - Hajibu mtu yeyote!"}
    
    elif action == "resume_global":
        control["global_pause"] = False
        save_control_data(control)
        return {"message": "☀️ BOT AMEAMKA GLOBAL - Anajibu wote!"}
    
    return {"error": "action haijulikani"}, 400

# === 4. FUNCTION YA KUTUMA ADMIN LINK KWA MFANYABIASHARA ===
def tuma_admin_link_kwa_mfanyabiashara(owner_whatsapp_number):
    """Tuma link kwa mfanyabiashara baada ya kununua bot"""
    # Badilisha YOUR_DOMAIN na domain yako halisi
    YOUR_DOMAIN = "https://yourdomain.com"  # mfano https://ncip.onrender.com
    link = f"{YOUR_DOMAIN}/admin/{PHONE_NUMBER_ID}?token={VERIFY_TOKEN}"
    
    text = f"""✅ *Hongera! Msaidizi wako wa NCIP uko tayari*

🔗 *ADMIN LINK YAKO:*
{link}

Kupitia link hii utaweza:
1. Kuona mazungumzo yote ya bot yako na wateja LIVE
2. Kuona bot imeishia wapi kabla ya kukuita
3. Kujibu mteja moja kwa moja kwa kubonyeza 'Jibu kwa WhatsApp'

⚠️ Usimtumie mtu yeyote link hii, ni siri yako.

Karibu NCIP DIGITAL MARKET 🚀"""
    
    send_whatsapp_reply(owner_whatsapp_number, text)

CONTROL_FILE = "bot_control.json"

def get_control_data():
    if os.path.exists(CONTROL_FILE):
        with open(CONTROL_FILE, 'r') as f:
            return json.load(f)
    return {"paused_customers": [], "global_pause": False}

def save_control_data(data):
    with open(CONTROL_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def is_bot_paused(customer_num):
    data = get_control_data()
    if data.get("global_pause"):
        return True
    return customer_num in data.get("paused_customers", [])

def pause_bot_for_customer(customer_num):
    data = get_control_data()
    if customer_num not in data["paused_customers"]:
        data["paused_customers"].append(customer_num)
    save_control_data(data)
    print(f">>> BOT AMELALAZWA kwa {customer_num}")

def resume_bot_for_customer(customer_num):
    data = get_control_data()
    if customer_num in data["paused_customers"]:
        data["paused_customers"].remove(customer_num)
    save_control_data(data)
    print(f">>> BOT AMEAMSHWA kwa {customer_num}")
CHATS_FILE = "chats.json"

def save_chat(business_id, customer_num, role, message):
    """Hifadhi kila ujumbe - role ni 'customer' au 'bot'"""
    try:
        if os.path.exists(CHATS_FILE):
            with open(CHATS_FILE, 'r') as f:
                data = json.load(f)
        else:
            data = {}
        
        if business_id not in data:
            data[business_id] = {}
        if customer_num not in data[business_id]:
            data[business_id][customer_num] = []
        
        data[business_id][customer_num].append({
            "role": role,
            "msg": message,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        data[business_id][customer_num] = data[business_id][customer_num][-20:]
        
        with open(CHATS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"ERROR SAVE CHAT: {e}")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
    ADMIN_TEMPLATE = 
    html = f '''
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NCIP ADMIN</title>
<style>
body{font-family:sans-serif;background:#0f172a;color:white;margin:0;padding:10px}
.header{background: white;padding:15px;border-radius:12px;text-align:center}
.customer{background:#1e293b;margin:15px 0;border-radius:12px;padding:12px;border-left:5px solid #22c55e}
.customer.paused{border-left-color:#ef4444;background:#2a1a1a}
.msg{padding:8px 12px;border-radius:18px;margin:5px 0;max-width:85%;color:black}
.cust{background:#dbeafe}
.bot{background:#dcfce7;margin-left:auto;text-align:right}
.time{font-size:10px;color:gray}
.btn{padding:10px 16px;border-radius:20px;text-decoration:none;display:inline-block;margin:4px;font-weight:bold}
.btn-pause{background:#ef4444;color:white}
.btn-resume{background:#22c55e;color:white}
.btn-wa{background:#25D366;color:white}
.status{padding:8px;border-radius:10px;text-align:center;font-weight:bold;margin:10px 0}
.status-awake{background:#22c55e22;color:#22c55e;border:1px solid #22c55e}
.status-sleep{background:#ef444422;color:#ef4444;border:1px solid #ef4444}
</style>
</head>
<body>
<div class="header">
<h2>NCIP - BOT CONTROL PANEL</h2>
<p>Biashara: """ + business_id + """</p>
<p>Token: """ + token + """</p>
</div>
<h3 style="text-align:center">Wateja: """ + str(len(all_chats)) + """</h3>
'''
