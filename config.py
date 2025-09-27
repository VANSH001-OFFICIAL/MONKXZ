# config.py
import os

# Read BOT_TOKEN from the environment variable set on Render
# If not found (e.g., during local testing), it uses a default.
BOT_TOKEN = os.getenv("BOT_TOKEN", "8452992501:AAGiXpTsmgN8oOKkhECTHaOvGkZ4R6v3FR8") 

# If you have other static variables:
# ADMIN_USER_IDS is now managed via 'admin_ids.json' for dynamic updates.
# If you need to keep a static list for initial setup, you can do so, 
# but the code will rely on admin_ids.json after the first run.
