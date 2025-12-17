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
def home(): return "WA Validator Bot is Active"

def keep_alive():
    port = int(os.environ.get("PORT", 10000))
    Thread(target=lambda: app.run(host='0.0.0.0', port=port)).start()

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
    
    try:
        await page.goto("https://web.whatsapp.com/", timeout=60000)
        await asyncio.sleep(8) 
        
        link_selector = "text='Link with phone number'"
        await page.wait_for_selector(link_selector, timeout=30000)
        await page.click(link_selector)
        
        await asyncio.sleep(2)
        await page.fill('input[aria-label="Type your phone number."]', phone)
        await page.keyboard.press("Enter")
        await asyncio.sleep(5) # Status check karne ke liye wait

        content = (await page.content()).lower()
        
        # Checking Status
        if "is too short" in content or "invalid" in content:
            status = "❌ INVALID (Number galat hai)"
        elif "try again in" in content or "too many times" in content:
            status = "🚫 LIMITED (OTP limit hit hai)"
        elif "two-step verification" in content or "2-step" in content:
            status = "🔒 2FA LOCKED (Password laga hai)"
        elif "enter the 8-character code" in content or "code" in content:
            status = "✅ OTP SENT (Possible hai!)"
        else:
            status = "❓ UNKNOWN (Page load nahi hua)"

        await client.send_message('me', f"📊 **VALIDATION REPORT**\nNumber: `{phone}`\nResult: {status}")
        print(f"[LOG] {phone}: {status}")

    except Exception as e:
        await client.send_message('me', f"⚠️ **ERROR**\nNumber: `{phone}`\nReason: Timeout ya Slow Internet.")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context()
        page = await context.new_page()
        
        client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)
        await client.start()

        # Step 1: Scan Last 10 Numbers
        async for msg in client.iter_messages(GROUP_ID, limit=500):
            if len(processed_numbers) >= 10: break
            if msg.text:
                num_match = re.search(r'\+?\d{10,15}', msg.text)
                if num_match:
                    await validate_number(page, client, num_match.group())
                    await asyncio.sleep(15) # Safety gap

        # Step 2: Live Monitoring
        @client.on(events.NewMessage(chats=GROUP_ID))
        async def handler(event):
            num_match = re.search(r'\+?\d{10,15}', event.raw_text)
            if num_match:
                await validate_number(page, client, num_match.group())

        await client.run_until_disconnected()

if __name__ == "__main__":
    keep_alive()
    asyncio.run(main())
