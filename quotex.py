import os
import time
from threading import Thread
import yfinance as yf
import requests
from flask import Flask, request, jsonify

# 1. Flask Web Server Setup
app = Flask('')

# ২৮টি ভ্যালিড পেয়ারের তালিকা
VALID_PAIRS = {
    "EURUSD": "EURUSD=X", "GBPUSD": "GBPUSD=X", "AUDUSD": "AUDUSD=X", "NZDUSD": "NZDUSD=X",
    "USDJPY": "USDJPY=X", "USDCHF": "USDCHF=X", "USDCAD": "USDCAD=X", "EURGBP": "EURGBP=X",
    "EURJPY": "EURJPY=X", "EURCHF": "EURCHF=X", "EURCAD": "EURCAD=X", "EURAUD": "EURAUD=X",
    "EURNZD": "EURNZD=X", "GBPJPY": "GBPJPY=X", "GBPCHF": "GBPCHF=X", "GBPCAD": "GBPCAD=X",
    "GBPAUD": "GBPAUD=X", "GBPNZD": "GBPNZD=X", "AUDJPY": "AUDJPY=X", "AUDCHF": "AUDCHF=X",
    "AUDCAD": "AUDCAD=X", "AUDNZD": "AUDNZD=X", "NZDJPY": "NZDJPY=X", "NZDCHF": "NZDCHF=X",
    "NZDCAD": "NZDCAD=X", "CADJPY": "CADJPY=X", "CADCHF": "CADCHF=X", "CHFJPY": "CHFJPY=X"
}

# গ্লোবাল ভেরিয়বল (র্যাম মেমোরি)
CURRENT_SYMBOL = "EURUSD=X"
SYMBOL_DISPLAY_NAME = "EURUSD"

# 2. Telegram Configurations
TOKEN = os.environ.get("TELEGRAM_TOKEN", "8264008675:AAEHzakAXPZeNVZKWlvYHRWboyjAuUhg0QM") 
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "-1003684590469")
RENDER_URL = "https://kanak-quotex-trade.onrender.com/webhook"

@app.route('/')
def home():
    global SYMBOL_DISPLAY_NAME
    return f"Bot is running! Current Active Pair: {SYMBOL_DISPLAY_NAME}"

# স্বয়ংক্রিয় Webhook সেটআপ ফাংশন (যা এখন অটোমেটিক কাজ করবে)
def auto_refresh_webhook():
    """টেলিগ্রামের Webhook লিংক অটোমেটিক রিফ্রেশ করার ফাংশন"""
    url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={RENDER_URL}"
    try:
        response = requests.get(url, timeout=10)
        print(f"🤖 [Auto-Webhook] Refreshed: {response.json()}")
    except Exception as e:
        print(f"❌ [Auto-Webhook] Error: {e}")

# টেলিগ্রাম থেকে চ্যানেলের নতুন মেসেজ রিসিভ করার রুট
@app.route('/webhook', methods=['POST'])
def webhook():
    global CURRENT_SYMBOL, SYMBOL_DISPLAY_NAME
    data = request.get_json()
    
    if "channel_post" in data:
        post = data["channel_post"]
        text = post.get("text", "").strip().upper()
        
        if text in VALID_PAIRS:
            CURRENT_SYMBOL = VALID_PAIRS[text]
            SYMBOL_DISPLAY_NAME = text
            
            confirm_msg = (
                f"⚙️ **Quotex Pair Configuration Update**\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"✅ **Success:** Active Pair Changed!\n"
                f"🎯 **Now Scanning:** `{text}`\n"
                f"📊 *বট এখন শুধুমাত্র এই পেয়ারের ICT FVG সিগন্যাল পাঠাবে।*"
            )
            send_telegram_message(confirm_msg)
            
            # 🔥 ম্যাজিক: পেয়ার চেঞ্জ হওয়া মাত্রই ব্যাকগ্রাউন্ডে অটো-রিফ্রেশ কল হবে
            auto_refresh_webhook()
            
    return jsonify({"status": "success"})

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload)
    except Exception as e: print(f"Telegram Error: {e}")

