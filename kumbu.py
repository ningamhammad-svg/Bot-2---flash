# kumbu.py - Kumbukumbu ya bot
import json
import os

FILE = "memory.json"
MAX_MSG = 12  # 12 = sms 6 za mteja + 6 za bot. Ukisema 5-6 za mwisho, hii ndio sahihi

class Kumbukumbu:
    def __init__(self):
        self.data = self._load()

    def _load(self):
        if os.path.exists(FILE):
            try:
                with open(FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # hakikisha paused_users ipo, isifutwe
                    if "paused_users" not in data:
                        data["paused_users"] = {}
                    return data
            except:
                return {"paused_users": {}}
        return {"paused_users": {}}

    def _save(self):
        with open(FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def add_message(self, from_num, role, text):
        # role ni "user" au "bot"
        if from_num not in self.data:
            self.data[from_num] = []
        self.data[from_num].append({"role": role, "text": text})
        # baki na 12 za mwisho tu, zingine zifute ili file isijaze
        self.data[from_num] = self.data[from_num][-MAX_MSG:]
        self._save()

    def get_history(self, from_num):
        # hii ndio AI inaitumia kukumbuka
        # inarudisha list ya mfano: [{"role": "user", "text": "mimi ni john"}, ...]
        return self.data.get(from_num, [])[-MAX_MSG:]

    def get_history_text(self, from_num):
        # hii ni rahisi kuweka kwenye prompt ya AI
        # inarudisha mfano: "Mteja: mimi ni john\nBot: Karibu John..."
        history = self.get_history(from_num)
        lines = []
        for h in history:
            jina = "Mteja" if h["role"] == "user" else "Bot"
            lines.append(f"{jina}: {h['text']}")
        return "\n".join(lines)

    def clear(self, from_num):
        if from_num in self.data:
            self.data[from_num] = []
            self._save()

# hii ndio utakayoi-import kwenye bot yako
memory = Kumbukumbu()
