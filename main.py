import os
import time
import requests

API_URL = "https://mt5.mtapi.io"
ACCOUNT_ID = os.getenv("MT5_ACCOUNT")
PASSWORD = os.getenv("MT5_PASSWORD")
SERVER = os.getenv("MT5_SERVER")

SESSION_TOKEN = ""

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

def modify_sl(ticket, new_sl):
    print(f"[Action] هەوڵی جوڵاندنی SL بۆ ئۆردەری {ticket} بۆ نرخی {new_sl}...")
    params = {
        "id": SESSION_TOKEN,
        "ticket": ticket,
        "sl": new_sl
    }
    try:
        # ناردنی فەرمانی گۆڕین بۆ برۆکەرەکە
        response = requests.get(f"{API_URL}/OrderModify", params=params, timeout=20)
        if response.status_code == 200:
            print(f"[Success] قەڵغانەکە (SL) بە سەرکەوتوویی ڕاکێشرا بۆ {new_sl}!")
        else:
            print(f"[Failed] کێشە لە جوڵاندن: {response.text}")
    except Exception as e:
        print(f"[Error] هەڵە لە ناردنی فەرمان: {e}")

def get_sar_value(symbol):
    # لێرەدا پێویستمان بە لینکی تایبەتە بە ئیندیکەیتەرەکان لە mtapi.io
    # بۆ نموونە: دەبێت داوای خاڵی iSAR بکەین لەسەر فڕەیمی 15 خولەک
    # لەبەر ئەوەی هێشتا لینکە تەواوەکەمان نییە، بۆ تاقیکردنەوە ژمارەیەکی خەیاڵی دەگەڕێنینەوە
    # دواتر ئەم بەشە بە داتای ڕاستەقینە پڕ دەکەینەوە
    return 60000.00  # نموونە: گریمان خاڵی SAR لەسەر 60,000 دۆلارە

def start_sar_engine():
    global SESSION_TOKEN
    print(f"[VIROS-SAR] مەکینەی جوڵاندن دەستی پێکرد | Account: {ACCOUNT_ID}")
    
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
                    for pos in positions:
                        symbol = pos.get("Symbol", pos.get("symbol", ""))
                        
                        if "BTC" in symbol.upper() or "BITCOIN" in symbol.upper():
                            ticket = pos.get("Ticket", pos.get("ticket"))
                            current_sl = pos.get("StopLoss", pos.get("sl", 0))
                            pos_type = pos.get("Type", pos.get("type")) # 0 = Buy, 1 = Sell
                            
                            print(f"[Tracking] بیتکۆین | Ticket: {ticket} | SL ئێستا: {current_sl}")
                            
                            # وەرگرتنی خاڵی نوێی SAR
                            new_sar_point = get_sar_value(symbol)
                            
                            # لۆژیکی بڕیاردان بۆ جوڵاندن
                            if pos_type == 0:  # ئەگەر ئۆردەرەکە Buy بوو
                                if new_sar_point > current_sl:
                                    modify_sl(ticket, new_sar_point)
                            
                            elif pos_type == 1:  # ئەگەر ئۆردەرەکە Sell بوو
                                if current_sl == 0 or new_sar_point < current_sl:
                                    modify_sl(ticket, new_sar_point)

                else:
                    print("[Idle] چاوەڕێی ئۆردەری نوێ دەکات...")
            else:
                SESSION_TOKEN = ""

        except Exception as e:
            print(f"[Loop Error] {e}")

        time.sleep(30)

if __name__ == "__main__":
    start_sar_engine()