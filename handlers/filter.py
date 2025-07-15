from aiogram import Router, types, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from bot import bot, supabase
from handlers.start import send_start_menu 
router = Router()

class FilterStates(StatesGroup):
    waiting_price_range = State()
    waiting_emission_range = State()

class ChannelFSM(StatesGroup):
    waiting_for_new_username = State()
    waiting_for_channel_to_add = State()

channel_memory = {}

async def load_filter(user_id: int) -> dict:
    result = supabase.table("user_filters").select("*").eq("user_id", user_id).execute()
    if result.data:
        return result.data[0]
    else:
        default = {
            "user_id": user_id,
            "min_price": 0,
            "max_price": 9999999,
            "only_limited": False,
            "min_emission": None,
            "max_emission": None
        }
        supabase.table("user_filters").insert(default).execute()
        return default

def save_filter(user_id: int, updates: dict):
    supabase.table("user_filters").update(updates).eq("user_id", user_id).execute()


async def load_info(user_id: int) -> dict:
    result = supabase.table("user_info").select("*").eq("user_id", user_id).execute()
    if result.data:
        return result.data[0]
    else:
        default = {
            "user_id": user_id,
            "notif_enabled": False,
            "balance": 0
        }
        supabase.table("user_info").insert(default).execute()
        return default

def save_info(user_id: int, updates: dict):
    supabase.table("user_info").update(updates).eq("user_id", user_id).execute()

class FilterStates(StatesGroup):
    waiting_price_range = State()
    waiting_emission_range = State()

@router.callback_query(F.data == "stub_settings")
async def filter_menu(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.clear()
    await send_filter_menu(callback)
    await callback.answer()

@router.callback_query(F.data == "exit_to_main")
async def exit_to_main(callback: types.CallbackQuery):
        await callback.message.delete()
        await send_start_menu(callback.message, with_banner=True)

@router.callback_query(F.data == "toggle_limited")
async def toggle_limited_filter(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    filt = await load_filter(user_id)
    new_value = not filt.get("only_limited", False)    
    save_filter(user_id, {"only_limited": new_value})
    await send_filter_menu(callback)

async def send_filter_menu(target: types.CallbackQuery | types.Message):
    user_id = target.from_user.id
    chat_id = target.message.chat.id if isinstance(target, types.CallbackQuery) else target.chat.id

    filt = await load_filter(user_id)
    info = await load_info(user_id)

    only_limited = filt.get("only_limited", False)
    notif_enabled = info.get("notif_enabled", False)

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [
         InlineKeyboardButton(text="💎 Редкие: ✅" if only_limited else "🎯 Редкие: ❌", callback_data="toggle_limited"),
         InlineKeyboardButton(text="✒️ Задать эмиссию", callback_data="set_emission")
        ],
        [
         InlineKeyboardButton(text="✏️ Задать диапазон цен", callback_data="set_price_range"),
         InlineKeyboardButton(text="🔍 Показать подарки", callback_data="show_filtered_gifts")
        ],
        [
         InlineKeyboardButton(text=f"{'🔔' if notif_enabled else '🔕'} Обнаружение новых подарков", callback_data="toggle_notif"),
         InlineKeyboardButton(text="🛍️ Покупка подарков на каналы", callback_data="set_channels"),
        ],
        [InlineKeyboardButton(text="🔙 Выйти", callback_data="exit_to_main")]

    ])

    text = "🛠 Выбери действие для настройки фильтров и поиска подарков"

    try:
        if isinstance(target, types.CallbackQuery):
            await target.message.edit_text(text, reply_markup=markup)
        else:
            await target.answer(text, reply_markup=markup)
    except Exception:
        await bot.send_message(chat_id, text, reply_markup=markup)

@router.callback_query(F.data == "set_price_range")
async def ask_price_range(callback: types.CallbackQuery, state: FSMContext):
    markup = InlineKeyboardMarkup(inline_keyboard=[
     [InlineKeyboardButton(text="🔙 Назад", callback_data="stub_settings")]
    ])
    await callback.message.edit_text("Введите диапазон цен в формате `10-50`⭐:", parse_mode=ParseMode.MARKDOWN, reply_markup=markup)
    await state.set_state(FilterStates.waiting_price_range)

