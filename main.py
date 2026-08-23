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
    
    params = {
        "user": ACCOUNT_ID,
        "password": PASSWORD,
        "server": SERVER
    }
    
    try:
        # لێرەدا کێشەکەمان چارەسەر کرد و کردمان بە ConnectEx
        response = requests.get(f"{API_URL}/ConnectEx", params=params, timeout=30)
        
        if response.status_code == 200:
            result = response.text.replace('"', '').strip()
            SESSION_TOKEN = result
            print(f"[Success] پەیوەندی بەسترا! Token: {SESSION_TOKEN[:10]}...")
            return True
        else:
            print(f"[Failed] نەتوانرا پەیوەندی ببەسترێت: {response.text}")
            return False
    except Exception as e:
        print(f"[Error] هەڵە لە کاتی کۆنێکت بوون: {e}")
        return False

def start_sar_engine():
    global SESSION_TOKEN
    print(f"[VIROS-SAR] دەستی بە کار کرد | Account: {ACCOUNT_ID}")
    
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
                    print(f"[Active] {len(positions)} پۆزیشن دۆزرایەوە.")
                    for pos in positions:
                        symbol = pos.get("Symbol", pos.get("symbol", ""))
                        if "XAUUSD" in symbol.upper() or "GOLD" in symbol.upper():
                            ticket = pos.get("Ticket", pos.get("ticket"))
                            sl = pos.get("StopLoss", pos.get("sl", 0))
                            print(f"[Tracking] ئاڵتوون | Ticket: {ticket} | SL: {sl}")
                else:
                    print("[Idle] هیچ پۆزیشنێکی کراوە نییە لە ئێستادا.")
            else:
                print(f"[API Error] تۆکنەکە کێشەی هەیە یان بەسەرچووە: {response.text}")
                SESSION_TOKEN = ""

        except Exception as e:
            print(f"[Loop Error] {e}")

        time.sleep(30)

if __name__ == "__main__":
    start_sar_engine()