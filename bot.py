from flask import Flask, jsonify, request
import requests, os
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
                                    msg_body = msg.get("image", {}).get("caption", "Hii simu ipo?")
    
                                lower = msg_body.lower()
                                print(f"MESSAGE FROM {from_num}: {msg_body}")
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