@router.message(FilterStates.waiting_price_range)
async def receive_price_range(message: types.Message, state: FSMContext):
    try:
        parts = message.text.replace(" ", "").split("-")
        if len(parts) != 2:
            raise ValueError
        min_price, max_price = map(int, parts)
        if min_price < 0 or max_price < 0 or min_price > max_price:
            raise ValueError

        save_filter(message.from_user.id, {
            "min_price": min_price,
            "max_price": max_price
        })

        await message.answer(f"Диапазон установлен: от {min_price} до {max_price} ⭐")
    except ValueError:
        await message.answer("Неверный формат. Введите диапазон в виде `10-50`.")
        return

    await state.clear()
    await send_filter_menu(message)

@router.callback_query(F.data == "set_emission")
async def ask_emission_range(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    filt = await load_filter(user_id)

    if not filt.get("only_limited"):
        await callback.answer("Сначала включи фильтр на редкие подарки", show_alert=True)
        return

    markup = InlineKeyboardMarkup(inline_keyboard=[
     [InlineKeyboardButton(text="🔙 Назад", callback_data="stub_settings")]
    ])

    await callback.message.edit_text("Введите диапазон эмиссии в формате `100-1000`:", reply_markup=markup)
    await state.set_state(FilterStates.waiting_emission_range)


@router.message(FilterStates.waiting_emission_range)
async def receive_emission_range(message: types.Message, state: FSMContext):
    try:
        parts = message.text.replace(" ", "").split("-")
        if len(parts) != 2:
            raise ValueError

        min_em, max_em = map(int, parts)
        if min_em < 0 or max_em < 0 or min_em > max_em:
            raise ValueError

        save_filter(message.from_user.id, {
            "min_emission": min_em,
            "max_emission": max_em
        })

        await message.answer(f"Эмиссия установлена: от {min_em} до {max_em}")
    except ValueError:
        await message.answer("Неверный формат. Введите диапазон как `100-1000`")
        return

    await state.clear()
    await send_filter_menu(message)


@router.callback_query(F.data == "show_filtered_gifts")
async def show_filtered_gifts(callback: types.CallbackQuery):
    try:
        await callback.message.delete()

        user_id = callback.from_user.id
        filt = await load_filter(user_id)

        if not filt:
            return await callback.message.answer("Сначала установите фильтр.")

        gifts = await bot.get_available_gifts()
        filtered = []

        for gift in gifts.gifts:
            price = getattr(gift, "price", None) or getattr(gift, "star_count", 0)
            if not (filt.get("min_price", 0) <= price <= filt.get("max_price", 9999999)):
                continue

            if filt.get("only_limited"):
                if getattr(gift, "total_amount", None) is None:
                    continue
                total = gift.total_amount or 0
                min_em = filt.get("min_emission", 0)
                max_em = filt.get("max_emission", 9999999)
                if not (min_em <= total <= max_em):
                    continue

            filtered.append((gift, price))

        if not filtered:
            text = "❗ Нет подарков в этом диапазоне.\n\n" + format_filters(filt)
            back_markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="stub_settings")]
            ])
            return await callback.message.answer(text, reply_markup=back_markup)


        lines = [f"*Подарки от {filt.get('min_price', 0)} до {filt.get('max_price', 9999)} ⭐:*", ""]
        for i, (gift, price) in enumerate(filtered, 1):
            emoji = gift.sticker.emoji if gift.sticker else "🎁"
            lines.append(f"{i}. {emoji}  `{gift.id}` — ⭐ {price}")

        back_markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="stub_settings")]
        ])

        await callback.message.answer(
            "\n".join(lines),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_markup
        )

    except Exception as e:
        print(f"Ошибка при показе подарков: {e}")
        await callback.message.answer("Не удалось получить подарки.")



@router.callback_query(F.data == "toggle_notif")
async def toggle_notif(callback: types.CallbackQuery):
    user_id = callback.message.chat.id
    info = await load_info(user_id)
    new_value = not info.get("notif_enabled", False)
    save_info(user_id, {"notif_enabled": new_value})
    await send_filter_menu(callback)


@router.callback_query(F.data == "set_channels")
async def set_channels(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    result = supabase.table("channels").select("*").eq("user_id", user_id).execute()
    channels = result.data

    buttons = []

    # Если есть каналы — добавляем кнопки каналов
    if channels:
        buttons.extend([
            [InlineKeyboardButton(text=ch["username"], callback_data=f"channel_{ch['id']}")]
            for ch in channels
        ])
        title = "Ваши каналы:"
    else:
        title = "У вас пока нет каналов."

    # Кнопка "добавить" — одна для всех случаев
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="stub_settings"), InlineKeyboardButton(text="➕ Добавить канал", callback_data="add_channel")])


    await callback.message.edit_text(
        title,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("channel_"))
