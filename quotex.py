import os
import time
from threading import Thread
import yfinance as yf
import requests
from flask import Flask, request, jsonify

# 1. Flask Web Server Setup
app = Flask('')

# গ্লোবাল ভেরিয়েবল (ডিফল্ট পেয়ার হিসেবে EURUSD থাকবে)
CURRENT_SYMBOL = "EURUSD=X"
SYMBOL_DISPLAY_NAME = "EURUSD"

@app.route('/')
def home():
    return f"Bot is running! Current Active Pair: {SYMBOL_DISPLAY_NAME}"

# টেলিগ্রাম বাটন ক্লিকের ডেটা রিসিভ করার জন্য Webhook রুট
@app.route('/webhook', methods=['POST'])
def webhook():
    global CURRENT_SYMBOL, SYMBOL_DISPLAY_NAME
    data = request.get_json()
    
    if "callback_query" in data:
        callback_query = data["callback_query"]
        callback_data = callback_query["data"]
        
        # ২৮টি পেয়ারের সম্পূর্ণ ম্যাপিং ডিকশনারি
        pairs_map = {
            # USD-Based
            "p_eurusd": ("EURUSD=X", "EURUSD"), "p_gbpusd": ("GBPUSD=X", "GBPUSD"),
            "p_audusd": ("AUDUSD=X", "AUDUSD"), "p_nzdusd": ("NZDUSD=X", "NZDUSD"),
            "p_usdjpy": ("USDJPY=X", "USDJPY"), "p_usdchf": ("USDCHF=X", "USDCHF"),
            "p_usdcad": ("USDCAD=X", "USDCAD"),
            # EUR Crosses
            "p_eurgbp": ("EURGBP=X", "EURGBP"), "p_eurjpy": ("EURJPY=X", "EURJPY"),
            "p_eurchf": ("EURCHF=X", "EURCHF"), "p_eurcad": ("EURCAD=X", "EURCAD"),
            "p_euraud": ("EURAUD=X", "EURAUD"), "p_eurnzd": ("EURNZD=X", "EURNZD"),
            # GBP Crosses
            "p_gbpjpy": ("GBPJPY=X", "GBPJPY"), "p_gbpchf": ("GBPCHF=X", "GBPCHF"),
            "p_gbpcad": ("GBPCAD=X", "GBPCAD"), "p_gbpaud": ("GBPAUD=X", "GBPAUD"),
            "p_gbpnzd": ("GBPNZD=X", "GBPNZD"),
            # AUD Crosses
            "p_audjpy": ("AUDJPY=X", "AUDJPY"), "p_audchf": ("AUDCHF=X", "AUDCHF"),
            "p_audcad": ("AUDCAD=X", "AUDCAD"), "p_audnzd": ("AUDNZD=X", "AUDNZD"),
            # NZD Crosses
            "p_nzdjpy": ("NZDJPY=X", "NZDJPY"), "p_nzdchf": ("NZDCHF=X", "NZDCHF"),
            "p_nzdcad": ("NZDCAD=X", "NZDCAD"),
            # CAD Crosses
            "p_cadjpy": ("CADJPY=X", "CADJPY"), "p_cadchf": ("CADCHF=X", "CADCHF"),
            # CHF Cross
            "p_chfjpy": ("CHFJPY=X", "CHFJPY")
        }
        
        if callback_data in pairs_map:
            CURRENT_SYMBOL, SYMBOL_DISPLAY_NAME = pairs_map[callback_data]
            
            # 📢 চ্যানেলে একটি সুন্দর নতুন মেসেজ পাঠিয়ে কনফার্ম করা (যাতে আপনি বুঝতে পারেন)
            alert_msg = (
                f"⚙️ **Quotex Pair Configuration Update**\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"✅ **Success:** Active Pair Changed!\n"
                f"🎯 **Now Scanning:** `{SYMBOL_DISPLAY_NAME}`\n"
                f"📊 *বট এখন শুধুমাত্র এই পেয়ারের ICT FVG সিগন্যাল পাঠাবে।*"
            )
            send_telegram_message(alert_msg)
            
            # টেলিগ্রামকে ইন্টারনাল কনফার্মেশন পাঠানো (এরর এড়ানোর জন্য)
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

