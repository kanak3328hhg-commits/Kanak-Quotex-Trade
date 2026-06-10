import os
import time
from threading import Thread
import yfinance as yf
import requests
from flask import Flask, request, jsonify

# 1. Flask Web Server Setup
app = Flask('')

# পেয়ারের নাম স্থায়ীভাবে সেভ রাখার জন্য ফাইলের নাম
STATE_FILE = "active_pair.txt"

def get_active_pair():
    """ফাইল থেকে বর্তমানে অ্যাক্টিভ পেয়ারের তথ্য পড়ে নিয়ে আসে"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            data = f.read().strip().split(",")
            if len(data) == 2:
                return data[0], data[1]
    return "EURUSD=X", "EURUSD"  # ফাইল না থাকলে ডিফল্ট

def set_active_pair(symbol, display_name):
    """নতুন সিলেক্ট করা পেয়ারের তথ্য ফাইলে লিখে রাখে"""
    with open(STATE_FILE, "w") as f:
        f.write(f"{symbol},{display_name}")

@app.route('/')
def home():
    _, display_name = get_active_pair()
    return f"Bot is running! Current Active Pair: {display_name}"

# telegram বাটন ক্লিকের ডেটা রিসিভ করার জন্য Webhook রুট
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    
    if "callback_query" in data:
        callback_query = data["callback_query"]
        callback_data = callback_query["data"]
        message_id = callback_query["message"]["message_id"]
        
        # ২৮টি পেয়ারের সম্পূর্ণ সঠিক ম্যাপিং ডিকশনারি
        pairs_map = {
            "p_eurusd": ("EURUSD=X", "EURUSD"), "p_gbpusd": ("GBPUSD=X", "GBPUSD"),
            "p_audusd": ("AUDUSD=X", "AUDUSD"), "p_nzdusd": ("NZDUSD=X", "NZDUSD"),
            "p_usdjpy": ("USDJPY=X", "USDJPY"), "p_usdchf": ("USDCHF=X", "USDCHF"),
            "p_usdcad": ("USDCAD=X", "USDCAD"),
            "p_eurgbp": ("EURGBP=X", "EURGBP"), "p_eurjpy": ("EURJPY=X", "EURJPY"),
            "p_eurchf": ("EURCHF=X", "EURCHF"), "p_eurcad": ("EURCAD=X", "EURCAD"),
            "p_euraud": ("EURAUD=X", "EURAUD"), "p_eurnzd": ("EURNZD=X", "EURNZD"),
            "p_gbpjpy": ("GBPJPY=X", "GBPJPY"), "p_gbpchf": ("GBPCHF=X", "GBPCHF"),
            "p_gbpcad": ("GBPCAD=X", "GBPCAD"), "p_gbpaud": ("GBPAUD=X", "GBPAUD"),
            "p_gbpnzd": ("GBPNZD=X", "GBPNZD"),
            "p_audjpy": ("AUDJPY=X", "AUDJPY"), "p_audchf": ("AUDCHF=X", "AUDCHF"),
            "p_audcad": ("AUDCAD=X", "AUDCAD"), "p_audnzd": ("AUDNZD=X", "AUDNZD"),
            "p_nzdjpy": ("NZDJPY=X", "NZDJPY"), "p_nzdchf": ("NZDCHF=X", "NZDCHF"),
            "p_nzdcad": ("NZDCAD=X", "NZDCAD"),
            "p_cadjpy": ("CADJPY=X", "CADJPY"), "p_cadchf": ("CADCHF=X", "CADCHF"),
            "p_chfjpy": ("CHFJPY=X", "CHFJPY")
        }
        
        if callback_data in pairs_map:
            symbol, display_name = pairs_map[callback_data]
            # নতুন পেয়ার ফাইলে সেভ করুন
            set_active_pair(symbol, display_name)
            
            # ১. চ্যানেলে নতুন মেসেজ দিয়ে কনফার্ম করা
            alert_msg = (
                f"⚙️ **Quotex Pair Configuration Update**\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"✅ **Success:** Active Pair Changed!\n"
                f"🎯 **Now Scanning:** `{display_name}`\n"
                f"📊 *বট এখন শুধুমাত্র এই পেয়ারের ICT FVG সিগন্যাল পাঠাবে।*"
            )
            send_telegram_message(alert_msg)
            
            # ২. মূল কন্ট্রোল প্যানেলের বাটনগুলো আপডেট করে সিলেক্টেড পেয়ারের পাশে ✅ বসানো
            update_pair_selection_panel(message_id)
            
            # টেলিগ্রাম ইন্টারনাল রেসপন্স সাকসেস করা
            callback_id = callback_query["id"]
            requests.post(f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery", json={"callback_query_id": callback_id})
            
    return jsonify({"status": "success"})

# 2. Telegram Configurations
TOKEN = os.environ.get("TELEGRAM_TOKEN", "8264008675:AAEHzakAXPZeNVZKWlvYHRWboyjAuUhg0QM") 
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "-1003684590469")

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram Error: {e}")

# ডাইনামিক কিবোর্ড জেনারেটর
def generate_keyboard():
    _, current_display_name = get_active_pair()
    def label(name):
        return f"✅ {name}" if current_display_name == name else name

    keyboard = {
        "inline_keyboard": [
            [{"text": "🔹 USD BASED 🔹", "callback_data": "none"}],
            [
                {"text": label("EURUSD"), "callback_data": "p_eurusd"},
                {"text": label("GBPUSD"), "callback_data": "p_gbpusd"},
                {"text": label("AUDUSD"), "callback_data": "p_audusd"}
            ],
            [
                {"text": label("NZDUSD"), "callback_data": "p_nzdusd"},
                {"text": label("USDJPY"), "callback_data": "p_usdjpy"},
                {"text": label("USDCHF"), "callback_data": "p_usdchf"},
                {"text": label("USDCAD"), "callback_data": "p_usdcad"}
            ],
            [{"text": "🔹 EUR CROSSES 🔹", "callback_data": "none"}],
            [
                {"text": label("EURGBP"), "callback_data": "p_eurgbp"},
                {"text": label("EURJPY"), "callback_data": "p_eurjpy"},
                {"text": label("EURCHF"), "callback_data": "p_eurchf"}
            ],
            [
                {"text": label("EURCAD"), "callback_data": "p_eurcad"},
                {"text": label("EURAUD"), "callback_data": "p_euraud"},
                {"text": label("EURNZD"), "callback_data": "p_eurnzd"}
            ],
            [{"text": "🔹 GBP CROSSES 🔹", "callback_data": "none"}],
            [
                {"text": label("GBPJPY"), "callback_data": "p_gbpjpy"},
                {"text": label("GBPCHF"), "callback_data": "p_gbpchf"},
                {"text": label("GBPCAD"), "callback_data": "p_gbpcad"}
            ],
            [
                {"text": label("GBPAUD"), "callback_data": "p_gbpaud"},
                {"text": label("GBPNZD"), "callback_data": "p_gbpnzd"}
            ],
            [{"text": "🔹 AUD / NZD / CAD / CHF 🔹", "callback_data": "none"}],
            [
                {"text": label("AUDJPY"), "callback_data": "p_audjpy"},
                {"text": label("AUDCHF"), "callback_data": "p_audchf"},
                {"text": label("AUDCAD"), "callback_data": "p_audcad"},
                {"text": label("AUDNZD"), "callback_data": "p_audnzd"}
            ],
            [
                {"text": label("NZDJPY"), "callback_data": "p_nzdjpy"},
                {"text": label("NZDCHF"), "callback_data": "p_nzdchf"},
                {"text": label("NZDCAD"), "callback_data": "p_nzdcad"}
            ],
            [
                {"text": label("CADJPY"), "callback_data": "p_cadjpy"},
                {"text": label("CADCHF"), "callback_data": "p_cadchf"},
                {"text": label("CHFJPY"), "callback_data": "p_chfjpy"}
            ]
        ]
    }
    return keyboard

def send_pair_selection_panel():
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": f"🎛 **Quotex Master Control Panel**\n\nযেকোনো একটি পেয়ার সিলেক্ট করুন। বর্তমানে একটি টিকচিহ্ন (✅) দেখতে পাবেন।",
        "reply_markup": generate_keyboard(),
        "parse_mode": "Markdown"
    }
    try: requests.post(url, json=payload)
    except Exception as e: print(f"Panel Error: {e}")

def update_pair_selection_panel(message_id):
    url = f"https://api.telegram.org/bot{TOKEN}/editMessageReplyMarkup"
    payload = {
        "chat_id": CHAT_ID,
        "message_id": message_id,
        "reply_markup": generate_keyboard()
    }
    try: requests.post(url, json=payload)
    except Exception as e: print(f"Update Panel Error: {e}")

# Webhook কানেকশন সেটআপ
def set_webhook():
    time.sleep(5)
    render_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}.onrender.com/webhook"
    url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={render_url}"
    requests.get(url)
    print(f"Webhook successfully pointed to: {render_url}")

# 3. ICT FVG Strategy Logic
def check_fvg():
    try:
        # প্রতি মিনিটে ফাইল থেকে তাজা পেয়ারের নাম রিড করবে
        current_symbol, display_name = get_active_pair()
        
        ticker = yf.Ticker(current_symbol)
        df = ticker.history(period="3d", interval="1m") # Rate Limit এড়াতে 3d ব্যবহার করা হয়েছে
        
        if df.empty or len(df) < 4:
            return

        c1_high = df['High'].iloc[-4]
        c1_low  = df['Low'].iloc[-4]
        c3_high = df['High'].iloc[-2]
        c3_low  = df['Low'].iloc[-2]
        current_price = df['Close'].iloc[-1]

        # Bullish FVG
        if c1_high < c3_low:
            gap = c3_low - c1_high
            entry_price = c1_high
            msg = (
                f"🟢 **Quotex ICT UP SIGNAL!** ({display_name})\n"
                f"⏱ Timeframe: 1m\n"
                f"📊 Current Price: {current_price:.5f}\n"
                f"🎯 **Best Entry Price: {entry_price:.5f}** (or below)\n"
                f"📐 Gap Size: {gap:.5f}"
            )
            send_telegram_message(msg)

        # Bearish FVG
        elif c1_low > c3_high:
            gap = c1_low - c3_high
            entry_price = c1_low
            msg = (
                f"🔴 **Quotex ICT DOWN SIGNAL!** ({display_name})\n"
                f"⏱ Timeframe: 1m\n"
                f"📊 Current Price: {current_price:.5f}\n"
                f"🎯 **Best Entry Price: {entry_price:.5f}** (or above)\n"
                f"📐 Gap Size: {gap:.5f}"
            )
            send_telegram_message(msg)
            
    except Exception as e:
        print(f"Data Fetch Error: {e}")

# 4. Main Bot Loop
def bot_loop():
    print("Trading Bot Loop Started...")
    send_telegram_message("🚀 Quotex 28-Pair FVG Control Bot with Live Alerts is LIVE!")
    send_pair_selection_panel()
    
    while True:
        check_fvg()
        time.sleep(60) 

def start_background_tasks():
    t1 = Thread(target=bot_loop)
    t1.daemon = True
    t1.start()
    
    t2 = Thread(target=set_webhook)
    t2.daemon = True
    t2.start()

@app.before_request
def initialize():
    if not getattr(app, '_tasks_started', False):
        start_background_tasks()
        app._tasks_started = True

if __name__ == "__main__":
    start_background_tasks()
    from werkzeug.serving import make_server
    port = int(os.environ.get("PORT", 8080))
    srv = make_server('0.0.0.0', port, app)
    srv.serve_forever()
