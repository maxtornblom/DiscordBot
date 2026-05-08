import requests, time

session = requests.Session()

headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0",
    "Origin": "https://www.avanza.se",
    "Referer": "https://www.avanza.se/"
}

# 1. Start BankID login
start_url = "https://www.avanza.se/_api/authentication/v2/sessions/bankid"
resp = session.post(start_url, headers=headers, json={ "useEasyLogin": False })
print(resp.json())

order_ref = resp.json()["orderRef"]

# 2. Poll until complete
while True:
    poll_url = f"https://www.avanza.se/_api/authentication/v2/sessions/bankid/collect/{order_ref}"
    r = session.post(poll_url, headers=headers)
    data = r.json()
    print(data)
    if data.get("status") == "COMPLETE":
        print("✅ Inloggad!")
        break
    time.sleep(2)
