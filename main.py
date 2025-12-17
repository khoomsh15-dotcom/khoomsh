import asyncio
import re
import os
from flask import Flask
from threading import Thread
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from playwright.async_api import async_playwright

# --- 1. KEEP ALIVE SERVER ---
app = Flask('')
@app.route('/')
def home(): return "WA Validator Bot is Live & Stable"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run).start()

# --- 2. CONFIGURATION ---
API_ID = 31177437
API_HASH = '2edea950fe232f2e0ba6febfcd036452'
SESSION_STR = '1BVtsOHkBu2NF_Eed8a3L5smpjnejm_pa6MxxISTt7LA2dJFbNQPCZm8sSfWqGBfM1EkeVd188A2VPqf1QAZwFm2n7pvZCT6P5oSMPkYsBLBtmDFpMF5Mtx3BorsFDgjMryiiUiY4y_LYB7Xkg1VmamnUV5BHCjpTjc3BPq1ksSMjIBxucWrWj7PCqQrIzgGZa380qkeuloYohdMMiskE3iu1cl3jbFLXc6bcQbGpryhwHRZVZeMEZsllM9PasT0oKcbYWggPOvbXWh5rPm4ovaJuRCri_iUaff9BhFWb1QHAj03ERooBhu4sfaOquwWiKH3G88Nn7dC8SoBzuH66POPFY9fa4A4='
GROUP_ID = -1003211737650 

processed_numbers = set()

# --- 3. VALIDATOR LOGIC ---
async def validate_number(page, client, phone):
    # India (+91) Format Fix
    if not phone.startswith('+91'):
        if len(phone) == 10: phone = '+91' + phone
        elif len(phone) == 12 and phone.startswith('91'): phone = '+' + phone
        else: return

    if phone in processed_numbers: return
    processed_numbers.add(phone)
    
    await client.send_message('me', f"⏳ **VALIDATING**: `{phone}`...")
    
    try:
        # High Timeout for Render's Network
        await page.goto("https://web.whatsapp.com/", timeout=120000, wait_until="domcontentloaded")
        await asyncio.sleep(15) 
        
        link_selector = "text='Link with phone number'"
        await page.wait_for_selector(link_selector, timeout=60000)
        await page.click(link_selector)
        
        await asyncio.sleep(5)
        await page.fill('input[aria-label="Type your phone number."]', phone)
        await page.keyboard.press("Enter")
        await asyncio.sleep(12) # Result load hone ka wait

        content = (await page.content()).lower()
        
        # Result Categories
        if "is too short" in content or "invalid" in content:
            status = "❌ INVALID (Number Galat Hai)"
        elif "try again in" in content or "too many times" in content:
            status = "🚫 LIMITED (OTP Limit Hit Hai)"
        elif "two-step verification" in content or "2-step" in content:
            status = "🔒 2FA LOCKED (Password Laga Hai)"
        elif "code" in content or "enter" in content:
            status = "✅ AVAILABLE (OTP Sent!)"
        else:
            status = "❓ UNKNOWN (Page Loading Issue)"

        await client.send_message('me', f"📊 **REPORT**: `{phone}`\nResult: {status}")

    except Exception as e:
        error_msg = str(e)
        reason = "Timeout/Slow Render Net" if "Timeout" in error_msg else "Browser Launch Issue"
        await client.send_message('me', f"⚠️ **FAILED**: `{phone}`\nReason: {reason}")

async def main():
    async with async_playwright() as p:
        # Docker Optimized Browser Launch
        browser = await p.chromium.launch(
            headless=True, 
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)
        await client.start()

        print("--- BOT STARTED: SCANNING LAST 10 ---")
        
        # History Scan (Last 10 Unique India Numbers)
        count = 0
        async for msg in client.iter_messages(GROUP_ID, limit=300):
            if count >= 10: break
            if msg.text:
                match = re.search(r'\+?\d{10,15}', msg.text)
                if match:
                    await validate_number(page, client, match.group())
                    count += 1
                    await asyncio.sleep(20) # 20s gap between checks

        # Live Monitoring
        @client.on(events.NewMessage(chats=GROUP_ID))
        async def handler(event):
            match = re.search(r'\+?\d{10,15}', event.raw_text)
            if match:
                await validate_number(page, client, match.group())

        await client.run_until_disconnected()

if __name__ == "__main__":
    keep_alive()
    asyncio.run(main())
