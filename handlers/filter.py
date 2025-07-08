from aiogram import Router, types, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from bot import bot, supabase
from handlers.start import get_start_menu 

router = Router()

user_filters = {}

class FilterStates(StatesGroup):
    waiting_price_range = State()

@router.callback_query(F.data == "stub_settings")
async def filter_menu(callback: types.CallbackQuery):
    await send_filter_menu(callback)

@router.callback_query(F.data == "exit_to_main")
async def exit_to_main(callback: types.CallbackQuery):
    text, keyboard = get_start_menu()
    await callback.message.edit_text(text, reply_markup=keyboard)


async def send_filter_menu(target: types.Message | types.CallbackQuery):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Задать диапазон цен", callback_data="set_price_range")],
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

        user_filters[message.from_user.id] = {"min": min_price, "max": max_price}
        await message.answer(f"Диапазон установлен: от {min_price} до {max_price} ⭐")

    except ValueError:
        await message.answer("Неверный формат. Введите диапазон в виде `10-50`.")
        return

    await state.clear()
    await send_filter_menu(message)

    
@router.callback_query(F.data == "show_filtered_gifts")
async def show_filtered_gifts(callback: types.CallbackQuery):
    try:
        await callback.message.delete()

        user_id = callback.from_user.id
        filt = user_filters.get(user_id)

        if not filt:
            return await callback.message.answer("Сначала установите фильтр.")
        back_markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="stub_settings")]
        ])

        gifts = await bot.get_available_gifts()
        filtered = [g for g in gifts.gifts if filt["min"] <= g.star_count <= filt["max"]]

        if not filtered:
            return await callback.message.answer("Нет подарков в этом диапазоне.")

        lines = [f"*Подарки от {filt['min']} до {filt['max']} ⭐:*", ""]
        for i, gift in enumerate(filtered, 1):
            lines.append(f"{i}. {gift.sticker.emoji}  `{gift.id}` — ⭐ {gift.star_count}")

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