# সম্পূর্ণ ২৮টি পেয়ারের বাটন প্যানেল তৈরি
def send_pair_selection_panel():
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    keyboard = {
        "inline_keyboard": [
            # --- USD Based ---
            [{"text": "🔹 USD BASED 🔹", "callback_data": "none"}],
            [
                {"text": "EURUSD", "callback_data": "p_eurusd"},
                {"text": "GBPUSD", "callback_data": "p_gbpusd"},
                {"text": "AUDUSD", "callback_data": "p_audusd"}
            ],
            [
                {"text": "NZDUSD", "callback_data": "p_nzdusd"},
                {"text": "USDJPY", "callback_data": "p_usdjpy"},
                {"text": "USDCHF", "callback_data": "p_usdchf"},
                {"text": "USDCAD", "callback_data": "p_usdcad"}
            ],
            # --- EUR Crosses ---
            [{"text": "🔹 EUR CROSSES 🔹", "callback_data": "none"}],
            [
                {"text": "EURGBP", "callback_data": "p_eurgbp"},
                {"text": "EURJPY", "callback_data": "p_eurjpy"},
                {"text": "EURCHF", "callback_data": "p_eurchf"}
            ],
            [
                {"text": "EURCAD", "callback_data": "p_eurcad"},
                {"text": "EURAUD", "callback_data": "p_euraud"},
                {"text": "EURNZD", "callback_data": "p_eurnzd"}
            ],
            # --- GBP Crosses ---
            [{"text": "🔹 GBP CROSSES 🔹", "callback_data": "none"}],
            [
                {"text": "GBPJPY", "callback_data": "p_gbpjpy"},
                {"text": "GBPCHF", "callback_data": "p_gbpchf"},
                {"text": "GBPCAD", "callback_data": "p_gbpcad"}
            ],
            [
                {"text": "GBPAUD", "callback_data": "p_gbpaud"},
                {"text": "GBPNZD", "callback_data": "p_gbpnzd"}
            ],
            # --- Other Crosses ---
            [{"text": "🔹 AUD / NZD / CAD / CHF 🔹", "callback_data": "none"}],
            [
                {"text": "AUDJPY", "callback_data": "p_audjpy"},
                {"text": "AUDCHF", "callback_data": "p_audchf"},
                {"text": "AUDCAD", "callback_data": "p_audcad"},
                {"text": "AUDNZD", "callback_data": "p_audnzd"}
            ],
            [
                {"text": "NZDJPY", "callback_data": "p_nzdjpy"},
                {"text": "NZDCHF", "callback_data": "p_nzdchf"},
                {"text": "NZDCAD", "callback_data": "p_nzdcad"}
            ],
            [
                {"text": "CADJPY", "callback_data": "p_cadjpy"},
                {"text": "CADCHF", "callback_data": "p_cadchf"},
                {"text": "CHFJPY", "callback_data": "p_chfjpy"}
            ]
        ]
    }
    
    payload = {
        "chat_id": CHAT_ID,
        "text": "🎛 **Quotex Master Control Panel**\n\nযেকোনো একটি পেয়ার সিলেক্ট করুন। বট তাৎক্ষণিকভাবে শুধুমাত্র ওই পেয়ারটি স্ক্যান করা শুরু করবে এবং বাকি সব পেয়ারের মেসেজ পাঠানো বন্ধ রাখবে।",
        "reply_markup": keyboard,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Panel Error: {e}")

# Webhook কানেকশন সেটআপ
def set_webhook():
    time.sleep(5)
    render_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}.onrender.com/webhook"
    url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={render_url}"
    requests.get(url)
    print(f"Webhook successfully pointed to: {render_url}")

# 3. ICT FVG Strategy Logic
def check_fvg():
    global CURRENT_SYMBOL, SYMBOL_DISPLAY_NAME
    try:
        # বর্তমানে সিলেক্ট থাকা টোকেনটি রিড করা
        ticker = yf.Ticker(CURRENT_SYMBOL)
        df = ticker.history(period="1d", interval="1m")
        
        if len(df) < 4:
            return

        c1_high = df['High'].iloc[-4]
        c1_low  = df['Low'].iloc[-4]
        c3_high = df['High'].iloc[-2]
        c3_low  = df['Low'].iloc[-2]
        current_price = df['Close'].iloc[-1]

        # Bullish FVG (UP)
        if c1_high < c3_low:
            gap = c3_low - c1_high
            entry_price = c1_high
            msg = (
                f"🟢 **Quotex ICT UP SIGNAL!** ({SYMBOL_DISPLAY_NAME})\n"
                f"⏱ Timeframe: 1m\n"
                f"📊 Current Price: {current_price:.5f}\n"
                f"🎯 **Best Entry Price: {entry_price:.5f}** (or below)\n"
                f"📐 Gap Size: {gap:.5f}"
            )
            send_telegram_message(msg)

        # Bearish FVG (DOWN)
        elif c1_low > c3_high:
            gap = c1_low - c3_high
            entry_price = c1_low
            msg = (
                f"🔴 **Quotex ICT DOWN SIGNAL!** ({SYMBOL_DISPLAY_NAME})\n"
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

if __name__ == "__main__":
    t1 = Thread(target=bot_loop)
    t1.start()
    
    t2 = Thread(target=set_webhook)
    t2.start()
    
    from werkzeug.serving import make_server
    port = int(os.environ.get("PORT", 8080))
    srv = make_server('0.0.0.0', port, app)
    srv.serve_forever()
