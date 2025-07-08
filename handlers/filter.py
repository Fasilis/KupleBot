from aiogram import Router, types, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from bot import bot, supabase
from handlers.start import get_start_menu 

router = Router()


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


class FilterStates(StatesGroup):
    waiting_price_range = State()
    waiting_emission_range = State()

@router.callback_query(F.data == "stub_settings")
async def filter_menu(callback: types.CallbackQuery):
    await send_filter_menu(callback)

@router.callback_query(F.data == "exit_to_main")
async def exit_to_main(callback: types.CallbackQuery):
    text, keyboard = get_start_menu()
    await callback.message.edit_text(text, reply_markup=keyboard)

@router.callback_query(F.data == "toggle_limited")
async def toggle_limited_filter(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    filt = await load_filter(user_id)
    new_value = not filt.get("only_limited", False)

    save_filter(user_id, {"only_limited": new_value})
    await send_filter_menu(callback)


async def send_filter_menu(target: types.Message | types.CallbackQuery):
    user_id = target.from_user.id if isinstance(target, types.CallbackQuery) else target.from_user.id
    filt = await load_filter(user_id) 

    only_limited = filt.get("only_limited", False)

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Задать диапазон цен", callback_data="set_price_range")],
        [InlineKeyboardButton(text="💎 Редкие: ✅" if only_limited else "🎯 Редкие: ❌", callback_data="toggle_limited")],
        [InlineKeyboardButton(text="✒️ Задать эмиссию", callback_data="set_emission")],
        [InlineKeyboardButton(text="🔍 Показать подарки", callback_data="show_filtered_gifts")],
        [InlineKeyboardButton(text="🔙 Выйти", callback_data="exit_to_main")]
    ])

    text = "Выбери действие:"

    if isinstance(target, types.CallbackQuery):
        await target.message.edit_text(text, reply_markup=markup)
    else:
        await target.answer(text, reply_markup=markup)


    
@router.callback_query(F.data == "set_price_range")
async def ask_price_range(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите диапазон цен в формате `10-50` (звёзды):", parse_mode=ParseMode.MARKDOWN)
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
    filt = await load_filter(user_id)  # загружаем из базы

    if not filt.get("only_limited"):
        await callback.answer("Сначала включи фильтр на редкие подарки", show_alert=True)
        return

    await callback.message.edit_text("Введите диапазон эмиссии в формате `100-1000`:")
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
        await message.answer("Неверный формат. Введите диапазон как `100-500`.")
        return

    await state.clear()
    await send_filter_menu(message)


@router.callback_query(F.data == "show_filtered_gifts")
async def show_filtered_gifts(callback: types.CallbackQuery):
    try:
        await callback.message.delete()

        user_id = callback.from_user.id
        filt = await load_filter(user_id)  # 🔄 берём фильтр из базы

        if not filt:
            return await callback.message.answer("Сначала установите фильтр.")

        gifts = await bot.get_available_gifts()
        filtered = []

        for gift in gifts.gifts:
            price = getattr(gift, "price", None) or getattr(gift, "star_count", 0)
            if not (filt.get("min", 0) <= price <= filt.get("max", 9999999)):
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
            return await callback.message.answer(text)

        lines = [f"*Подарки от {filt.get('min', 0)} до {filt.get('max', 9999)} ⭐:*", ""]
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





