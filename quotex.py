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
        message_id = callback_query["message"]["message_id"]
        
        # ২৮টি পেয়ারের সম্পূর্ণ সঠিক ম্যাপিং ডিকশনারি
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
            CURRENT_SYMBOL, SYMBOL_DISPLAY_NAME = pairs_map[callback_data]
            
            # ১. চ্যানেলে নতুন মেসেজ দিয়ে কনফার্ম করা
            alert_msg = (
                f"⚙️ **Quotex Pair Configuration Update**\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"✅ **Success:** Active Pair Changed!\n"
                f"🎯 **Now Scanning:** `{SYMBOL_DISPLAY_NAME}`\n"
                f"📊 *বট এখন শুধুমাত্র এই পেয়ারের ICT FVG সিগন্যাল পাঠাবে।*"
            )
            send_telegram_message(alert_msg)
            
            # ২. মূল কন্ট্রোল প্যানেলের বাটনগুলো আপডেট করে সিলেক্টেড পেয়ারের পাশে ✅ বসানো
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
    def label(name):
        return f"✅ {name}" if SYMBOL_DISPLAY_NAME == name else name

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
        "text": f"🎛 **Quotex Master Control Panel**\n\nযেকোনো একটি পেয়ার সিলেক্ট করুন। বর্তমানে্যাক্টিভ পেয়ারের পাশে একটি টিকচিহ্ন (✅) দেখতে পাবেন।",
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
    global CURRENT_SYMBOL, SYMBOL_DISPLAY_NAME
    try:
        ticker = yf.Ticker(CURRENT_SYMBOL)
        df = ticker.history(period="1d", interval="1m")
        
        if len(df) < 4:
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
                f"🟢 **Quotex ICT UP SIGNAL!** ({SYMBOL_DISPLAY_NAME})\n"
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
