import os
import time
import requests

# وەرگرتنی زانیارییەکان لە ژینگەی Railway
API_URL = "https://mt5.mtapi.io"
ACCOUNT_ID = os.getenv("MT5_ACCOUNT")
PASSWORD = os.getenv("MT5_PASSWORD")
SERVER = os.getenv("MT5_SERVER")

def api_request(endpoint, payload=None):
    if payload is None:
        payload = {}
    payload.update({
        "id": ACCOUNT_ID,
        "password": PASSWORD,
        "server": SERVER
    })
    try:
        response = requests.post(f"{API_URL}/{endpoint}", json=payload, timeout=15)
        return response.json()
    except Exception as e:
        print(f"[Error] پەیوەندی سەرکەوتوو نەبوو: {e}")
        return None

def start_sar_engine():
    print("[VIROS-SAR] مەکینەی دووەم دەستی بە کار کرد لەسەر Railway...")
    
    while True:
        try:
            # پشکنینی پۆزیشنە کراوەکان
            positions = api_request("openPositions")
            
            if positions and isinstance(positions, list):
                for pos in positions:
                    symbol = pos.get("symbol", "")
                    
                    # تەنها چاودێری ئاڵتوون دەکەین
                    if "XAUUSD" in symbol.upper():
                        ticket = pos.get("ticket")
                        pos_type = pos.get("type")  # 0 = Buy, 1 = Sell
                        current_sl = pos.get("sl", 0)
                        
                        print(f"[Tracking] ئاڵتوون دۆزرایەوە | Ticket: {ticket} | جۆر: {'Buy' if pos_type == 0 else 'Sell'} | SL: {current_sl}")
            else:
                print("[Idle] هیچ پۆزیشنێکی کراوە نییە...")

        except Exception as e:
            print(f"[Loop Error] هەڵە لە پشکنین: {e}")

        # هەر ٣٠ چرکە جارێک پشکنین دەکاتەوە
        time.sleep(30)

if __name__ == "__main__":
    start_sar_engine()