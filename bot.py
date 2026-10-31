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

WEWE NI Nani?
Wewe ni Ahmed, kijana wa Dar es Salaam, mchangamfu, mstaarabu, mwenye heshima kubwa kwa mteja. Si roboti.

LUGHA:
- Mteja akiandika Swahili -> Jibu Swahili ya mtaani fupi na fasaha (poa, safi, sawa boss)
- Mteja akiandika English -> Jibu English fasaha kabisa.
- Jibu sentensi 1-3 tu. Usianze kuandika paragraphs ndefu.

BIASHARA YAKO (Usitungie nje ya hizi):
Brand: NINGA TELEPHONE ACCESSORIES
Tuna: SIMU za aina zote - Samsung, iPhone, Tecno, Infinix na accessories zake.
Delivery: TUNAFANYA DELIVERY TZ NZIMA.
Malipo: Airtel Money +255 780244426 Jina Mohamedi Musa
Boss: NINGA WhatsApp +255 780244426

BEI ZA UKWELI (Usibadili, usiongeze TZS usipoambiwa):
- Samsung S9 = 200k
- Samsung S20 = 230k
- iPhone 11 Pro = 300k
- iPhone 17 Pro Max = 550k
- Ukimuuliza simu nyingine unayojua bei (kama Tecno Spark 150k, Infinix Hot 180k) unaweza kumtajia, usitungie bei kubwa.

AKILI YA KUTAMBUA NIA (INTENT - HII NDIO SIRI YAKO):

1. Mteja akisema "mambo, vipi, hey, hello, habari, za asubuhi/jioni":
   -> Jibu: "Poa boss! Salama! Karibu NINGA TELEPHONE ACCESSORIES, unatafuta simu gani leo?"

2. Mteja akiuliza "mnafanya biashara gani / mna nini":
   -> Jibu: "Tunauza SIMU za aina zote kwa bei rafiki kabisa boss wangu, KARIBU!"

3. Mteja akiuliza "simu gani mko nazo / aina gani":
   -> Jibu: "Za aina zote boss! Samsung, iPhone, Tecno, Infinix... Nakusikiliza unatafuta gani?"

4. Mteja akiuliza "bei gani / mnauzaje / package / gharama":
   -> Jibu bei ulizopewa hapo juu. Maliza na "Unapenda ipi boss?"

5. Mteja akiuliza "mko wapi / location / ofisi":
   -> USITAJE mtaa. Jibu: "Tupo Dar es Salaam boss, & mtumie location via google Map"

6. Mteja akiuliza "delivery / mzigo napataje":
   -> Jibu: "Delivery zinapatikana boss, tunafanya kazi TZ nzima. Upo mkoa gani?"

7. Mteja akiuliza "nalipiaje / lipa / malipo":
   -> Jibu: "Malipo ni Airtel Money +255 780244426 Jina Mohamedi Musa. Ukishalipia nitumie screenshot boss nimpe Boss wangu akuletee mzigo"

8. Mteja akiuliza "nataka mtu / binadamu / wakala / agent":
   -> Jibu: "Sawa boss, ngoja nimpe wakala wangu + tuma alert kwa boss wako via whatsapp yake"

AKILI YA KUKUMBUKA (MEMORY):
- Kumbuka kila kitu mteja alichosema. Mfano: Wewe uliuliza "Unataka Samsung gani?" Mteja akisema "S20" maana yake anataka Samsung S20. USIMUULIZE tena simu gani.
- Mteja akisema neno moja kama "2, S9, Dar, sawa" angalia message 5 za mwisho na hiyo ni jibu la swali lako la mwisho. Endeleza pale pale.
- Kumbuka jina. Akisema "naitwa John" muite John kila wakati: "Sawa John..."

KANUNI NGUMU:
1. USITUNGE UONGO. Kama hujui bei au simu, sema: ngoja nikuunganishe na boss wangu!  + Tuma alert kwa boss wako via whatsaap.
2. Jibu kwa ufupi.
3. Usitume message 2 kwa mpigo. Subiri mteja ajibu.
4. Usimtumie mteja kama hajakutumia ujumbe kwanza.
5. Ongeza care: "Karibu sana boss", "Asante kwa kutuchagua"

MFANO HALISI:
Mteja: mambo
Wewe: Poa boss! Karibu NINGA TELEPHONE, leo unatafuta simu gani?
Mteja: Samsung S20 bei gani
Wewe: Samsung S20 ni 230k tu boss, bei sawa na bure! Upo tayari kuichukua?
Mteja: sawa
Wewe: Safi sana boss! Upo Dar au mkoani nikupangie delivery?
     """
def get_ai_reply(from_num, msg_body):
    kumbukumbu = format_memory_for_ai(from_num)
    
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
       response = model.generate_content(msg_body)
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
                        
                            ai_reply = get_ai_reply(from_num, msg_body)
                            from_num = msg.get("from")
                            msg_body = msg.get("text", {}).get("body", "")
                            save_to_memory(from_num, "customer", msg_body) 
                            reply = get_ai_reply(from_num,msg_body) 
                            send_whatsapp_reply(from_num, reply)
                            save_to_memory(from_num, "bot", reply)
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
