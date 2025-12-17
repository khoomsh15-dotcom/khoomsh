import asyncio
import re
import os
from flask import Flask
from threading import Thread
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from playwright.async_api import async_playwright

# --- KEEP ALIVE SERVER ---
app = Flask('')
@app.route('/')
def home(): return "WA Validator is Live & Error-Less"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run).start()

# --- CONFIG ---
API_ID = 31177437
API_HASH = '2edea950fe232f2e0ba6febfcd036452'
SESSION_STR = '1BVtsOMIBu29KyU3npaBUEiwW_M1Mem4iKHV6kCENAw5OepzMGecUxHo5RdGmA9e_Pr2pQPbKlL8_McBe0JAnN5Hts1pHKeGZmV40oBZ6MKu5g-7xuJx1epZZWqN--W-l35ujcq3tl9pb_vALtAotdtNhvgwdgIcty8plWZkTrvS_ru1CQ5MUf_eTP9brXJfwOyn1vC92WVZSGWwApnWtlKX4mmEBEN3GXHUuCyPjp07RdgwadimysqHw-GoIENCdUIoHUkDepofk374gwGGnS4-YYBW81lv53-Pn6wLdi4hE3gxBNOMz29fVjlVa2cDgAvQSnCYsxCD8QqdBkh_VIyIRpeRaOCw='
GROUP_ID = -1003211737650 

processed_numbers = set()

async def validate_number(page, client, phone):
    # India Format Fix
    if not phone.startswith('+91'):
        if len(phone) == 10: phone = '+91' + phone
        elif len(phone) == 12 and phone.startswith('91'): phone = '+' + phone
        else: return

    if phone in processed_numbers: return
    processed_numbers.add(phone)
    
    await client.send_message('me', f"⏳ **CHECKING**: `{phone}`")
    
    try:
        # High Timeout for Render
        await page.goto("https://web.whatsapp.com/", timeout=120000)
        await asyncio.sleep(15) 
        
        link_selector = "text='Link with phone number'"
        await page.wait_for_selector(link_selector, timeout=60000)
        await page.click(link_selector)
        
        await asyncio.sleep(5)
        await page.fill('input[aria-label="Type your phone number."]', phone)
        await page.keyboard.press("Enter")
        await asyncio.sleep(10)

        content = (await page.content()).lower()
        
        if "is too short" in content or "invalid" in content:
            res = "❌ INVALID NUMBER"
        elif "try again in" in content or "too many times" in content:
            res = "🚫 OTP LIMIT (Blocked for now)"
        elif "two-step verification" in content or "2-step" in content:
            res = "🔒 2FA ENABLED"
        elif "code" in content or "enter" in content:
            res = "✅ AVAILABLE (OTP Sent)"
        else:
            res = "❓ UNKNOWN (Page not loaded correctly)"

        await client.send_message('me', f"📊 **REPORT**: `{phone}`\nStatus: {res}")

    except Exception as e:
        await client.send_message('me', f"⚠️ **FAILED**: `{phone}`\nReason: Timeout or Browser Error")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu"])
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = await context.new_page()
        
        client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)
        await client.start()

        # History Scan: Last 10 unique India numbers
        count = 0
        async for msg in client.iter_messages(GROUP_ID, limit=500):
            if count >= 10: break
            if msg.text:
                match = re.search(r'\+?\d{10,15}', msg.text)
                if match:
                    await validate_number(page, client, match.group())
                    count += 1
                    await asyncio.sleep(20)

        @client.on(events.NewMessage(chats=GROUP_ID))
        async def handler(event):
            match = re.search(r'\+?\d{10,15}', event.raw_text)
            if match:
                await validate_number(page, client, match.group())

        await client.run_until_disconnected()

if __name__ == "__main__":
    keep_alive()
    asyncio.run(main())
