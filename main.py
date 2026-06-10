import os
import time
from threading import Thread
import yfinance as yf
import requests
from flask import Flask

# 1. Flask Web Server
app = Flask('')

@app.route('/')
def home():
    return "Bot is running 24/7!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# 2. Telegram Configurations
TOKEN = os.environ.get("TELEGRAM_TOKEN", "8264008675:AAEHzakAXPZeNVZKWlvYHRWboyjAuUhg0QM") 
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "-1003684590469")


def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram Error: {e}")

# 3. ICT FVG Strategy Logic
def check_fvg(symbol="EURUSD=X", timeframe="1m"):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1d", interval=timeframe)
        
        if len(df) < 4: # অন্তত ৪টি ক্যান্ডেল দরকার
            return

        # রানিং ক্যান্ডেল [-1] বাদ দিয়ে তার আগের ৩টি ক্যান্ডেল:
        # ১ম ক্যান্ডেল = -4, ২য় ক্যান্ডেল = -3, ৩য় ক্যান্ডেল = -2
        c1_high = df['High'].iloc[-4]
        c1_low  = df['Low'].iloc[-4]
        c3_high = df['High'].iloc[-2]
        c3_low  = df['Low'].iloc[-2]

        # Bullish FVG
        if c1_high < c3_low:
            gap = c3_low - c1_high
            msg = f"🟢 Quotex ICT UP SIGNAL! ({symbol})\nTimeframe: {timeframe}\nBullish FVG Detected!\nGap: {gap:.5f}"
            print(msg)
            send_telegram_message(msg)

        # Bearish FVG
        elif c1_low > c3_high:
            gap = c1_low - c3_high
            msg = f"🔴 Quotex ICT DOWN SIGNAL! ({symbol})\nTimeframe: {timeframe}\nBearish FVG Detected!\nGap: {gap:.5f}"
            print(msg)
            send_telegram_message(msg)
            
    except Exception as e:
        print(f"Data Fetch Error: {e}")

# 4. Main Bot Loop
def bot_loop():
    print("Trading Bot Started...")
    send_telegram_message("🚀 Quotex ICT FVG Bot is now LIVE on Render!")
    
    while True:
        check_fvg(symbol="EURUSD=X", timeframe="1m")
        time.sleep(60) 

if __name__ == "__main__":
    t = Thread(target=bot_loop)
    t.start()
    run_server()
