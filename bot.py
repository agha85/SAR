import os
import time
import requests
import numpy as np

BASE_URL = "https://mt5.mtapi.io"

# زانیارییەکان لە Variables لە Railway دەخوێندرێنەوە
MT5_USER = os.getenv("MT5_USER")
MT5_PASSWORD = os.getenv("MT5_PASSWORD")
MT5_HOST = os.getenv("MT5_HOST")
MT5_PORT = os.getenv("MT5_PORT", "443")

# هێمای بیتکۆین (ئەگەر برۆکەرەکەت پاشگری هەیە وەک BTCUSDm لێرە بیگۆڕە)
SYMBOL = os.getenv("SYMBOL", "BTCUSD")
LOT_SIZE = 0.01
TIMEFRAME = 5  # تایم فڕەیمی ٥ خولەکی (M5) زۆر گونجاوترە بۆ بیتکۆین

# ڕێژەی ستۆپ لۆس و تێک پرۆفیت بەپێی نرخی بیتکۆین
SL_PERCENT = 0.008  # 0.8% ستۆپ لۆس (نزیکەی ٥٠٠ بۆ ٨٠٠ دۆلار بەپێی نرخ)
TP_PERCENT = 0.016  # 1.6% تێک پرۆفیت (نزیکەی ١٠٠٠ بۆ ١٦٠٠ دۆلار)

def get_token():
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
        print(f"پەیوەست بوو! Token: {token[:8]}***")
        return token
    except Exception as e:
        print(f"هەڵە لە پەیوەستبوون بە سێرڤەری MT5: {e}")
        return None

def calculate_indicators(closes):
    # Exponential Moving Averages (EMA 9, EMA 21)
    w_fast = np.exp(np.linspace(-1., 0., 9))
    w_fast /= w_fast.sum()
    ema_fast = np.convolve(closes, w_fast, mode='valid')[-1]

    w_slow = np.exp(np.linspace(-1., 0., 21))
    w_slow /= w_slow.sum()
    ema_slow = np.convolve(closes, w_slow, mode='valid')[-1]

    # RSI (14)
    deltas = np.diff(closes[-16:])
    seed = deltas[:14]
    up = seed[seed >= 0].sum() / 14
    down = -seed[seed < 0].sum() / 14
    rs = up / down if down != 0 else 0
    rsi = 100. - 100. / (1. + rs)

    return ema_fast, ema_slow, rsi

def get_open_positions(token):
    url = f"{BASE_URL}/OpenedOrders"
    params = {"id": token}
    try:
        res = requests.get(url, params=params, timeout=15)
        orders = res.json()
        return [o for o in orders if o.get("symbol") == SYMBOL] if isinstance(orders, list) else []
    except Exception:
        return []

def send_order(token, operation, price, sl, tp):
    url = f"{BASE_URL}/OrderSend"
    params = {
        "id": token,
        "symbol": SYMBOL,
        "operation": operation,
        "volume": LOT_SIZE,
        "price": round(price, 2),
        "stoploss": round(sl, 2),
        "takeprofit": round(tp, 2)
    }
    try:
        res = requests.get(url, params=params, timeout=15)
        print(f"فەرمانی بازرگانی جێبەجێ کرا ({operation}): {res.text}")
    except Exception as e:
        print(f"هەڵە لە ناردنی فەرمان: {e}")

def main():
    if not MT5_USER or not MT5_PASSWORD or not MT5_HOST:
        print("تکایە دڵنیابە لە دانانی زانیارییەکان لە بەشی Variables.")
        return

    token = get_token()
    while not token:
        time.sleep(10)
        token = get_token()

    print(f"بۆتی بیتکۆین دەستی بە چاودێری بازاڕی {SYMBOL} کرد...")

    while True:
        try:
            # وەرگرتنی نرخی ڕاستەوخۆی بیتکۆین
            quote_res = requests.get(f"{BASE_URL}/QuoteClient", params={"id": token, "symbol": SYMBOL}, timeout=10)
            quote = quote_res.json()

            # وەرگرتنی مۆمەکانی ڕابردوو
            hist_res = requests.get(f"{BASE_URL}/QuoteHistory", params={"id": token, "symbol": SYMBOL, "timeframe": TIMEFRAME, "count": 40}, timeout=15)
            candles = hist_res.json()

            if isinstance(candles, list) and len(candles) >= 30:
                closes = np.array([c['close'] for c in candles])
                ask = float(quote.get("ask", closes[-1]))
                bid = float(quote.get("bid", closes[-1]))

                ema_fast, ema_slow, rsi = calculate_indicators(closes)
                open_pos = get_open_positions(token)

                # مەرجی کڕین (BUY)
                if ema_fast > ema_slow and (50 < rsi < 70) and len(open_pos) == 0:
                    sl = ask * (1 - SL_PERCENT)
                    tp = ask * (1 + TP_PERCENT)
                    print(f"سیگناڵی کڕینی بیتکۆین (BUY) | نرخ: {ask:.2f} | RSI: {rsi:.1f}")
                    send_order(token, "Buy", ask, sl=sl, tp=tp)

                # مەرجی فرۆشتن (SELL)
                elif ema_fast < ema_slow and (30 < rsi < 50) and len(open_pos) == 0:
                    sl = bid * (1 + SL_PERCENT)
                    tp = bid * (1 - TP_PERCENT)
                    print(f"سیگناڵی فرۆشتنی بیتکۆین (SELL) | نرخ: {bid:.2f} | RSI: {rsi:.1f}")
                    send_order(token, "Sell", bid, sl=sl, tp=tp)

            # چاوەڕوانکردنی کاتی مۆمی نوێ
            time.sleep(60)

        except Exception as e:
            print(f"تێبینی / پچڕان: {e}")
            token = get_token()
            time.sleep(10)

if __name__ == "__main__":
    main()