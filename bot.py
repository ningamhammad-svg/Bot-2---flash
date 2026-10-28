from flask import Flask, jsonify, request, render_template_string 
import requests, os
import json
from datetime import datetime
from PIL import Image
import google.generativeai  as genai
from dotenv import load_dotenv
load_dotenv()
from storage import save_chat, is_bot_paused, get_control_data
from admin import admin_bp
from rememb import save_to_memory, format_memory_for_ai, clear_memory
app = Flask(__name__)
app.register_blueprint(admin_bp)
VERIFY_TOKEN = "NEGRO342"
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
    kumbukumbu = format_memory_for_ai(business_id, from_num)
    
    prompt = f"""
    Wewe ni msaidizi wa duka.
    Kumbukumbu ya mazungumzo na mteja {from_num}:
    {kumbukumbu}

    Ujumbe mpya wa mteja: {msg_body}
    Jibu kwa kifupi na kwa Kiswahili.
    """
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
                entry_id = entry.get("id")
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    business_id = value.get('metadata', {}).get('phone_number_id')
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
                            if is_bot_paused(from_num):
                                print(f"BOT AMELALA kwa {from_num}")
                                continue   
                                ai_reply = get_ai_reply(msg_body)
                                from_num = msg.get("from")
                                msg_body = msg.get("text", {}).get("body", "")
                            save_to_memory(business_id, from_num, "customer", msg_body) 
                            reply = get_ai_reply(msg_body) 
                            send_whatsapp_reply(from_num, reply)
                            save_to_memory(business_id, from_num, "bot", reply)
                            if not msg_body and msg.get("image"):
                                msg_body = msg.get("image", {}).get("caption", "")
                                image_id = msg.get("image", {}).get("id")
                              
                                lower = msg_body.lower()
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
    ADMIN_TEMPLATE = """
    html = f'''
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
    body{{margin:0;padding:0;background:#f1f5f9;font-family:-apple-system,BlinkMacSystemFont,sans-serif}}
    .header{{background:#111827;color:white;padding:20px;text-align:center}}
    .header h1{{margin:0;font-size:18px;letter-spacing:1px}}
    .stats{{display:flex;gap:10px;padding:12px}}
    .stat{{flex:1;background:white;border-radius:12px;padding:12px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,0.1)}}
    .stat b{{display:block;font-size:20px}}
    .stat span{{font-size:12px;color:#64748b}}
    .container{{padding:12px}}
    .card{{background:white;border-radius:16px;padding:14px;margin-bottom:12px;box-shadow:0 2px 8px rgba(0,0,0,0.06);border-left:4px solid #10b981}}
    .card.paused{{border-left-color:#ef4444}}
    .card-top{{display:flex;justify-content:space-between;align-items:center}}
    .num{{font-weight:700;font-size:15px}}
    .badge{{font-size:11px;padding:4px 10px;border-radius:20px}}
    .badge.on{{background:#dcfce7;color:#166534}} .badge.off{{background:#fee2e2;color:#991b1b}}
    .actions{{margin:10px 0;display:flex;gap:8px}}
    .btn{{flex:1;text-align:center;padding:10px;border-radius:10px;text-decoration:none;font-weight:700;font-size:13px;color:white}}
    .btn-pause{{background:#ef4444}} .btn-resume{{background:#10b981}} .btn-wa{{background:#111827}}
    .chat-box{{background:#f8fafc;border-radius:12px;padding:10px;margin-top:10px;max-height:300px;overflow-y:auto}}
    .msg{{padding:8px 12px;border-radius:14px;margin:6px 0;font-size:13px;line-height:1.4;max-width:85%}}
    .msg-c{{background:#e0f2fe;color:#0c4a6e}} .msg-b{{background:#dcfce7;color:#14532d;margin-left:auto;text-align:right}}
    .time{{font-size:10px;color:#94a3b8;margin-top:2px}}
    </style></head><body>
    <div class="header"><h1>NCIP ADMIN - {business_id}</h1><small style="opacity:0.7">bot-2-flash.onrender.com</small></div>
    <div class="stats">
      <div class="stat"><b>{len(all_chats)}</b><span>WATEJA</span></div>
      <div class="stat"><b>{len(control.get('paused_customers',[]))}</b><span>PAUSED</span></div>
      <div class="stat"><b>{sum(len(v) if isinstance(v,list) else 0 for v in all_chats.values())}</b><span>JUMLA MSGS</span></div>
    </div>
    <div class="container">
    '''
  """
