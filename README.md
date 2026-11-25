# JAKICHA AI HOTEL ASSISTANT — NCIP Technologies Demo

A Python/Flask WhatsApp Cloud API prototype with:
- WhatsApp webhook verification and inbound text handling
- Gemini-powered multilingual hotel Q&A (Swahili/English/French/Arabic)
- Deterministic booking-request collection
- SQLite storage for messages, guest sessions and booking requests
- Human handover notification to a staff WhatsApp number
- Password-protected dashboard, booking status updates and outbound message form
- Browser demo chat that works without WhatsApp credentials

## Important accuracy / demo limits
This is a demonstration prototype, not an official Jakicha Motel system.
It is NOT connected to live room inventory, a property-management system, payment gateway or confirmed hotel policies.
A booking collected by the bot is only a **request pending staff confirmation**.
Room types, facilities and indicative rates are based on third-party listings and must be confirmed by motel management before public use. Replace or remove sample rates in `brain/engine.py` once verified.
The motel has not approved this demo or authorized use of its branding. Obtain permission before public deployment or presenting it as an official service. Until then, label it clearly as a concept demonstration by NCIP Technologies.

## 1. Run locally (browser demo)
Use Python 3.10+.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env
# macOS/Linux: cp .env.example .env
python app.py
```

Open:
- Dashboard: http://127.0.0.1:5000/dashboard
- Health: http://127.0.0.1:5000/health

Login password is `ADMIN_PASSWORD` in `.env`. Change it before running.
To test the assistant, use the **Try the assistant** chat on the dashboard. Gemini key is optional; without it, rule-based replies and booking capture still work.

## 2. Configure Gemini
Set `GEMINI_API_KEY` in `.env`.
Optional model setting: `GEMINI_MODEL=gemini-2.5-flash`.
Restart the app after changing `.env`.

## 3. Connect WhatsApp Cloud API
1. Create/configure a Meta app and WhatsApp product.
2. Add a WhatsApp Business phone number and obtain a permanent/long-lived access token as appropriate.
3. Set `WHATSAPP_TOKEN`, `PHONE_NUMBER_ID`, `VERIFY_TOKEN`, and `GRAPH_VERSION` in `.env`.
4. Deploy this Flask app to a public HTTPS host.
5. In Meta Webhooks, subscribe to the WhatsApp `messages` field and set callback URL to:
   `https://YOUR-DOMAIN/webhook`
6. Enter the exact same `VERIFY_TOKEN` in Meta and `.env`.
7. Send a test message to the connected WhatsApp number.

Meta's test numbers may have recipient allow-list restrictions. Outbound messages outside the allowed customer-service window may require an approved template. The demo currently sends text messages only.

## 4. Human handover
Set `ADMIN_WHATSAPP` to the staff phone number in international digits format, e.g. `2557XXXXXXXX` (no plus sign).
When a guest asks for a person or submits a booking request, the system sends a notification to that number if WhatsApp API credentials are configured.

## 5. Booking flow
Guest sends `BOOK` and bot collects:
- Full name
- Check-in date (YYYY-MM-DD)
- Check-out date (YYYY-MM-DD)
- Number of guests
- Preferred room type
- Extra notes

It stores the request in SQLite and displays it on the dashboard. Staff must verify inventory/rate and then update its status. The bot does not automatically send a final confirmation to the guest when staff changes status in this starter version.

## 6. Before a real customer pilot
- Obtain written approval from Jakicha Motel to use its name, details and branding.
- Verify phone, address, room types, rates, facilities, check-in rules, payment methods and airport transfer terms with management.
- Add live availability/PMS integration if they require instant booking confirmation.
- Add privacy notice, data retention/deletion process and secure hosting.
- Use HTTPS, strong secrets, restricted dashboard access, backups and monitoring.
- Add approved WhatsApp templates for business-initiated messages.
- Test with staff and a small number of invited guests before production.

## Routes
- `GET /webhook` — Meta webhook verification
- `POST /webhook` — inbound WhatsApp events
- `POST /demo-chat` — browser demo chat
- `GET /dashboard/login` — admin login
- `GET /dashboard` — protected dashboard
- `GET /health` — health check

## Files
- `app.py` — Flask app and webhook
- `brain/engine.py` — AI logic and booking conversation
- `brain/storage.py` — SQLite persistence
- `brain/whatsapp.py` — WhatsApp Cloud API send helper
- `templates/` — dashboard pages
- `static/style.css` — dashboard styling