async def channel_menu(callback: types.CallbackQuery):
    channel_id = int(callback.data.split("_")[1])
    channel_memory[callback.from_user.id] = channel_id

    buttons = [
        [
            InlineKeyboardButton(text="❌ Удалить", callback_data="delete_channel"),
            InlineKeyboardButton(text="✏️ Изменить", callback_data="edit_channel"),
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="set_channels"),
        ]
    ]

    # Получаем username для показа
    ch_data = supabase.table("channels").select("*").eq("id", channel_id).single().execute().data
    username = ch_data["username"]

    await callback.message.edit_text(
        f"Канал: @{username}\nВыберите действие:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


@router.callback_query(F.data == "delete_channel")
async def delete_channel(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    channel_id = channel_memory.get(user_id)

    if channel_id:
        supabase.table("channels").delete().eq("id", channel_id).execute()

    await callback.answer("Канал удалён.")
    await set_channels(callback)

@router.callback_query(F.data == "edit_channel")
async def edit_channel(callback: types.CallbackQuery, state: FSMContext):
    markup = InlineKeyboardMarkup(inline_keyboard=[
     [InlineKeyboardButton(text="🔙 Назад", callback_data="set_channels")]
    ])

    user_id = callback.from_user.id
    channel_id = channel_memory.get(user_id)

    if not channel_id:
        await callback.answer("Канал не найден.", show_alert=True)
        return

    await state.update_data(editing_channel_id=channel_id)
    await state.set_state(ChannelFSM.waiting_for_new_username)
    await callback.message.edit_text("✏️ Введите новый username канала:", reply_markup=markup)
    await callback.answer()


@router.message(ChannelFSM.waiting_for_new_username)
async def receive_new_username(message: types.Message, state: FSMContext):
    markup = InlineKeyboardMarkup(inline_keyboard=[
     [InlineKeyboardButton(text="🔙 Назад", callback_data="set_channels")]
    ])

    data = await state.get_data()
    channel_id = data.get("editing_channel_id")
    new_username = message.text.strip()

    if not new_username.startswith("@"):
        await message.answer("⚠️ Username должен начинаться с @. Попробуйте снова.", reply_markup=markup)
        return

    username_clean = new_username[1:]

    supabase.table("channels").update({"username": username_clean}).eq("id", channel_id).execute()

    
    await message.answer(f"✅ Канал обновлён: @{username_clean}", reply_markup=markup)
    
    await state.clear()

@router.callback_query(F.data == "add_channel")
async def add_channel(callback: types.CallbackQuery, state: FSMContext):
    markup = InlineKeyboardMarkup(inline_keyboard=[
     [InlineKeyboardButton(text="🔙 Назад", callback_data="set_channels")]
    ])

    await state.set_state(ChannelFSM.waiting_for_channel_to_add)
    await callback.message.edit_text("➕ Введите username нового канала (с @):", reply_markup=markup)
    await callback.answer()


@router.message(ChannelFSM.waiting_for_channel_to_add)
async def save_new_channels(message: types.Message, state: FSMContext):
    markup = InlineKeyboardMarkup(inline_keyboard=[
     [InlineKeyboardButton(text="🔙 Назад", callback_data="set_channels")]
    ])
    
    user_id = message.from_user.id
    text = message.text.strip()

    # Разбиваем по строкам и фильтруем пустые
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # Проверяем, чтобы каждая строка начиналась с @
    cleaned_usernames = []
    for line in lines:
        if line.startswith("@"):
            cleaned_usernames.append(line[1:])  # убираем @
        else:
            await message.answer(f"⚠️ Строка `{line}` должна начинаться с @.", reply_markup=markup)
            return

    # Создаём записи для вставки
    records = [{"user_id": user_id, "username": username} for username in cleaned_usernames]

    # Добавляем в базу все сразу
    supabase.table("channels").insert(records).execute()

    joined = "\n".join(f"✅ Канал @{u} добавлен." for u in cleaned_usernames)
    await message.answer(joined, reply_markup=markup)
    await state.clear()

        
def format_filters(filt: dict) -> str:
    lines = []
    if filt.get("only_limited"):
        lines.append("🎯 Только редкие: ✅")
        if filt.get("min_emission") is not None and filt.get("max_emission") is not None:
            lines.append(f"🎚 Эмиссия: от {filt['min_emission']} до {filt['max_emission']}")
    else:
        lines.append("🎯 Только редкие: ❌")

    lines.append(f"⭐ Цена: от {filt['min_price']} до {filt['max_price']}")
    return "\n".join(lines)





