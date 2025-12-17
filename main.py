import asyncio
import re
import os
from flask import Flask
from threading import Thread
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from playwright.async_api import async_playwright

app = Flask('')
@app.route('/')
def home(): return "Bot is Active & Scanning History!"

def keep_alive():
    port = int(os.environ.get("PORT", 10000))
    Thread(target=lambda: app.run(host='0.0.0.0', port=port)).start()

# --- CONFIG ---
API_ID = 31177437
API_HASH = '2edea950fe232f2e0ba6febfcd036452'
SESSION_STR = '1BVtsOMIBu29KyU3npaBUEiwW_M1Mem4iKHV6kCENAw5OepzMGecUxHo5RdGmA9e_Pr2pQPbKlL8_McBe0JAnN5Hts1pHKeGZmV40oBZ6MKu5g-7xuJx1epZZWqN--W-l35ujcq3tl9pb_vALtAotdtNhvgwdgIcty8plWZkTrvS_ru1CQ5MUf_eTP9brXJfwOyn1vC92WVZSGWwApnWtlKX4mmEBEN3GXHUuCyPjp07RdgwadimysqHw-GoIENCdUIoHUkDepofk374gwGGnS4-YYBW81lv53-Pn6wLdi4hE3gxBNOMz29fVjlVa2cDgAvQSnCYsxCD8QqdBkh_VIyIRpeRaOCw='
GROUP_ID = -1003211737650 
TARGET_NAME = "Test Guy"

processed_numbers = set()

async def try_login(page, client, phone):
    # Same number dobara scan na ho
    if phone in processed_numbers: return
    processed_numbers.add(phone)
    
    await client.send_message('me', f"🔍 **SCANNING**\nNumber: `{phone}`\nStatus: Initializing WhatsApp...")
    try:
        await page.goto("https://web.whatsapp.com/", timeout=60000)
        # Link button click karna
        await page.click('text=Link with phone number', timeout=30000)
        await page.fill('input[aria-label="Type your phone number."]', phone)
        await page.keyboard.press("Enter")
        await client.send_message('me', f"📩 **OTP SENT**\nNumber: `{phone}`\nStatus: Waiting for OTP in group...")
    except Exception as e:
        # Agar error browser file missing ka hai toh reporting
        reason = "Browser Error" if "Executable doesn't exist" in str(e) else str(e)[:50]
        await client.send_message('me', f"❌ **FAILED**\nNumber: `{phone}`\nReason: {reason}")

async def main():
    async with async_playwright() as p:
        # Docker optimized browser launch
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu"])
        context = await browser.new_context()
        page = await context.new_page()
        
        client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)
        await client.start()

        # --- STEP 1: SCAN MASSIVE HISTORY (10,000 Messages) ---
        print("[*] Starting deep scan of last 10,000 messages...")
        await client.send_message('me', "🚀 **HISTORY SCAN STARTED**\nScanning last 10,000 messages. This might take some time...")

        async for msg in client.iter_messages(GROUP_ID, limit=10000):
            if msg.text:
                num_match = re.search(r'\+?\d{10,15}', msg.text)
                if num_match:
                    num = num_match.group()
                    await try_login(page, client, num)
                    # 10 second ka gap taaki WhatsApp block na kare
                    await asyncio.sleep(10)

        # --- STEP 2: LISTEN FOR NEW MESSAGES ---
        @client.on(events.NewMessage(chats=GROUP_ID))
        async def handler(event):
            num_match = re.search(r'\+?\d{10,15}', event.raw_text)
            if num_match:
                await try_login(page, client, num_match.group())

        print("--- DEEP SCAN COMPLETE / LISTENING FOR NEW ---")
        await client.send_message('me', "✅ **DEEP SCAN COMPLETE**\nNow listening for new messages in real-time.")
        await client.run_until_disconnected()

if __name__ == "__main__":
    keep_alive()
    asyncio.run(main())
