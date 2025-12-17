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
def home(): return "Bot is Active!"

def keep_alive():
    port = int(os.environ.get("PORT", 10000))
    Thread(target=lambda: app.run(host='0.0.0.0', port=port)).start()

# --- 2. CONFIG ---
API_ID = 31177437
API_HASH = '2edea950fe232f2e0ba6febfcd036452'
SESSION_STR = '1BVtsOMIBu29KyU3npaBUEiwW_M1Mem4iKHV6kCENAw5OepzMGecUxHo5RdGmA9e_Pr2pQPbKlL8_McBe0JAnN5Hts1pHKeGZmV40oBZ6MKu5g-7xuJx1epZZWqN--W-l35ujcq3tl9pb_vALtAotdtNhvgwdgIcty8plWZkTrvS_ru1CQ5MUf_eTP9brXJfwOyn1vC92WVZSGWwApnWtlKX4mmEBEN3GXHUuCyPjp07RdgwadimysqHw-GoIENCdUIoHUkDepofk374gwGGnS4-YYBW81lv53-Pn6wLdi4hE3gxBNOMz29fVjlVa2cDgAvQSnCYsxCD8QqdBkh_VIyIRpeRaOCw='
GROUP_ID = -1003211737650 
TARGET_NAME = "Test Guy"

state = {"waiting": False, "target_num": None}

async def main():
    async with async_playwright() as p:
        # Browser Launch logic
        try:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = await browser.new_context()
            page = await context.new_page()
        except Exception as e:
            print(f"Critical Browser Error: {e}")
            return

        client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)

        @client.on(events.NewMessage(chats=GROUP_ID))
        async def handler(event):
            global state
            text = event.raw_text.lower()

            # 1. Number Detection
            if not state["waiting"]:
                num_match = re.search(r'\+?\d{10,15}', text)
                if num_match:
                    state["target_num"] = num_match.group()
                    state["waiting"] = True
                    # Telegram Update: TRYING
                    await client.send_message('me', f"🔍 **TRYING LOGIN**\nNumber: `{state['target_num']}`\nStatus: Opening WhatsApp Web...")
                    
                    try:
                        await page.goto("https://web.whatsapp.com/", timeout=60000)
                        await page.click('text=Link with phone number', timeout=30000)
                        await page.fill('input[aria-label="Type your phone number."]', state["target_num"])
                        await page.keyboard.press("Enter")
                    except Exception as e:
                        await client.send_message('me', f"❌ **FAILED**\nNumber: `{state['target_num']}`\nReason: Browser Timeout or Link Button missing.")
                        state["waiting"] = False

            # 2. OTP Detection
            elif state["waiting"] and ("whatsapp" in text or "code" in text):
                otp_match = re.search(r'\b\d{6}\b', text)
                if otp_match:
                    otp = otp_match.group()
                    await client.send_message('me', f"📩 **OTP DETECTED**\nNumber: `{state['target_num']}`\nOTP: `{otp}`\nStatus: Entering OTP...")
                    
                    try:
                        await page.type('div[contenteditable="true"]', otp)
                        await asyncio.sleep(15)
                        
                        # Name Change try karna
                        await page.goto("https://web.whatsapp.com/settings/profile", timeout=30000)
                        await page.wait_for_selector('span[data-icon="pencil"]', timeout=10000)
                        await page.click('span[data-icon="pencil"]')
                        await page.fill('div[contenteditable="true"]', TARGET_NAME)
                        await page.keyboard.press("Enter")
                        
                        await client.send_message('me', f"✅ **SUCCESS**\nNumber: `{state['target_num']}`\nStatus: Logged in & Name set to {TARGET_NAME}")
                    except Exception as e:
                        await client.send_message('me', f"⚠️ **PARTIAL SUCCESS**\nNumber: `{state['target_num']}`\nStatus: Logged in but Profile Name change failed.")
                    
                    state["waiting"] = False
                    state["target_num"] = None

        await client.start()
        print("--- BOT LIVE WITH REPORTING ---")
        await client.run_until_disconnected()

if __name__ == "__main__":
    keep_alive()
    asyncio.run(main())
