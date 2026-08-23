import os
import time
import requests

API_URL = "https://mt5.mtapi.io"
ACCOUNT_ID = os.getenv("MT5_ACCOUNT")
PASSWORD = os.getenv("MT5_PASSWORD")
SERVER = os.getenv("MT5_SERVER")

SYMBOL = "BITCOIN"     
LOT_SIZE = 0.01        
PRICE_GAP = 1.0        # بۆشایی ١ سەنت (١ دۆلار لە نرخی بیتکۆین)

SESSION_TOKEN = ""

last_position = {
    "ticket": None,
    "type": None
}

# بۆ پاراستنی بەرزی و نزمی ستۆپ بۆ ئەوەی هەرگیز بۆ دواوە نەگەڕێتەوە
highest_price_seen = 0.0
lowest_price_seen = 0.0

def connect_account():
    global SESSION_TOKEN
    print("[Connect] هەوڵی بەستنەوە دەدات...")
    params = {"user": ACCOUNT_ID, "password": PASSWORD, "server": SERVER}
    try:
        response = requests.get(f"{API_URL}/ConnectEx", params=params, timeout=30)
        if response.status_code == 200:
            SESSION_TOKEN = response.text.replace('"', '').strip()
            return True
        return False
    except:
        return False

def open_order(cmd_type_str):
    global highest_price_seen, lowest_price_seen
    cmd_code = 0 if cmd_type_str.lower() == "buy" else 1
    print(f"\n[Action] ⚡ VIROS پێچەوانەی کردەوە بۆ: {cmd_type_str.upper()}...")
    params = {
        "id": SESSION_TOKEN,
        "symbol": SYMBOL,
        "cmd": cmd_code,
        "volume": LOT_SIZE
    }
    try:
        res = requests.get(f"{API_URL}/OrderSend", params=params, timeout=20)
        # پاککردنەوەی پێوەرەکان بۆ ئۆردەری نوێ
        highest_price_seen = 0.0
        lowest_price_seen = 0.0
    except:
        pass

def modify_sl(ticket, new_sl):
    new_sl = round(new_sl, 2)
    params = {
        "id": SESSION_TOKEN,
        "ticket": ticket,
        "sl": new_sl
    }
    try:
        res = requests.get(f"{API_URL}/OrderModify", params=params, timeout=20)
        if "SAME_PARAMS" not in res.text and res.status_code == 200:
            print(f"[Trailing] 🛡️ ستۆپ ڕاکێشرا بۆ دوای نرخ: {new_sl}")
    except:
        pass

def start_sar_engine():
    global SESSION_TOKEN, highest_price_seen, lowest_price_seen
    print(f"[VIROS🐉] مەکینەی خێرای کاندڵ و پێچەوانەبوونەوە دەستی پێکرد!")
    
    while True:
        try:
            if not SESSION_TOKEN:
                if not connect_account():
                    time.sleep(3)
                    continue

            params = {"id": SESSION_TOKEN}
            response = requests.get(f"{API_URL}/OpenedOrders", params=params, timeout=10)
            
            if response.status_code == 200:
                positions = response.json()
                
                if isinstance(positions, list) and len(positions) > 0:
                    pos = positions[0]
                    ticket = pos.get("Ticket", pos.get("ticket"))
                    order_type = pos.get("Type", pos.get("orderType", ""))
                    
                    sl = pos.get("StopLoss", pos.get("sl"))
                    sl = float(sl) if sl else 0.0
                    
                    open_price = float(pos.get("OpenPrice", pos.get("openPrice", 0)))
                    current_price = float(pos.get("currentPrice", pos.get("priceCurrent", open_price)))
                    
                    last_position["ticket"] = ticket
                    last_position["type"] = str(order_type)
                    
                    is_buy = (str(order_type).lower() == "buy" or order_type == 0)
                    
                    # ١. دانانی ستۆپ لۆسی سەرەتایی (١ سەنت زەرەر لە کاتی کردنەوەدا)
                    if sl == 0:
                        if is_buy:
                            initial_sl = open_price - PRICE_GAP
                            modify_sl(ticket, initial_sl)
                            highest_price_seen = open_price
                        else:
                            initial_sl = open_price + PRICE_GAP
                            modify_sl(ticket, initial_sl)
                            lowest_price_seen = open_price
                    
                    # ٢. مەکینەی ڕاکێشانی خێرا لە دوای نرخ (Trailing بە خێرایی کاندڵ)
                    elif current_price > 0:
                        if is_buy:
                            # ئەگەر نرخ بەرزتر بووەوە لە بەرزترین خاڵی پێشوو
                            if current_price > highest_price_seen:
                                highest_price_seen = current_price
                                # ستۆپەکە لە دوای نرخەوە بە GAPـی دیاریکراو دەجوڵێت
                                potential_sl = highest_price_seen - PRICE_GAP
                                if potential_sl > sl:
                                    modify_sl(ticket, potential_sl)
                        else:
                            # بۆ سێڵ: ئەگەر نرخ نزمتر بووەوە لە نزمترین خاڵی پێشوو
                            if lowest_price_seen == 0.0 or current_price < lowest_price_seen:
                                lowest_price_seen = current_price
                                potential_sl = lowest_price_seen + PRICE_GAP
                                if potential_sl < sl and potential_sl > 0:
                                    modify_sl(ticket, potential_sl)
                else:
                    # ٣. کاتێک ستۆپ شکێنرا و ئۆردەر نەما، ڕاستەوخۆ پێچەوانەکەی بکەوە
                    if last_position["ticket"] is not None:
                        print(f"\n[Reverse] 🚨 ستۆپ شکێنرا! ڕاستەوخۆ ئاڕاستە دەگۆڕێت...")
                        next_type = "Sell" if (str(last_position["type"]).lower() == "buy" or last_position["type"] == 0) else "Buy"
                        open_order(next_type)
                        last_position["ticket"] = None
                    else:
                        print("[Start] مەکینە دەست پێدەکات بە Buy...")
                        open_order("Buy")
            else:
                SESSION_TOKEN = ""

        except Exception as e:
            pass

        # خێرایی تەواو: هەر ١ چرکە جارێک چاودێری دەکات
        time.sleep(1)

if __name__ == "__main__":
    start_sar_engine()