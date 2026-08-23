import time
import requests
import numpy as np

# =========================================================================
# تکایە ئەم ٣ دێڕە بە زانیارییە ڕاستەقینەکانی ناو ئەپی MT5 پڕبکەرەوە:
# =========================================================================
MT5_USER = "ژمارەی_ئەکاونتەکەت"        # بۆ نموونە: "50123456"
MT5_PASSWORD = "تێپەڕەوشەکەت"        # تێپەڕەوشەکەت لێرە بنووسە
MT5_HOST = "ناوی_سێرڤەرەکەت"          # بۆ نموونە: "FxPro-MT5 Demo" یان ئایپی سێرڤەر
MT5_PORT = "443"

SYMBOL = "BTCUSD"
LOT_SIZE = 0.01
TIMEFRAME = 5
BASE_URL = "https://mt5.mtapi.io"

SL_PERCENT = 0.008  # 0.8% ستۆپ لۆس
TP_PERCENT = 0.016  # 1.6% تێک پرۆفیت

def get_token():
    print(f"دەستکرا بە پەیوەستبوون بە سێرڤەر ({MT5_HOST}) بە ئەکاونتی: {MT5_USER}...")
    url = f"{BASE_URL}/Connect"
    params = {
        "user": MT5_USER,
        "password": MT5_PASSWORD,
        "host": MT5_HOST,
        "port": MT5_PORT
    }
    try:
        response = requests.get(url, params=params, timeout=30)
        res_text = response.text.strip('"').strip()
        
        # ئەگەر هەڵە هەبوو Token وەرناگرێت
        if "CONNECT_ERROR" in res_text or "Disconnected" in res_text or response.status_code != 200:
            print(f"هەڵە لە زانیارییەکانی سێرڤەر/ئەکاونت: {res_text}")
            return None
            
        print(f"پەیوەست بوو! Token بە سەرکەوتوویی وەرگیرا.")
        return res_text
    except Exception as e:
        print(f"هەڵەی پەیوەستبوون: {e}")
        return None

def calculate_indicators(closes):
    w_fast = np.exp(np.linspace(-1., 0., 9))
    w_fast /= w_fast.sum()
    ema_fast = np.convolve(closes, w_fast, mode='valid')[-1]

    w_slow = np.exp(np.linspace(-1., 0., 21))
    w_slow /= w_slow.sum()
    ema_slow = np.convolve(closes, w_slow, mode='valid')[-1]

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
        print(f"فەرمانی بازرگانی ({operation}) جێبەجێ کرا: {res.text}")
    except Exception as e:
        print(f"هەڵە لە ناردنی فەرمان: {e}")

def main():
    token = get_token()
    while not token:
        print("دووبارە هەوڵ دەدرێتەوە دوای ١٥ چرکە...")
        time.sleep(15)
        token = get_token()

    print(f"بۆتەکە چالاکە و چاودێری بازاڕی {SYMBOL} دەکات...")

    while True:
        try:
            quote_res = requests.get(f"{BASE_URL}/QuoteClient", params={"id": token, "symbol": SYMBOL}, timeout=10)
            quote = quote_res.json()

            hist_res = requests.get(f"{BASE_URL}/QuoteHistory", params={"id": token, "symbol": SYMBOL, "timeframe": TIMEFRAME, "count": 40}, timeout=15)
            candles = hist_res.json()

            if isinstance(candles, list) and len(candles) >= 30:
                closes = np.array([c['close'] for c in candles])
                ask = float(quote.get("ask", closes[-1]))
                bid = float(quote.get("bid", closes[-1]))

                ema_fast, ema_slow, rsi = calculate_indicators(closes)
                open_pos = get_open_positions(token)

                if ema_fast > ema_slow and (50 < rsi < 70) and len(open_pos) == 0:
                    sl = ask * (1 - SL_PERCENT)
                    tp = ask * (1 + TP_PERCENT)
                    print(f"سیگناڵی کڕین (BUY) | نرخ: {ask:.2f} | RSI: {rsi:.1f}")
                    send_order(token, "Buy", ask, sl=sl, tp=tp)

                elif ema_fast < ema_slow and (30 < rsi < 50) and len(open_pos) == 0:
                    sl = bid * (1 + SL_PERCENT)
                    tp = bid * (1 - TP_PERCENT)
                    print(f"سیگناڵی فرۆشتن (SELL) | نرخ: {bid:.2f} | RSI: {rsi:.1f}")
                    send_order(token, "Sell", bid, sl=sl, tp=tp)

            time.sleep(60)

        except Exception as e:
            print(f"تێبینی: {e}")
            token = get_token()
            time.sleep(10)

if __name__ == "__main__":
    main()