# 3. ICT FVG Strategy Logic
def check_fvg():
    global CURRENT_SYMBOL, SYMBOL_DISPLAY_NAME
    try:
        symbol_to_scan = CURRENT_SYMBOL
        display_name_to_scan = SYMBOL_DISPLAY_NAME
        
        ticker = yf.Ticker(symbol_to_scan)
        df = ticker.history(period="3d", interval="1m")
        
        if df.empty or len(df) < 4:
            send_telegram_message(f"⚠️ **{display_name_to_scan}**: Data fetching error. Retrying next minute...")
            return

        c1_high = df['High'].iloc[-4]
        c1_low  = df['Low'].iloc[-4]
        c3_high = df['High'].iloc[-2]
        c3_low  = df['Low'].iloc[-2]
        current_price = df['Close'].iloc[-1]

        # ১. Bullish FVG
        if c1_high < c3_low:
            gap = c3_low - c1_high
            entry_price = c1_high
            msg = (
                f"🟢 **Quotex ICT UP SIGNAL!** ({display_name_to_scan})\n"
                f"⏱ Timeframe: 1m\n"
                f"📊 Current Price: {current_price:.5f}\n"
                f"🎯 **Best Entry Price: {entry_price:.5f}** (or below)\n"
                f"📐 Gap Size: {gap:.5f}"
            )
            send_telegram_message(msg)

        # ২. Bearish FVG
        elif c1_low > c3_high:
            gap = c1_low - c3_high
            entry_price = c1_low
            msg = (
                f"🔴 **Quotex ICT DOWN SIGNAL!** ({display_name_to_scan})\n"
                f"⏱ Timeframe: 1m\n"
                f"📊 Current Price: {current_price:.5f}\n"
                f"🎯 **Best Entry Price: {entry_price:.5f}** (or above)\n"
                f"📐 Gap Size: {gap:.5f}"
            )
            send_telegram_message(msg)
            
        # ৩. কোনো সিগন্যাল না থাকলে
        else:
            no_signal_msg = (
                f"❌ **Quotex Signal Status** ({display_name_to_scan})\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📢 **Status:** No Signal Available Right Now!\n"
                f"⏳ *বট পরবর্তী মিনিটে আবার মার্কেট স্ক্যান করবে।* \n"
                f"📊 Current Price: {current_price:.5f}"
            )
            send_telegram_message(no_signal_msg)
            
    except Exception as e:
        print(f"Data Fetch Error: {e}")
        
# 4. Main Bot Loop
def bot_loop():
    print("Trading Bot Loop Started...")
    send_telegram_message("🚀 Quotex FVG Control Bot is LIVE!\n\n👉 পেয়ার পরিবর্তন করতে চ্যানেলে পেয়ারের নাম লিখুন (যেমন: GBPUSD)")
    
    # প্রথমবার চালুর সময় একবার অটো-লিংক রিসেট করে নেবে
    auto_refresh_webhook()
    
    while True:
        try:
            check_fvg()
        except Exception as loop_err:
            print(f"Loop function error: {loop_err}")
        
        # প্রতি ৫ম মিনিটে ব্যাকগ্রাউন্ডে অটো-লিংক রিফ্রেশ হবে যেন রাস্তা কখনো ব্লক না হয়
        if int(time.time()) % 300 < 60:
            auto_refresh_webhook()
            
        time.sleep(60) 

if __name__ == "__main__":
    t1 = Thread(target=bot_loop, daemon=True)
    t1.start()
    
    # মূল থ্রেডে ফ্ল্যাস্ক সার্ভার চালু
    from werkzeug.serving import make_server
    port = int(os.environ.get("PORT", 8080))
    srv = make_server('0.0.0.0', port, app)
    srv.serve_forever()
