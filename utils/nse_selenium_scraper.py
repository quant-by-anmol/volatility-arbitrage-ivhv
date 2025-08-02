import datetime
import json
import os
import time

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def fetch_nifty_option_chain_selenium():
    options = Options()
    options.headless = True
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # install / locate ChromeDriver
    chromedriver_path = ChromeDriverManager().install()

    try:
        # Try Selenium 4+ style
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=options)
    except TypeError:
        # Fallback for older Selenium (<4)
        driver = webdriver.Chrome(
            executable_path=chromedriver_path, chrome_options=options
        )

    try:
        driver.get("https://www.nseindia.com/option-chain")
        time.sleep(3)

        # NSE dynamically loads content using JavaScript — wait & get <pre> tag
        json_text = driver.find_element(By.TAG_NAME, "pre").text
        raw_json = json.loads(json_text)
        return raw_json

    finally:
        driver.quit()


def save_raw_json(raw_json, date_str):
    output_dir = os.path.join(BASE_PATH, "data", "options_raw")
    os.makedirs(output_dir, exist_ok=True)

    path = os.path.join(output_dir, f"nifty_chain_{date_str}.json")
    with open(path, "w") as f:
        json.dump(raw_json, f, indent=2)
    print(f"✅ Raw JSON saved: {path}")


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

    raise Exception("ATM strike not found in option chain")


def save_clean_csv(entry, date_str):
    df = pd.DataFrame([entry])
    output_dir = os.path.join(BASE_PATH, "data", "parsed_iv_data")
    os.makedirs(output_dir, exist_ok=True)

    out_path = os.path.join(output_dir, f"nifty_iv_{date_str}.csv")
    df.to_csv(out_path, index=False)
    print(f"✅ Parsed IV data saved: {out_path}")


def save_json_and_csv_selenium():
    today = datetime.date.today().strftime("%Y-%m-%d")

    try:
        raw_json = fetch_nifty_option_chain_selenium()
        save_raw_json(raw_json, today)

        entry = parse_atm_iv_and_premiums(raw_json)
        save_clean_csv(entry, today)

        print("✅ Done! IV & premium data fetched.")
        print(entry)

    except Exception as e:
        print("❌ Error:", str(e))
