import os
import time
from threading import Thread
import yfinance as yf
import requests
from flask import Flask, request, jsonify

# 1. Flask Web Server Setup (Render-কে বাঁচিয়ে রাখার জন্য)
app = Flask('')

# ২৮টি ভ্যালিড পেয়ারের তালিকা (যা আপনি চ্যানেলে লিখতে পারবেন)
VALID_PAIRS = {
    "EURUSD": "EURUSD=X", "GBPUSD": "GBPUSD=X", "AUDUSD": "AUDUSD=X", "NZDUSD": "NZDUSD=X",
    "USDJPY": "USDJPY=X", "USDCHF": "USDCHF=X", "USDCAD": "USDCAD=X", "EURGBP": "EURGBP=X",
    "EURJPY": "EURJPY=X", "EURCHF": "EURCHF=X", "EURCAD": "EURCAD=X", "EURAUD": "EURAUD=X",
    "EURNZD": "EURNZD=X", "GBPJPY": "GBPJPY=X", "GBPCHF": "GBPCHF=X", "GBPCAD": "GBPCAD=X",
    "GBPAUD": "GBPAUD=X", "GBPNZD": "GBPNZD=X", "AUDJPY": "AUDJPY=X", "AUDCHF": "AUDCHF=X",
    "AUDCAD": "AUDCAD=X", "AUDNZD": "AUDNZD=X", "NZDJPY": "NZDJPY=X", "NZDCHF": "NZDCHF=X",
    "NZDCAD": "NZDCAD=X", "CADJPY": "CADJPY=X", "CADCHF": "CADCHF=X", "CHFJPY": "CHFJPY=X"
}

STATE_FILE = "active_pair.txt"

def get_active_pair():
    """ফাইল থেকে একটিভ পেয়ারের তথ্য পড়ে নিয়ে আসে"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            data = f.read().strip().split(",")
            if len(data) == 2:
                return data[0], data[1]
    return "EURUSD=X", "EURUSD"

def set_active_pair(symbol, display_name):
    """নতুন সিলেক্ট করা পেয়ার ফাইলে লিখে রাখে"""
    with open(STATE_FILE, "w") as f:
        f.write(f"{symbol},{display_name}")

@app.route('/')
def home():
    _, display_name = get_active_pair()
    return f"Bot is running! Current Active Pair: {display_name}"

# টেলিগ্রাম থেকে চ্যানেলের নতুন মেসেজ রিসিভ করার রুট
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    
    # চ্যানেলে কোনো নতুন পোস্ট বা মেসেজ আসলে
    if "channel_post" in data:
        post = data["channel_post"]
        text = post.get("text", "").strip().upper() # ছোট হাতের লিখলেও বড় হাতের করে নেবে
        
        # লেখাটি আমাদের ২৮টি পেয়ারের তালিকার সাথে মিলছে কিনা চেক
        if text in VALID_PAIRS:
            symbol = VALID_PAIRS[text]
            set_active_pair(symbol, text)
            
            # চ্যানেলে কনফার্মেশন মেসেজ পাঠানো
            confirm_msg = (
                f"⚙️ **Quotex Pair Configuration Update**\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"✅ **Success:** Active Pair Changed!\n"
                f"🎯 **Now Scanning:** `{text}`\n"
                f"📊 *বট এখন শুধুমাত্র এই পেয়ারের ICT FVG সিগন্যাল পাঠাবে।*"
            )
            send_telegram_message(confirm_msg)
        else:
            # পেয়ার বাদে অন্য কিছু লিখলে বা কোনো সিগন্যাল মেসেজ আসলে তা ইগনোর করবে (কিছুই করবে না)
            pass
            
    return jsonify({"status": "success"})


# 2. Telegram Configurations
TOKEN = os.environ.get("TELEGRAM_TOKEN", "8264008675:AAEHzakAXPZeNVZKWlvYHRWboyjAuUhg0QM") 
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "-1003684590469")


def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload)
    except Exception as e: print(f"Telegram Error: {e}")

# Webhook সেটআপ
def set_webhook():
    time.sleep(5)
    render_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}.onrender.com/webhook"
    url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={render_url}"
    requests.get(url)
    print(f"Webhook connected to: {render_url}")

# 3. ICT FVG Strategy Logic
# আপনার কোডের এই ফাংশনটুকু শুধু বদলে দিন
def check_fvg():
    try:
        # প্রতি মিনিটে ফাইল থেকে অ্যাক্টিভ পেয়ারের নাম রিড করবে
        current_symbol, display_name = get_active_pair()
        
        ticker = yf.Ticker(current_symbol)
        df = ticker.history(period="3d", interval="1m") # Rate Limit এড়াতে 3d বাফার
        
        if df.empty or len(df) < 4:
            # যদি কোনো কারণে ডাটা ফেচ না হয়
            send_telegram_message(f"⚠️ **{display_name}**: Data fetching error. Retrying next minute...")
            return

        c1_high = df['High'].iloc[-4]
        c1_low  = df['Low'].iloc[-4]
        c3_high = df['High'].iloc[-2]
        c3_low  = df['Low'].iloc[-2]
        current_price = df['Close'].iloc[-1]

        # ১. Bullish FVG (UP Signal Check)
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

        # ২. Bearish FVG (DOWN Signal Check)
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
            
        # ৩. যদি কোনো সিগন্যাল না থাকে (আপনার নতুন রিকোয়েস্ট)
        else:
            no_signal_msg = (
                f"❌ **Quotex Signal Status** ({display_name})\n"
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
    
    while True:
        check_fvg()
        time.sleep(60) 

if __name__ == "__main__":
    # ব্যাকগ্রাউন্ড টাস্ক চালু করা
    t1 = Thread(target=bot_loop)
    t1.start()
    
    t2 = Thread(target=set_webhook)
    t2.start()
    
    # মূল থ্রেডে ফ্ল্যাস্ক সার্ভার চালু (Gunicorn ছাড়া সাধারণ পাইথনেই চলবে)
    from werkzeug.serving import make_server
    port = int(os.environ.get("PORT", 8080))
    srv = make_server('0.0.0.0', port, app)
    srv.serve_forever()
