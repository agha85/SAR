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
    print(f"[Action] VIROS هەوڵ دەدات SL بۆ ئۆردەری {ticket} بکات بە {new_sl}...")
    params = {
        "id": SESSION_TOKEN,
        "ticket": ticket,
        "sl": new_sl
    }
    try:
        response = requests.get(f"{API_URL}/OrderModify", params=params, timeout=20)
        print(f"[Result] وەڵامی برۆکەر: {response.text}")
    except Exception as e:
        print(f"[Error] کێشە لە ناردنی فەرمان: {e}")

def start_sar_engine():
    global SESSION_TOKEN
    print(f"[VIROS🐉] پشکنەری داتا دەستی پێکرد | Account: {ACCOUNT_ID}")
    
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
                            # لێرەدا تەواوی داتاکە وەک خۆی چاپ دەکەین بۆ ئەوەی وشە ڕاستەقینەکە بدۆزینەوە
                            print(f"[RAW DATA] تەواوی زانیارییەکان: {pos}")
                            
                            ticket = pos.get("Ticket", pos.get("ticket"))
                            current_sl = pos.get("StopLoss", pos.get("sl", 0))
                            open_price = pos.get("OpenPrice", pos.get("openPrice", 0))
                            
                            # تاقیکردنەوەیەکی کوێرانە: ئەگەر ستۆپ لۆس سفر بوو، ٥٠٠ دۆلار لە خوار نرخی کردنەوە دایدەنێین
                            if current_sl == 0 and open_price > 0:
                                modify_sl(ticket, open_price - 500)
                else:
                    print("[Idle] هیچ ئۆردەرێک نییە...")
            else:
                SESSION_TOKEN = ""

        except Exception as e:
            print(f"[Loop Error] {e}")

        time.sleep(15)

if __name__ == "__main__":
    start_sar_engine()