import os
import requests


def send_whatsapp_message(to, text):
    token = os.getenv("WHATSAPP_TOKEN", "").strip()
    phone_number_id = os.getenv("PHONE_NUMBER_ID", "").strip()
    version = os.getenv("GRAPH_VERSION", "v23.0").strip()
    if not token or not phone_number_id:
        return {"ok": False, "error": "Missing WHATSAPP_TOKEN or PHONE_NUMBER_ID"}
    url = f"https://graph.facebook.com/{version}/{phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": text[:4000]}
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        try:
            body = response.json()
        except Exception:
            body = {"raw": response.text}
        return {"ok": response.ok, "status_code": response.status_code, "data": body}
    except requests.RequestException as exc:
        return {"ok": False, "error": str(exc)}
