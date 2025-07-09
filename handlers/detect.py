from aiogram import Router, types, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from bot import bot, supabase
import asyncio
from handlers.filter import load_settings, save_settings

router = Router()

###TEST###

# class fake_gift():
#     def __init__(self, id):
#         self.id = id

# class test_gifts():
#     def __init__(self):
#         self.gifts = []
#         self.create_gift(1)
#         self.create_gift(2)
#         self.create_gift(3)
    

#     def create_gift(self, g_id):
#         gift = fake_gift(g_id)
#         self.gifts.append(gift)


# fake_gifts = test_gifts() 

    
# @router.message(Command("makegift"))
# async def makegift(message: types.Message):
#     g_id = message.text.split(" ")[1]
#     fake_gifts.create_gift(g_id)

###TEST###





def check_notif(user_id: int):
    result = supabase.table("user_settings").select("*").eq("user_id", user_id).execute()
    return result.data[0]["notif_enabled"]

async def init_check(message: types.Message):
    current_gifts = await bot.get_available_gifts()
    # current_gifts = fake_gifts   #TEST
    text = [] 
    for gift in current_gifts.gifts:
        gift_id = gift.id
        if gift_id and not supabase.table("known_gifts").select("gift_id").eq("gift_id", gift.id).execute().data:
            text.append(f"INITIAL CHECK. AVAILABLE GIFT:\n{gift.sticker.emoji} ID:{gift_id}\n")
            supabase.table("known_gifts").insert({'gift_id': gift_id}).execute()
            
    for t in text:
        print(t)            
        

async def check_for_new_gifts(message: types.Message):
    current_gifts = await bot.get_available_gifts()
    # current_gifts = fake_gifts    #TEST
    text = [] 
    for gift in current_gifts.gifts:
        gift_id = gift.id
        if gift_id and not supabase.table("known_gifts").select("gift_id").eq("gift_id", gift_id).execute().data:
            text.append(f"NEW GIFT DETECTED:\n{gift.sticker.emoji} ID:{gift_id}\n")  
            supabase.table("known_gifts").insert({'gift_id': gift_id}).execute()

    
    for user in supabase.table("user_settings").select("*").execute().data:
        if check_notif(user["user_id"]) and text:
            try:
                for t in text:
                    await bot.send_message(chat_id=user["user_id"], text=t)
            except Exception as e:
                print(f"Error sending notification: {e}")            
    return True     
            
    

@router.message(Command("detector")) 
async def detect_gifts(message: types.Message):
    await init_check(message)
    while True:
        try:
            await asyncio.sleep(30)
            if not await check_for_new_gifts(message):
                print("no gifts detected in the past 30 seconds")
        except Exception as e:
            print(f"error: {e}")
            await asyncio.sleep(5)


    
    