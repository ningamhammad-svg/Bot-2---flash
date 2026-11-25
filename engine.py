import os
import re
from google import genai
from google.genai import types
from .storage import get_session, set_session, create_booking
from .whatsapp import send_whatsapp_message

HOTEL_INFO = """
BUSINESS: Jakicha Motel (DEMO PROFILE)
LOCATION: Kitunda Road, Kitunda Relini, Dar es Salaam, Tanzania.
PUBLIC CONTACT LISTED IN DIRECTORY: +255 742 796 931.
FACILITIES LISTED ONLINE: accommodation, restaurant, bar, swimming pool, garden,
parking, Wi-Fi, room service, laundry and airport transfer. Availability of each
service must be reconfirmed with hotel staff.
ROOM TYPES LISTED ONLINE: Deluxe Double Room, Deluxe Single Room,
Deluxe Double Room with Balcony, Deluxe Single Room with Balcony, Deluxe Bungalow.
INDICATIVE THIRD-PARTY LISTING PRICES ONLY (NOT VERIFIED OFFICIAL RATES):
some listings show approximately TZS 90,750 to TZS 100,100 per night.
Never promise these rates or room availability. Always tell guests to confirm
current prices and availability with reception.
IMPORTANT: This is a sales demonstration prototype, not connected to the hotel's
live property-management/room inventory system. It can collect booking requests
but cannot confirm a room reservation.
"""
SYSTEM_PROMPT = f"""
You are Jakicha AI Hotel Assistant, a polite hotel guest-support assistant.
Reply in the language used by the guest. You can communicate in Swahili, English,
French and Arabic. Keep replies concise, welcoming and clear.
Use only these business facts:
{HOTEL_INFO}
Never invent prices, room availability, policies, check-in/check-out times,
payment methods, exact address directions, or facilities. If unsure, say reception
will confirm. Do not claim a booking is confirmed. Explain that a booking request
has been received and is pending staff confirmation.
If a guest asks for a human, staff member, receptionist, manager, complaint,
urgent help or a complex matter, politely say you are forwarding the request.
Do not provide medical, legal or financial advice.
"""


