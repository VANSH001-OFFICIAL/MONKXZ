# config.py
import os

# BOT_TOKEN ko seedhe code mein na likhen.
# Ise Environment Variable "BOT_TOKEN" se load karein.
BOT_TOKEN = os.getenv("BOT_TOKEN") 

# Agar Render par BOT_TOKEN nahi milta hai, toh aap apne PC par test karne ke liye 
# ek local fallback token de sakte hain, lekin ise GitHub par push karne se pehle 
# hata dena behtar hai ya koi fake token rakhna.
# Example: BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_FAKE_LOCAL_TOKEN_FOR_TESTING")
