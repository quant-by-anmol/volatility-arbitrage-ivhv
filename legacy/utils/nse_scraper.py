import datetime
import json
import os

import pandas as pd
import requests

# --------🔧 HEADERS --------
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Referer": "https://www.nseindia.com/option-chain",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Cookie": "AKA_A2=A; _ga=GA1.1.1523076279.1754135728; bm_mi=7019FBE48B8B2F35ACB04DAC0663196A~YAAQNK3OF0oAbFWYAQAA79Sjahw6M9+X7BLnyFnWvzR9CVLLy2ZsMQ9LywWKXbOsqoLUcCnZd8beS4NEAWtv+HeQpRNEjVDG4HzotXt2Tb4I/ExlG1t7SLCRU+NQHotZh4ys2FtBnWbL1atLKD76CvlM3vVH1Pz+scsPsbvSSrfTjDZfYiAbH0E0MR4TNtXKgYi3C5fdki98iQjOqkwQPq1TEzzbd1nFBzChvbtZOSME5HXw5zwcXwAjVghzJGzE+Qi/6eee9XwBMTwMeX5ku5KhqFmzMlpu+xFJZpqdEbnYmav7xoRUSTvKLHaUa6DKbl2zEUU/kXimbZF1~1; _abck=68E7A7E9985006EBBCA7EA9D10EDF486~0~YAAQNK3OF00AbFWYAQAAs9Wjag7EoZjs7iDzDLwVTXf5F7ALlQ8St6Xx68a/KMF9mZBEwHuvIRJtdZxfmXEFg5YJrcqblY5kzBcvLRX9/YVZlDznb13/IoPmXQdy+NQOrcuhB0M2giQWX6cLSIKgqdYH5KipHu4MxnajQTRMi6Rkbs8SefRaErtPGSJYgsUn0S5bKDLYDoX3SCxjzQqNsB6gDVV/OMQg4FEWZeojYaEfANQAr4bYjh0iNB+jh+uvoU5QMuIHZBDCQZOFvn7fX0soqBJoebMT6EMB5CE0MtJZSYUhQGgs+Mr1euGAEgdwlVytRK5pD7Fdo6fOc2pGWYWE4cFkHlCffEmQwv6gWu5SZhZxDCOYA1cfbtwhAWv9fuKk4VLeUiiSbQXZOw9sS7AEIcA4B1kFXJX9f3yLOlb2qptUivrH/r450DbD3bD9BZGLaixbBlbIsBsE3bRFvG9S0wR0Q908dXwKvjgmWng72pGuYAqwT/3iZCUKBchFGoLs/xqeIO60I/alpwhexD38CHltCxDgCmLf2lLvbrMs7WxbKmJGq8VQk+Xr5z7RdhAlMh48+MGs3gf2roAegFUjvDTY3NWxlQvul6jzLspwJvewHppwy1jtRek3sMx6~...",
}

BASE_URL = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"

# --------📁 FIXED BASE PATH --------
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


# --------📡 STEP 1: Fetch Raw JSON from NSE --------
def fetch_nifty_option_chain():
    session = requests.Session()
    session.headers.update(HEADERS)

    # Hit base URL first to set cookies
    session.get("https://www.nseindia.com", timeout=5)
    response = session.get(BASE_URL, timeout=10)

    if response.status_code != 200:
        raise Exception(
            "Failed to fetch option chain. Status code:", response.status_code
        )

    return response.json()


# --------💾 STEP 2: Save Raw JSON to /data/options_raw --------
def save_raw_json(raw_json, date_str):
    dir_path = os.path.join(BASE_PATH, "data", "options_raw")
    os.makedirs(dir_path, exist_ok=True)

    path = os.path.join(dir_path, f"nifty_chain_{date_str}.json")
    with open(path, "w") as f:
        json.dump(raw_json, f, indent=2)

    print(f"✅ Raw JSON saved: {path}")


# --------🧠 STEP 3: Extract ATM IV & Prices --------
def parse_atm_iv_and_premiums(raw_json):
    records = raw_json.get("records", {})
    data = records.get("data", [])
    spot = float(records.get("underlyingValue", 0))

    if not data:
        raise Exception("Empty option chain data")

    all_strikes = [d["strikePrice"] for d in data]
    atm_strike = min(all_strikes, key=lambda x: abs(x - spot))

    for entry in data:
        if entry["strikePrice"] == atm_strike:
            ce = entry.get("CE")
            pe = entry.get("PE")
            if not ce or not pe:
                raise Exception("Missing CE or PE data at ATM")

            return {
                "date": datetime.date.today().strftime("%Y-%m-%d"),
                "spot": spot,
                "atm_strike": atm_strike,
                "ce_iv": ce.get("impliedVolatility"),
                "pe_iv": pe.get("impliedVolatility"),
                "ce_price": ce.get("lastPrice"),
                "pe_price": pe.get("lastPrice"),
            }

    raise Exception("ATM strike not found")


# --------💾 STEP 4: Save Clean Data to /data/parsed_iv_data --------
def save_clean_csv(entry, date_str):
    dir_path = os.path.join(BASE_PATH, "data", "parsed_iv_data")
    os.makedirs(dir_path, exist_ok=True)

    path = os.path.join(dir_path, f"nifty_iv_{date_str}.csv")
    pd.DataFrame([entry]).to_csv(path, index=False)

    print(f"✅ Parsed IV data saved: {path}")


# --------🚀 MASTER: Run All Steps --------
def fetch_and_save_nifty_iv():
    today = datetime.date.today().strftime("%Y-%m-%d")

    try:
        raw_json = fetch_nifty_option_chain()
        save_raw_json(raw_json, today)

        entry = parse_atm_iv_and_premiums(raw_json)
        save_clean_csv(entry, today)

        print("✅ Done! IV & premium data fetched.")
        print(entry)

    except Exception as e:
        print("❌ Error:", str(e))
