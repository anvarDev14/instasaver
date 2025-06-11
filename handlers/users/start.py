from datetime import datetime
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.inline import menu
from loader import dp, bot, channel_db, lang_db,  user_db  # db - foydalanuvchilar uchun Database klassi
from states.state import Lang, Update
import asyncio
import logging
import os
from dotenv import load_dotenv

# .env faylini yuklash
load_dotenv()
ADMINS = [int(admin_id) for admin_id in os.getenv("ADMINS", "").split(",") if admin_id.strip().isdigit()]
ADMIN_NICKNAME = "@anvarcode"

# Logging sozlamalari
logging.basicConfig(
    filename='bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Kanalda obuna tekshirish
async def check_subscription(user_id: int, channel_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.error(f"Kanal {channel_id} da {user_id} tekshirishda xatolik: {e}")
        return False

# Barcha kanallarga obuna tekshiruvi
async def is_subscribed_to_all_channels(user_id: int) -> bool:
    try:
        channels = channel_db.get_all_channels()
        if not channels:
            return True
        for channel_id, title, link in channels:
            if not await check_subscription(user_id, channel_id):
                return False
        return True
    except AttributeError as e:
        logger.error(f"Ma'lumotlar bazasida xatolik: {e}")
        raise

# Obuna bo'lmagan kanallar ro'yxati
async def get_unsubscribed_channels(user_id: int) -> list:
    try:
        channels = channel_db.get_all_channels()
        if not channels:
            return []
        return [(link, title) for channel_id, title, link in channels if not await check_subscription(user_id, channel_id)]
    except AttributeError as e:
        logger.error(f"Ma'lumotlar bazasida xatolik: {e}")
        raise

# Inline klaviatura
def get_subscription_keyboard(unsubscribed_channels):
    markup = InlineKeyboardMarkup(row_width=1)
    if unsubscribed_channels:
        for index, (invite_link, title) in enumerate(unsubscribed_channels, start=1):
            if invite_link.startswith("https://t.me/"):
                markup.add(InlineKeyboardButton(f"{index}. ➕ Obuna bo‘lish", url=invite_link))
            else:
                markup.add(InlineKeyboardButton(f"{index}. ➕ Obuna bo‘lish", callback_data="no_action"))
        markup.add(InlineKeyboardButton("✅ Azo bo'ldim", callback_data="check_subscription"))
    return markup

# Foydalanuvchi xabari
def get_welcome_message(lang: str, full_name: str) -> str:
    messages = {
        'ru': f"Добро пожаловать, {full_name}! Бот готов к работе.\n\nАдминистратор - {ADMIN_NICKNAME}\nСвяжитесь с {ADMIN_NICKNAME}, чтобы создать бота",
        'en': f"Welcome, {full_name}! The bot is ready to work.\n\nAdmin - {ADMIN_NICKNAME}\nContact {ADMIN_NICKNAME} to Create a Bot",
        'uz': f"Xush kelibsiz, {full_name}! Bot ishga tayyor.\n\nAdmin - {ADMIN_NICKNAME}\nBot yaratish uchun {ADMIN_NICKNAME} ga murojaat qiling"
    }
    return messages.get(lang, messages['uz'])

# Foydalanuvchini ro'yxatdan o'tkazish (user va lang uchun)
async def register_user(user_id: int, username: str, lang: str = "uz", context: str = "unknown") -> bool:
    try:
        # 1. Foydalanuvchini Users jadvaliga qo'shish
        user_db.add_user(user_id, username)
        # 2. Tilni lang_db ga qo'shish yoki yangilash
        lang_db.add_or_update_lang(user_id, lang)
        logger.info(f"Foydalanuvchi: @{username}, lang: {lang}, Context: {context}")
        for admin in ADMINS:
            try:
                user_info = await bot.get_chat(user_id)
                full_name = user_info.full_name or "Noma'lum"
                join_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                admin_message = (
                    f"🔔 <b>{admin}</b>\n\n"
                    f"👤 <b>Username:</b> @{username}\n"
                    f"📛 <b>Ism:</b> {full_name}\n"
                    f"🆗 <b>ID:</b> {user_id}\n"
                    f"📅 <b>Ro‘yxatdan o‘tgan vaqt:</b> {join_date}\n"
                    f"📍 <b>Kirish usuli:</b> {context}\n"
                    f"────────────────────\n"
                    f"<i>Botdan foydalanish boshlandi!</i>"
                )
                await bot.send_message(admin, admin_message, parse_mode="HTML")
            except Exception as e:
                logger.error(f"Admin {admin} ga xabar yuborishda xatolik: {e}")
        return True
    except Exception as e:
        logger.error(f"Ro'yxatdan o'tkazishda xatolik (Context: {context}): {e}")
        raise

# Avtomatik obuna tekshirish
async def auto_check_subscription(user_id: int, message: types.Message):
    while True:
        await asyncio.sleep(5)
        lang = lang_db.get_lang(user_id) or "uz"
        if await is_subscribed_to_all_channels(user_id):
            new_text = f"👋 {get_welcome_message(lang, message.from_user.full_name)}"
            try:
                await message.edit_text(new_text, parse_mode="HTML")
            except Exception:
                pass
            break
        else:
            unsubscribed = await get_unsubscribed_channels(user_id)
            new_text = "⚠️ <b>Siz hali barcha kanallarga obuna bo'lmadingiz!</b>\n\n👇 Quyidagilarga obuna bo'ling:"
            new_reply_markup = get_subscription_keyboard(unsubscribed)
            try:
                await message.edit_text(new_text, reply_markup=new_reply_markup, parse_mode="HTML")
            except Exception:
                pass

# /start komandasi
@dp.message_handler(CommandStart())
async def bot_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name
    logger.info(f"/start from user_id={user_id}, username={username}")

    if message.chat.type != "private":
        await message.reply("Bot faqat shaxsiy chatda ishlaydi!")
        return

    if user_id in ADMINS:
        await message.answer(
            f"👑 Admin {message.from_user.full_name}! Botga xush kelibsiz.\n✍🏻 {get_welcome_message('uz', message.from_user.full_name)}",
            parse_mode="HTML"
        )
        return

    try:
        await register_user(user_id, username, context="/start")
        lang = lang_db.get_lang(user_id) or "uz"
        if await is_subscribed_to_all_channels(user_id):
            await message.answer(
                f"👋 {get_welcome_message(lang, message.from_user.full_name)}",
                parse_mode="HTML"
            )
        else:
            unsubscribed = await get_unsubscribed_channels(user_id)
            text = "⚠️ <b>Botdan foydalanish uchun quyidagi kanallarga obuna bo‘ling:</b>"
            markup = get_subscription_keyboard(unsubscribed)
            msg = await message.answer(text, reply_markup=markup, parse_mode="HTML")
            if unsubscribed:
                asyncio.create_task(auto_check_subscription(user_id, msg))
    except Exception as e:
        logger.error(f"/start da xatolik: {e}")
        await message.answer("⚠️ Ro‘yxatdan o‘tishda xatolik yuz berdi. Qayta urinib ko‘ring.")

# Til tanlash
@dp.callback_query_handler(state=Lang.lang)
async def bot_echo(message: types.CallbackQuery, state: FSMContext):
    await message.message.delete()
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name
    selected_lang = message.data

    try:
        await register_user(user_id, username, selected_lang, context="lang_select")
        if await is_subscribed_to_all_channels(user_id):
            await message.message.answer(
                f"👋 {get_welcome_message(selected_lang, message.from_user.full_name)}",
                parse_mode="HTML"
            )
        else:
            unsubscribed = await get_unsubscribed_channels(user_id)
            text = "⚠️ <b>Botdan foydalanish uchun quyidagi kanallarga obuna bo‘ling:</b>"
            markup = get_subscription_keyboard(unsubscribed)
            msg = await message.message.answer(text, reply_markup=markup, parse_mode="HTML")
            if unsubscribed:
                asyncio.create_task(auto_check_subscription(user_id, msg))
    except Exception as e:
        logger.error(f"Til tanlashda xatolik: {e}")
        await message.answer("Try again!", show_alert=True)
    await state.finish()

# Til o'zgartirish
@dp.message_handler(commands='lang')
async def change_lang(message: types.Message):
    await message.answer('Choose language 🌐', reply_markup=menu)
    await Update.lang.set()

@dp.callback_query_handler(state=Update.lang)
async def update_lang(message: types.CallbackQuery, state: FSMContext):
    await message.message.delete()
    user_id = message.from_user.id
    selected_lang = message.data

    try:
        lang_db.update_lang(lang=selected_lang, tg_id=user_id)
        if await is_subscribed_to_all_channels(user_id):
            await message.message.answer(
                f"👋 {get_welcome_message(selected_lang, message.from_user.full_name)}",
                parse_mode="HTML"
            )
        else:
            unsubscribed = await get_unsubscribed_channels(user_id)
            text = "⚠️ <b>Hali barcha kanallarga obuna bo‘lmadingiz!</b>\n\n👇 Quyidagilarga obuna bo'ling:"
            markup = get_subscription_keyboard(unsubscribed)
            msg = await message.message.answer(text, reply_markup=markup, parse_mode="HTML")
            if unsubscribed:
                asyncio.create_task(auto_check_subscription(user_id, msg))
    except Exception as e:
        logger.error(f"Til yangilashda xatolik: {e}")
        await message.answer("Try again!", show_alert=True)
    await state.finish()

# Obuna tekshirish callback
@dp.callback_query_handler(lambda c: c.data == "check_subscription")
async def check_subscription_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    username = callback.from_user.username or callback.from_user.full_name

    if user_id in ADMINS:
        await callback.message.edit_text(
            "👑 Siz adminsiz, obuna shart emas!",
            parse_mode="HTML"
        )
        await callback.answer()
        return

    try:
        await register_user(user_id, username, context="check_subscription")
        lang = lang_db.get_lang(user_id) or "uz"
        if await is_subscribed_to_all_channels(user_id):
            await callback.message.edit_text(
                f"👋 {get_welcome_message(lang, callback.from_user.full_name)}",
                parse_mode="HTML"
            )
            await callback.answer()
        else:
            unsubscribed = await get_unsubscribed_channels(user_id)
            text = "⚠️ <b>Hali barcha kanallarga obuna bo‘lmadingiz!</b>\n\n👇 Quyidagilarga obuna bo'ling:"
            markup = get_subscription_keyboard(unsubscribed)
            await callback.message.edit_text(text, reply_markup=markup, parse_mode="HTML")
            await callback.answer("Obunani tekshiring!")
    except Exception as e:
        logger.error(f"Obuna tekshirishda xatolik: {e}")
        await callback.message.edit_text("⚠️ Ro‘yxatdan o‘tishda xatolik yuz berdi. Qayta urinib ko‘ring.", parse_mode="HTML")
        await callback.answer()

# Shaxsiy kanal uchun no_action callback
@dp.callback_query_handler(lambda c: c.data == "no_action")
async def no_action_callback(callback: types.CallbackQuery):
    await callback.answer("Bu shaxsiy kanal. Iltimos, kanal adminidan tasdiq so‘rang.", show_alert=True)