import os
import logging
from functools import wraps
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from dotenv import load_dotenv

from engine import HotelAssistant
from storage import (
    init_db, save_message, get_stats, get_recent_bookings,
    update_booking_status, get_recent_messages, get_booking
)
from whatsapp import send_whatsapp_message

load_dotenv()
logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-secret-key")
assistant = HotelAssistant()
init_db()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "jakicha_demo_verify")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change-me-now")
ADMIN_WHATSAPP = os.getenv("ADMIN_WHATSAPP", "").strip()


@app.get("/")
def home():
    return redirect(url_for("dashboard"))


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "Jakicha AI Hotel Assistant"})


@app.get("/webhook")
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge or "", 200
    return "Verification failed", 403


@app.post("/webhook")
def receive_webhook():
    payload = request.get_json(silent=True) or {}
    try:
        entries = payload.get("entry", [])
        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])
                contacts = value.get("contacts", [])
                contact_name = ""
                if contacts:
                    contact_name = contacts[0].get("profile", {}).get("name", "")
                for msg in messages:
                    if msg.get("type") != "text":
                        continue
                    sender = msg.get("from", "")
                    text = msg.get("text", {}).get("body", "").strip()
                    if not sender or not text:
                        continue
                    save_message(sender, "user", text, contact_name)
                    reply = assistant.reply(sender, text, contact_name)
                    save_message(sender, "assistant", reply, contact_name)
                    result = send_whatsapp_message(sender, reply)
                    logging.info("WhatsApp reply result: %s", result)
        return jsonify({"status": "received"}), 200
    except Exception:
        logging.exception("Webhook processing failed")
        # WhatsApp should receive a 200 where possible to avoid repeated delivery storms.
        return jsonify({"status": "received_with_processing_error"}), 200


@app.post("/demo-chat")
def demo_chat():
    data = request.get_json(silent=True) or {}
    phone = "".join(ch for ch in str(data.get("phone", "255700000000")) if ch.isdigit())
    message = str(data.get("message", "")).strip()
    name = str(data.get("name", "Demo Guest")).strip()
    if not message:
        return jsonify({"error": "Andika ujumbe kwanza."}), 400
    save_message(phone, "user", message, name)
    reply = assistant.reply(phone, message, name)
    save_message(phone, "assistant", reply, name)
    return jsonify({"reply": reply})


@app.get("/dashboard/login")
def login():
    return render_template("login.html")


@app.post("/dashboard/login")
def login_post():
    password = request.form.get("password", "")
    if password == ADMIN_PASSWORD:
        session["admin_logged_in"] = True
        return redirect(url_for("dashboard"))
    flash("Password si sahihi.", "error")
    return redirect(url_for("login"))


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper


@app.get("/dashboard/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.get("/dashboard")
@admin_required
def dashboard():
    return render_template(
        "dashboard.html",
        stats=get_stats(),
        bookings=get_recent_bookings(50),
        messages=get_recent_messages(30)
    )


@app.post("/dashboard/booking/<int:booking_id>/status")
@admin_required
def booking_status(booking_id):
    status = request.form.get("status", "pending")
    if status not in {"pending", "confirmed", "declined", "contacted"}:
        flash("Booking status si sahihi.", "error")
    else:
        update_booking_status(booking_id, status)
        flash("Booking request imesasishwa.", "success")
    return redirect(url_for("dashboard"))


@app.post("/dashboard/send")
@admin_required
def dashboard_send():
    phone = "".join(ch for ch in request.form.get("phone", "") if ch.isdigit())
    message = request.form.get("message", "").strip()
    if phone and message:
        result = send_whatsapp_message(phone, message)
        flash("Ujumbe umetumwa." if result.get("ok") else "Ujumbe haukutumwa. Kagua WhatsApp API settings.", "success" if result.get("ok") else "error")
    else:
        flash("Weka namba na ujumbe.", "error")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
