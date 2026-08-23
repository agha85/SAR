import os
import time
import requests

API_URL = "https://mt5.mtapi.io"
ACCOUNT_ID = os.getenv("MT5_ACCOUNT")
PASSWORD = os.getenv("MT5_PASSWORD")
SERVER = os.getenv("MT5_SERVER")

def api_request(endpoint, params=None):
    if params is None:
        params = {}
    
    # mtapi.io زۆرجار پارامیتەرەکان وەک Query Params لە URL وەردەگرێت
    params.update({
        "id": ACCOUNT_ID,
        "password": PASSWORD,
        "server": SERVER
    })
    
    try:
        response = requests.get(f"{API_URL}/{endpoint}", params=params, timeout=20)
        
        # ئەگەر داواکارییەکە کێشەی هەبوو، دەقی وەڵامەکە چاپ بکە بۆ تێگەیشتن
        if response.status_code != 200:
            print(f"[API Status {response.status_code}] وەڵام: {response.text}")
            return None
            
        return response.json()
    except Exception as e:
        print(f"[Error] هەڵە لە پەیوەندی: {e}")
        return None

def start_sar_engine():
    print(f"[VIROS-SAR] دەستی بە کار کرد | Account: {ACCOUNT_ID} | Server: {SERVER}")
    
    # سەرەتا پشکنینی پەیوەندی دەکەین (Connect / CheckConnect)
    connect_check = api_request("Connect")
    print(f"[Connection Result] {connect_check}")

    while True:
        try:
            positions = api_request("OpenedOrders") or api_request("OrderList")
            
            if positions and isinstance(positions, list):
                print(f"[Active Positions] {len(positions)} پۆزیشن دۆزرایەوە.")
                for pos in positions:
                    symbol = pos.get("Symbol", pos.get("symbol", ""))
                    if "XAUUSD" in symbol.upper() or "GOLD" in symbol.upper():
                        ticket = pos.get("Ticket", pos.get("ticket"))
                        sl = pos.get("StopLoss", pos.get("sl", 0))
                        print(f"[Tracking] ئاڵتوون دۆزرایەوە | Ticket: {ticket} | SL: {sl}")
            else:
                print("[Idle] هیچ پۆزیشنێکی کراوە نییە یان داتا وەرنەگیراوە.")

        except Exception as e:
            print(f"[Loop Error] {e}")

        time.sleep(30)

if __name__ == "__main__":
    start_sar_engine()