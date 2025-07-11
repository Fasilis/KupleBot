from aiogram.filters import Command
from bot import bot, supabase
import asyncio
from handlers.autobuy import buy_while_available
from aiogram import Router, F


router = Router()


def get_notif_enabled_users():
    users = supabase.table("user_info").select("user_id, notif_enabled").execute().data
    return [u["user_id"] for u in users if u["notif_enabled"]]

def get_known_gift_ids():
    return set([str(row["gift_id"]) for row in supabase.table("known_gifts").select("gift_id").execute().data])

async def init_check():
    current_gifts = await bot.get_available_gifts()
    known_ids = get_known_gift_ids()
    text = []

    for gift in current_gifts.gifts:
        if gift.id and gift.id not in known_ids:
            supabase.table("known_gifts").insert({"gift_id": gift.id}).execute()
            text.append(f"INITIAL CHECK. AVAILABLE GIFT:\n{gift.sticker.emoji} ID:{gift.id}\n")
    
    for line in text:
        print(line)


async def check_for_new_gifts():
    current_gifts = await bot.get_available_gifts()
    known_ids = get_known_gift_ids()
    new_gifts = []
    text = []

    for gift in current_gifts.gifts:
        if gift.id and gift.id not in known_ids:
            supabase.table("known_gifts").insert({"gift_id": gift.id}).execute()
            text.append(f"NEW GIFT DETECTED:\n{gift.sticker.emoji} ID:{gift.id}\n")
            new_gifts.append(gift)

    if new_gifts and text:
        for user_id in get_notif_enabled_users():
            try:
                await bot.send_message(chat_id=user_id, text="\n".join(text))
            except Exception as e:
                print(f"Error sending notification to {user_id}: {e}")
    return new_gifts


async def detect_gifts():
    await init_check()

    while True:
        try:
            await asyncio.sleep(30)
            new_gifts = await check_for_new_gifts()
            if new_gifts:
                await buy_while_available(new_gifts)
            else:
                print("No gifts detected in the past 30 seconds")
        except Exception as e:
            print(f"Error during gift detection: {e}")
            await asyncio.sleep(5)
