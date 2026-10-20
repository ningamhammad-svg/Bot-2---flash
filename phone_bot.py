import google.generativeai as genai
def reply_phone(text):
  model = genai.generativeModel('gemini-3.1-flash-lite')
  prompt = f"wewe ni muuza simu "NINGA TELLEPHONE AND ACCESSORIES", jibu kwa kifupi tu. Mteja:{text)"
  return model.generate_content(prompt).text[:400]