class HotelAssistant:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None
        self.admin_phone = os.getenv("ADMIN_WHATSAPP", "").strip()

    def _notify_staff(self, phone, reason):
        if self.admin_phone:
            send_whatsapp_message(
                self.admin_phone,
                f"JAKICHA DEMO - Human handover request\nGuest: {phone}\nReason: {reason}\nPlease contact the guest."
            )

    def _human_handover(self, phone, message):
        self._notify_staff(phone, message)
        return ("Nimepokea ombi lako. Nitapeleka ujumbe huu kwa timu ya mapokezi "
                "ili wakusaidie. Tafadhali subiri au wasiliana na mapokezi moja kwa moja.")

    def _booking_flow(self, phone, message, guest_name):
        state, data = get_session(phone)
        text = message.strip()
        if text.lower() in {"cancel", "stop", "acha", "ghairi", "futa"}:
            set_session(phone, "idle", {})
            return "Sawa, ombi la booking limesitishwa. Ukiwa tayari, andika BOOK kuanza tena."

        if state == "booking_name":
            data["guest_name"] = text
            set_session(phone, "booking_checkin", data)
            return "Asante. Unapanga kuingia tarehe gani? Andika YYYY-MM-DD (mfano 2026-12-01)."

        if state == "booking_checkin":
            if not self._valid_date(text):
                return "Tafadhali weka tarehe sahihi kwa muundo YYYY-MM-DD (mfano 2026-12-01)."
            data["checkin"] = text
            set_session(phone, "booking_checkout", data)
            return "Unapanga kutoka tarehe gani? Andika YYYY-MM-DD."

        if state == "booking_checkout":
            if not self._valid_date(text) or text <= data.get("checkin", ""):
                return "Tarehe ya kutoka lazima iwe baada ya tarehe ya kuingia. Weka YYYY-MM-DD."
            data["checkout"] = text
            set_session(phone, "booking_guests", data)
            return "Wageni wangapi? (mfano 1, 2, 3)"

        if state == "booking_guests":
            if not text.isdigit() or not (1 <= int(text) <= 20):
                return "Tafadhali weka idadi ya wageni kwa namba kati ya 1 na 20."
            data["guests"] = text
            set_session(phone, "booking_room", data)
            return ("Unapendelea chumba gani?\n1. Deluxe Single\n2. Deluxe Double\n"
                    "3. Deluxe Double with Balcony\n4. Deluxe Single with Balcony\n5. Deluxe Bungalow\n"
                    "Au andika 'sina upendeleo'.")

        if state == "booking_room":
            data["room_type"] = text
            set_session(phone, "booking_notes", data)
            return "Una maelezo maalum au ombi la ziada? Kama hakuna, andika HAPANA."

        if state == "booking_notes":
            data["notes"] = "" if text.lower() in {"hapana", "no", "none"} else text
            booking_id = create_booking(phone, data.get("guest_name", guest_name or "Guest"), data)
            set_session(phone, "idle", {})
            self._notify_staff(phone, f"New booking request #{booking_id}: {data}")
            return (f"Asante {data.get('guest_name','')}. Ombi lako la booking limepokelewa "
                    f"(Ref: JK-{booking_id:04d}) na linasubiri uthibitisho wa mapokezi. "
                    "Hii si booking iliyothibitishwa. Timu itathibitisha upatikanaji na bei.")
        return None

    @staticmethod
    def _valid_date(value):
        return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value))

    def reply(self, phone, message, guest_name=""):
        text = message.strip()
        lower = text.lower()
        state, _ = get_session(phone)

        if state.startswith("booking_"):
            return self._booking_flow(phone, text, guest_name)

        if lower in {"hi", "hello", "hey", "habari", "mambo", "hujambo", "start", "menu"}:
            return ("Karibu Jakicha Motel! 😊 Mimi ni Jakicha AI Assistant.\n\n"
                    "Naweza kukusaidia kuhusu:\n"
                    "1. Vyumba na huduma\n2. Bei na upatikanaji\n3. Booking request\n"
                    "4. Restaurant / swimming pool\n5. Airport transfer\n6. Kuongea na mtu\n\n"
                    "Andika BOOK kuomba chumba, au niulize swali lako.")

        if lower in {"book", "booking", "reserve", "reservation", "nafanya booking", "naomba chumba"}:
            set_session(phone, "booking_name", {})
            return "Karibu! Tuanze booking request. Tafadhali niambie jina lako kamili."

        if any(k in lower for k in ["human", "person", "reception", "receptionist", "manager", "mtu", "mapokezi", "meneja", "malalamiko", "complaint"]):
            return self._human_handover(phone, text)

        if any(k in lower for k in ["price", "bei", "gharama", "how much", "rate"]):
            return ("Bei hutegemea aina ya chumba na tarehe. Baadhi ya tovuti za booking "
                    "zimeonyesha bei elekezi za takriban TZS 90,750–100,100 kwa usiku, "
                    "lakini hizi si bei rasmi zilizothibitishwa. Tafadhali niambie tarehe "
                    "na aina ya chumba; mapokezi yatathibitisha bei ya sasa.")

        if self.client:
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=f"Guest name: {guest_name or 'Not provided'}\nGuest phone: {phone}\nGuest message: {text}",
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.35,
                        max_output_tokens=450
                    )
                )
                answer = (response.text or "").strip()
                if answer:
                    return answer
            except Exception:
                pass

        # Useful fallback if Gemini is not configured or temporarily unavailable.
        if any(k in lower for k in ["room", "chumba", "accommodation", "vyumba"]):
            return ("Jakicha Motel inaorodhesha Deluxe Single, Deluxe Double, vyumba vyenye balcony "
                    "na Deluxe Bungalow. Tafadhali niambie tarehe zako ili nipokee booking request. "
                    "Mapokezi yatathibitisha upatikanaji.")
        if any(k in lower for k in ["pool", "swimming", "restaurant", "chakula", "food", "bar"]):
            return ("Taarifa za mtandaoni zinataja swimming pool, restaurant na bar. "
                    "Kwa saa za huduma na upatikanaji wa sasa, mapokezi yatahakikisha.")
        if any(k in lower for k in ["airport", "uwanja", "transfer", "pickup", "usafiri"]):
            return ("Airport transfer imetajwa kwenye baadhi ya listings. Tafadhali tuma "
                    "tarehe, muda wa kutua na idadi ya wageni; mapokezi yatathibitisha "
                    "upatikanaji na gharama.")
        return ("Asante kwa kuwasiliana na Jakicha Motel. Naweza kusaidia kuhusu vyumba, "
                "booking request, restaurant, swimming pool na airport transfer. "
                "Kwa taarifa ambazo sijathibitisha, nitakuunganisha na mapokezi. "
                "Andika BOOK kuanza booking request.")
