import os
import time
import requests

API_URL = "https://mt5.mtapi.io"
ACCOUNT_ID = os.getenv("MT5_ACCOUNT")
PASSWORD = os.getenv("MT5_PASSWORD")
SERVER = os.getenv("MT5_SERVER")

# قەبارەی ئۆردەرە نوێیەکان بەپێی داواکاری خۆت
LOT_SIZE = 0.01
SESSION_TOKEN = ""

# مێشکی بۆتەکە بۆ بیرکەوتنەوەی دواین ئۆردەری کراوە
last_position = {
    "ticket": None,
    "type": None,  # 0 بۆ Buy، 1 بۆ Sell
    "symbol": None
}

def connect_account():
    global SESSION_TOKEN
    print("[Connect] هەوڵی بەستنەوە دەدات بە برۆکەرەوە...")
    params = {"user": ACCOUNT_ID, "password": PASSWORD, "server": SERVER}
    try:
        response = requests.get(f"{API_URL}/ConnectEx", params=params, timeout=30)
        if response.status_code == 200:
            SESSION_TOKEN = response.text.replace('"', '').strip()
            print(f"[Success] پەیوەندی بەسترا! Token: {SESSION_TOKEN[:10]}...")
            return True
        return False
    except:
        return False

def send_reverse_order(symbol, cmd_type):
    type_name = "Buy" if cmd_type == 0 else "Sell"
    print(f"\n[Reverse Action] ⚠️ VIROS ئۆردەری پێچەوانە دەکاتەوە: {type_name} بە قەبارەی {LOT_SIZE}...")
    
    params = {
        "id": SESSION_TOKEN,
        "symbol": symbol,
        "cmd": cmd_type,  # 0 بۆ Buy وە 1 بۆ Sell
        "volume": LOT_SIZE
    }
    try:
        # ناردنی فەرمانی کردنەوەی ئۆردەری نوێ بۆ برۆکەر
        response = requests.get(f"{API_URL}/OrderSend", params=params, timeout=20)
        print(f"[Order Result] وەڵامی برۆکەر: {response.text}\n")
    except Exception as e:
        print(f"[Error] کێشە لە کردنەوەی ئۆردەری نوێ: {e}")

def start_sar_engine():
    global SESSION_TOKEN
    print(f"[VIROS🐉] مەکینەی SAR (وەستان و پێچەوانەبوونەوە) دەستی پێکرد | Account: {ACCOUNT_ID}")
    
    while True:
        try:
            if not SESSION_TOKEN:
                if not connect_account():
                    time.sleep(15)
                    continue

            params = {"id": SESSION_TOKEN}
            response = requests.get(f"{API_URL}/OpenedOrders", params=params, timeout=20)
            
            if response.status_code == 200:
                positions = response.json()
                
                if isinstance(positions, list) and len(positions) > 0:
                    # وەرگرتنی زانیاری یەکەم ئۆردەری کراوە
                    pos = positions[0]
                    ticket = pos.get("Ticket", pos.get("ticket"))
                    pos_type = pos.get("Type", pos.get("orderType"))
                    symbol = pos.get("Symbol", pos.get("symbol"))
                    sl = pos.get("StopLoss", pos.get("sl"))
                    
                    print(f"[Tracking] چاودێری ئۆردەری {ticket} دەکات | جۆر: {pos_type} | SL: {sl}")
                    
                    # زەخیرەکردنی ئەم ئۆردەرە لە مێشکی بۆتەکەدا بۆ ئەوەی بزانێت کەی لە ستۆپ دەدات
                    last_position["ticket"] = ticket
                    last_position["type"] = pos_type
                    last_position["symbol"] = symbol
                    
                    # تێبینی: بەشی ڕاکێشانی ستۆپ لۆسەکە لێرەدا کار دەکات کە داتای SARـمان خستە سەر
                    
                else:
                    # ئەگەر هیچ ئۆردەرێک نەبوو، پشکنین دەکات بزانێت ئایا پێشتر ئۆردەرمان هەبووە؟
                    if last_position["ticket"] is not None:
                        print(f"[Trigger] 🚨 ئۆردەری ژمارە {last_position['ticket']} لە ستۆپی دا و داخرا!")
                        
                        # بڕیاردان بۆ ئۆردەری پێچەوانە
                        if last_position["type"] == 0:  # ئەگەر ئۆردەرە داخراوەکە Buy بوو
                            send_reverse_order(last_position["symbol"], 1)  # ڕاستەوخۆ Sell بکە
                        elif last_position["type"] == 1:  # ئەگەر ئۆردەرە داخراوەکە Sell بوو
                            send_reverse_order(last_position["symbol"], 0)  # ڕاستەوخۆ Buy بکە
                            
                        # خاوێنکردنەوەی مێشکی بۆتەکە بۆ ئەوەی هەر هەمان ئۆردەر دووبارە نەکاتەوە
                        last_position["ticket"] = None
                        last_position["type"] = None
                        last_position["symbol"] = None
                    else:
                        print("[Idle] هیچ ئۆردەرێکی کراوە نییە. چاوەڕێی دەستپێک دەکات...")
                        
            else:
                SESSION_TOKEN = ""

        except Exception as e:
            print(f"[Loop Error] {e}")

        # هەر ٥ چرکە جارێک پشکنین دەکات بۆ ئەوەی زۆر خێرا بێت لە کاتی لێدانی ستۆپ
        time.sleep(5)

if __name__ == "__main__":
    start_sar_engine()