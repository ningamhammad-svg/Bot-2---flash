import google.generativeai as genai
def reply_nguo(text):
  model = genai.generativeModel('gemini-3.1-flash-lite')
  prompt = f"wewe ni muuza nguo 'PENDEZA NA NINGA FASHION', jibu kwa kifupi tu. Mteja:{text}"
  return model.generate_content(prompt).text[:400]
