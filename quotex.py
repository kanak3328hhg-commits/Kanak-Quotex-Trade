import os
import time
from threading import Thread
import yfinance as yf
import requests
from flask import Flask, request, jsonify

# 1. Flask Web Server Setup
app = Flask('')

# ৫-মিনিট লাইভ স্পট সিম্বল (মেটাল ও ফোরেক্স)
VALID_PAIRS = {
    "XAUUSD": "XAUUSD=X", "GOLD": "XAUUSD=X",
    "XAGUSD": "XAGUSD=X", "SILVER": "XAGUSD=X",
    "EURUSD": "EURUSD=X", "GBPUSD": "GBPUSD=X", "AUDUSD": "AUDUSD=X", "NZDUSD": "NZDUSD=X",
    "USDJPY": "USDJPY=X", "USDCHF": "USDCHF=X", "USDCAD": "USDCAD=X", "EURGBP": "EURGBP=X",
    "EURJPY": "EURJPY=X", "EURCHF": "EURCHF=X", "EURCAD": "EURCAD=X", "EURAUD": "EURAUD=X",
    "EURNZD": "EURNZD=X", "GBPJPY": "GBPJPY=X", "GBPCHF": "GBPCHF=X", "GBPCAD": "GBPCAD=X",
    "GBPAUD": "GBPAUD=X", "GBPNZD": "GBPNZD=X", "AUDJPY": "AUDJPY=X", "AUDCHF": "AUDCHF=X",
    "AUDCAD": "AUDCAD=X", "AUDNZD": "AUDNZD=X", "NZDJPY": "NZDJPY=X", "NZDCHF": "NZDCHF=X",
    "NZDCAD": "NZDCAD=X", "CADJPY": "CADJPY=X", "CADCHF": "CADCHF=X", "CHFJPY": "CHFJPY=X"
}

CURRENT_SYMBOL = "EURUSD=X"
SYMBOL_DISPLAY_NAME = "EURUSD"

# 2. Telegram Configurations
TOKEN = os.environ.get("TELEGRAM_TOKEN", "8264008675:AAEHzakAXPZeNVZKWlvYHRWboyjAuUhg0QM") 
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "-1003684590469")
RENDER_URL = "https://kanak-quotex-trade.onrender.com/webhook"

@app.route('/')
def home():
    global SYMBOL_DISPLAY_NAME
    return f"Bot is running! Current Active Pair: {SYMBOL_DISPLAY_NAME} (5m Timeframe)"

def auto_refresh_webhook():
    url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={RENDER_URL}"
    try:
        response = requests.get(url, timeout=10)
        print(f"🤖 [Auto-Webhook] Refreshed: {response.json()}")
    except Exception as e:
        print(f"❌ [Auto-Webhook] Error: {e}")

@app.route('/webhook', methods=['POST'])
def webhook():
    global CURRENT_SYMBOL, SYMBOL_DISPLAY_NAME, CHAT_ID
    data = request.get_json()
    
    if "channel_post" in data:
        post = data["channel_post"]
        text = post.get("text", "").strip().upper()
        
        incoming_chat_id = str(post["chat"]["id"])
        
        if text in VALID_PAIRS:
            CHAT_ID = incoming_chat_id
            CURRENT_SYMBOL = VALID_PAIRS[text]
            SYMBOL_DISPLAY_NAME = text
            
            confirm_msg = (
                f"⚙️ **Quotex Pair Configuration Update**\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"✅ **Success:** Active Pair Changed!\n"
                f"🎯 **Now Scanning:** `{text}` (5m Timeframe)\n"
                f"📊 *বট এখন প্রতি ৫ মিনিটে ট্রেন্ড ফিল্টারসহ এই পেয়ারটি স্ক্যান করবে।* "
            )
            send_telegram_message(confirm_msg)
            auto_refresh_webhook()
            
    return jsonify({"status": "success"})

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload)
    except Exception as e: print(f"Telegram Error: {e}")

