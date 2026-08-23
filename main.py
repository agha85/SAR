import os
import time
import requests

API_URL = "https://mt5.mtapi.io"
ACCOUNT_ID = os.getenv("MT5_ACCOUNT")
PASSWORD = os.getenv("MT5_PASSWORD")
SERVER = os.getenv("MT5_SERVER")

SYMBOL = "BITCOIN"     
LOT_SIZE = 0.01        
# بۆ بیتکۆین ١.٠ دۆلار جوڵەی نرخ دەکاتە ڕێک ١ سەنت زەرەر 
# (کاتێک ئیشت لەسەر ئاڵتوون کرد، ئەمە بکە بە 0.01)
PRICE_GAP = 1.0        

SESSION_TOKEN = ""

last_position = {
    "ticket": None,
    "type": None
}

def connect_account():
    global SESSION_TOKEN
    print("[Connect] هەوڵی بەستنەوە دەدات بە برۆکەرەوە...")
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
    cmd_code = 0 if cmd_type_str.lower() == "buy" else 1
    print(f"\n[Action] ⚡ VIROS ئۆردەری نوێ دەکاتەوە: {cmd_type_str.upper()}...")
    params = {
        "id": SESSION_TOKEN,
        "symbol": SYMBOL,
        "cmd": cmd_code,
        "volume": LOT_SIZE
    }
    try:
        requests.get(f"{API_URL}/OrderSend", params=params, timeout=20)
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
            print(f"[Trailing] 🛡️ قەڵغان ڕاکێشرا بۆ: {new_sl}")
    except:
        pass

def start_sar_engine():
    global SESSION_TOKEN
    print(f"[VIROS🐉] مەکینەی Reversal (بەمەرجی چوونە خێرەوە - ١ سەنت) دەستی پێکرد...")
    
    while True:
        try:
            if not SESSION_TOKEN:
                if not connect_account():
                    time.sleep(5)
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
                    
                    # ١. دانانی ستۆپ لۆسی سەرەتایی (ڕێک ١ سەنت زەرەر)
                    if sl == 0:
                        if str(order_type).lower() == "buy" or order_type == 0:
                            modify_sl(ticket, open_price - PRICE_GAP)
                        else:
                            modify_sl(ticket, open_price + PRICE_GAP)
                    
                    # ٢. جوڵاندنی ستۆپ لۆس (تەنها ئەگەر چووە خێرەوە)
                    elif current_price > 0:
                        if str(order_type).lower() == "buy" or order_type == 0:
                            if current_price > open_price:
                                potential_sl = current_price - PRICE_GAP
                                if potential_sl > sl:
                                    modify_sl(ticket, potential_sl)
                        else:
                            if current_price < open_price:
                                potential_sl = current_price + PRICE_GAP
                                if potential_sl < sl and potential_sl > 0:
                                    modify_sl(ticket, potential_sl)
                else:
                    if last_position["ticket"] is not None:
                        print(f"\n[Reverse] 🚨 لە ستۆپی دا (١ سەنت زەرەر)! ڕاستەوخۆ پێچەوانەی دەکاتەوە...")
                        next_type = "Sell" if (str(last_position["type"]).lower() == "buy" or last_position["type"] == 0) else "Buy"
                        open_order(next_type)
                        last_position["ticket"] = None
                    else:
                        print("[Start] مەکینەکە دەست پێ دەکات...")
                        open_order("Buy")
            else:
                SESSION_TOKEN = ""

        except Exception as e:
            pass

        time.sleep(3)

if __name__ == "__main__":
    start_sar_engine()