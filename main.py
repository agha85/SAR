import os
import time
import requests
import numpy as np

BASE_URL = "https://mt5.mtapi.io"

# زانیاری هەژماری MT5 لە ڕێگەی Variables لەسەر Railway وەردەگیرێت
MT5_USER = os.getenv("MT5_USER")          # ژمارەی هەژمارەکەت (Account Number)
MT5_PASSWORD = os.getenv("MT5_PASSWORD")  # تێپەڕەوشەی هەژمارەکەت (Password)
MT5_HOST = os.getenv("MT5_HOST")          # هۆست یان ئایپی برۆکەر (بۆ نموونە: 198.51.100.1 یان ناوی سێرڤەر)
MT5_PORT = os.getenv("MT5_PORT", "443")   # پۆرت (بە گشتی 443 یان 1950)

SYMBOL = "XAUUSD"
LOT_SIZE = 0.01
TIMEFRAME = 1  # 1 خولەکی (M1)

def get_token():
    """پەیوەندی کردن بە سێرڤەری MT5 و وەرگرتنی Token"""
    url = f"{BASE_URL}/Connect"
    params = {
        "user": MT5_USER,
        "password": MT5_PASSWORD,
        "host": MT5_HOST,
        "port": MT5_PORT
    }
    try:
        response = requests.get(url, params=params, timeout=30)
        token = response.text.strip('"').strip()
        print(f"Token بە سەرکەوتوویی وەرگیرا: {token[:8]}***")
        return token
    except Exception as e:
        print(f"هەڵە لە پەیوەستبوون بە سێرڤەر: {e}")
        return None

def calculate_indicators(closes):
    """هەژمارکردنی موڤینگ ئەڤرەیج و RSI"""
    # Exponential Moving Averages
    weights_9 = np.exp(np.linspace(-1., 0., 9))
    weights_9 /= weights_9.sum()
    ema_fast = np.convolve(closes, weights_9, mode='valid')[-1]

    weights_21 = np.exp(np.linspace(-1., 0., 21))
    weights_21 /= weights_21.sum()
    ema_slow = np.convolve(closes, weights_21, mode='valid')[-1]

    # RSI (14)
    deltas = np.diff(closes[-16:])
    seed = deltas[:14]
    up = seed[seed >= 0].sum() / 14
    down = -seed[seed < 0].sum() / 14
    rs = up / down if down != 0 else 0
    rsi = 100. - 100. / (1. + rs)

    return ema_fast, ema_slow, rsi

def get_open_positions(token):
    """پشکنینی پۆزیشنە کراوەکان"""
    url = f"{BASE_URL}/OpenedOrders"
    params = {"id": token}
    try:
        res = requests.get(url, params=params, timeout=15)
        orders = res.json()
        return [o for o in orders if o.get("symbol") == SYMBOL] if isinstance(orders, list) else []
    except Exception:
        return []

def send_order(token, operation, price, sl, tp):
    """ناردنی فەرمانی کڕین یان فرۆشتن"""
    url = f"{BASE_URL}/OrderSend"
    params = {
        "id": token,
        "symbol": SYMBOL,
        "operation": operation,  # "Buy" یان "Sell"
        "volume": LOT_SIZE,
        "price": round(price, 2),
        "stoploss": round(sl, 2),
        "takeprofit": round(tp, 2)
    }
    try:
        res = requests.get(url, params=params, timeout=15)
        print(f"ئەنجامی ناردنی فەرمان ({operation}): {res.text}")
    except Exception as e:
        print(f"هەڵە لە ناردنی فەرمان: {e}")

def main():
    if not MT5_USER or not MT5_PASSWORD or not MT5_HOST:
        print("تکایە دڵنیابە لە پڕکردنەوەی MT5_USER، MT5_PASSWORD، و MT5_HOST لە بەشی Variables.")
        return

    token = get_token()
    while not token:
        time.sleep(10)
        token = get_token()

    print("بۆتەکە دەستی بە چاودێری بازاڕی ئاڵتوون (XAUUSD) کرد...")

    while True:
        try:
            # وەرگرتنی دوایین نرخی ئاڵتوون
            quote_res = requests.get(f"{BASE_URL}/QuoteClient", params={"id": token, "symbol": SYMBOL}, timeout=10)
            quote = quote_res.json()
            
            # وەرگرتنی داتای مۆمەکان
            hist_res = requests.get(f"{BASE_URL}/QuoteHistory", params={"id": token, "symbol": SYMBOL, "timeframe": TIMEFRAME, "count": 40}, timeout=15)
            candles = hist_res.json()

            if isinstance(candles, list) and len(candles) >= 30:
                closes = np.array([c['close'] for c in candles])
                ask = quote.get("ask", closes[-1])
                bid = quote.get("bid", closes[-1])

                ema_fast, ema_slow, rsi = calculate_indicators(closes)
                open_pos = get_open_positions(token)

                # مەرجی کڕین (BUY)
                if ema_fast > ema_slow and (50 < rsi < 70) and len(open_pos) == 0:
                    print(f"سیگناڵی کڕین (BUY) | نرخ: {ask} | RSI: {rsi:.1f}")
                    send_order(token, "Buy", ask, sl=ask - 2.5, tp=ask + 5.0)

                # مەرجی فرۆشتن (SELL)
                elif ema_fast < ema_slow and (30 < rsi < 50) and len(open_pos) == 0:
                    print(f"سیگناڵی فرۆشتن (SELL) | نرخ: {bid} | RSI: {rsi:.1f}")
                    send_order(token, "Sell", bid, sl=bid + 2.5, tp=bid - 5.0)

            time.sleep(60)

        except Exception as e:
            print(f"تێبینی / هەڵە: {e}")
            # لە کاتی پچڕانی دانیشتن، دووبارە پەیوەندی نوێ دەکاتەوە
            token = get_token()
            time.sleep(10)

if __name__ == "__main__":
    main()