# 3. ICT FVG Strategy Logic with Trend Filter & Trade Duration
def check_fvg():
    global CURRENT_SYMBOL, SYMBOL_DISPLAY_NAME
    try:
        symbol_to_scan = CURRENT_SYMBOL
        display_name_to_scan = SYMBOL_DISPLAY_NAME
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        ticker = yf.Ticker(symbol_to_scan, session=session)
        df = ticker.history(period="5d", interval="5m")
        
        if df.empty or len(df) < 25:
            print(f"⚠️ {display_name_to_scan}: Data insufficient on Yahoo. Retrying...")
            return

        # Trend Filter: 20 SMA
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        
        c1_high = df['High'].iloc[-4]
        c1_low  = df['Low'].iloc[-4]
        c3_high = df['High'].iloc[-2]
        c3_low  = df['Low'].iloc[-2]
        
        current_price = df['Close'].iloc[-1]
        current_sma = df['SMA_20'].iloc[-1]

        if display_name_to_scan in ["GOLD", "XAUUSD", "SILVER", "XAGUSD"] or "JPY" in display_name_to_scan:
            dec_places = 3
        else:
            dec_places = 5

        is_uptrend = current_price > current_sma
        is_downtrend = current_price < current_sma
        trend_status = "UPTREND 📈" if is_uptrend else "DOWNTREND 📉"

        # ১. Bullish FVG (UP SIGNAL)
        if c1_high < c3_low:
            if is_uptrend:
                gap = c3_low - c1_high
                entry_price = c1_high
                msg = (
                    f"🟢 **Quotex ICT UP SIGNAL!** ({display_name_to_scan})\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"⏱ Chart Timeframe: 5m\n"
                    f"🔥 Market Trend: {trend_status}\n"
                    f"⏳ **Trade Duration: 5 Minutes (Fixed)**\n"
                    f"📊 Current Price: {current_price:.{dec_places}f}\n"
                    f"🎯 **Best Entry Price: {entry_price:.{dec_places}f}** (or below)\n"
                    f"📐 Gap Size: {gap:.{dec_places}f}\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"💡 *নিয়ম: ক্যান্ডেল যখনই এই এন্ট্রি প্রাইস টাচ করবে, কোটেক্সে ৫ মিনিটের জন্য UP ট্রেড প্লেস করুন।* "
                )
                send_telegram_message(msg)
            else:
                print(f"⏭️ Bullish FVG ignored due to Downtrend filter.")

        # ২. Bearish FVG (DOWN SIGNAL)
        elif c1_low > c3_high:
            if is_downtrend:
                gap = c1_low - c3_high
                entry_price = c1_low
                msg = (
                    f"🔴 **Quotex ICT DOWN SIGNAL!** ({display_name_to_scan})\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"⏱ Chart Timeframe: 5m\n"
                    f"🔥 Market Trend: {trend_status}\n"
                    f"⏳ **Trade Duration: 5 Minutes (Fixed)**\n"
                    f"📊 Current Price: {current_price:.{dec_places}f}\n"
                    f"🎯 **Best Entry Price: {entry_price:.{dec_places}f}** (or above)\n"
                    f"📐 Gap Size: {gap:.{dec_places}f}\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"💡 *নিয়ম: ক্যান্ডেল যখনই এই এন্ট্রি প্রাইস টাচ করবে, কোটেক্সে ৫ মিনিটের জন্য DOWN ট্রেড প্লেস করুন।* "
                )
                send_telegram_message(msg)
            else:
                print(f"⏭️ Bearish FVG ignored due to Uptrend filter.")
            
        # ৩. কোনো সিগন্যাল না থাকলে
        else:
            no_signal_msg = (
                f"❌ **Quotex Signal Status** ({display_name_to_scan})\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📢 **Status:** No Signal Filtered Currently.\n"
                f"🔥 Market Trend: {trend_status}\n"
                f"⏳ *বট পরবর্তী ৫ মিনিটের জন্য মার্কেট স্ক্যান করছে।* \n"
                f"📊 Current Price: {current_price:.{dec_places}f}"
            )
            send_telegram_message(no_signal_msg)
            
    except Exception as e:
        print(f"Data Fetch Error: {e}")
        
# 4. Main Bot Loop
def bot_loop():
    print("Trading Bot Loop Started...")
    send_telegram_message("🚀 Quotex FVG Control Bot is LIVE (5m Filter Active)!\n\n👉 পেয়ার পরিবর্তন করতে চ্যানেলে পেয়ারের নাম লিখুন (যেমন: GOLD বা EURUSD)")
    
    auto_refresh_webhook()
    
    while True:
        try:
            check_fvg()
        except Exception as loop_err:
            print(f"Loop function error: {loop_err}")
        
        if int(time.time()) % 300 < 60:
            auto_refresh_webhook()
            
        time.sleep(300) 

if __name__ == "__main__":
    t1 = Thread(target=bot_loop, daemon=True)
    t1.start()
    
    from werkzeug.serving import make_server
    port = int(os.environ.get("PORT", 8080))
    srv = make_server('0.0.0.0', port, app)
    srv.serve_forever()
