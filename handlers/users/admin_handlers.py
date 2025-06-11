import asyncio
import logging

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton

from data.config import ADMINS, update_env_admins
from handlers.users.middleware import SubscriptionMiddleware
from keyboards.default.admin_menu import admin_menu
from loader import dp, bot, user_db

# Logging sozlamasi
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Middleware ni sozlash
def setup_subscription_middleware():
    dp.middleware.setup(SubscriptionMiddleware())

# States for admin add and remove
class AdminAdd(StatesGroup):
    telegram_id = State()

class AdminRemove(StatesGroup):
    telegram_id = State()
    is_confirm = State()

# Asosiy adminni tekshirish funksiyasi
def is_main_admin(user_id: int):
    """Faqat birinchi admin (ADMINS[0]) asosiy admin hisoblanadi."""
    return user_id == ADMINS[0] if ADMINS else False

# Admin paneli
@dp.message_handler(Command("admin"))
async def admin_panel(message: types.Message):
    if user_db.check_if_admin(message.from_user.id) or message.from_user.id in ADMINS:
        await message.answer("Admin paneliga xush kelibsiz! Kerakli bo‘limni tanlang:", reply_markup=admin_menu)
    else:
        await message.answer("🚫 Siz admin emassiz.")

# Statistika ko‘rish
@dp.message_handler(text="📊 Statistika")
async def show_stats(message: types.Message):
    if not user_db.check_if_admin(message.from_user.id) and message.from_user.id not in ADMINS:
        await message.answer("🚫 <b>Siz admin emassiz.</b>", parse_mode="HTML")
        return

    try:
        total_users = user_db.count_users()
        daily_users = user_db.count_daily_users()
        weekly_users = user_db.count_weekly_users()
        monthly_users = user_db.count_monthly_users()
        active_daily = user_db.count_active_daily_users()
        active_weekly = user_db.count_active_weekly_users()
        active_monthly = user_db.count_active_monthly_users()

        stats_message = (
            "📊 <b>Statistika</b>\n"
            "─────────────────\n"
            "👥 Foydalanuvchilar: <b>{total_users}</b>\n"
            "─────────────────\n"
            "🗓 Kunlik: <b>{daily_users}</b> | Faol: <b>{active_daily}</b>\n"
            "📅 Haftalik: <b>{weekly_users}</b> | Faol: <b>{active_weekly}</b>\n"
            "📆 Oylik: <b>{monthly_users}</b> | Faol: <b>{active_monthly}</b>"
        ).format(
            total_users=total_users,
            daily_users=daily_users,
            weekly_users=weekly_users,
            monthly_users=monthly_users,
            active_daily=active_daily,
            active_weekly=active_weekly,
            active_monthly=active_monthly
        )

        markup = InlineKeyboardMarkup().add(
            InlineKeyboardButton("🔄 Yangilash", callback_data="refresh_stats")
        )
        await message.answer(stats_message, parse_mode="HTML", reply_markup=markup)
    except Exception as e:
        await message.answer("❌ <b>Statistika olishda xatolik yuz berdi.</b>", parse_mode="HTML")
        logger.error(f"Error fetching stats: {e}")

# Callback handler - Yangilash tugmasi uchun
@dp.callback_query_handler(lambda c: c.data == "refresh_stats")
async def refresh_stats_callback(callback: types.CallbackQuery):
    stages = [
        "✨ <b>Yangilanmoqda</b> |◦◦◦◦◦|",
        "✨ <b>Yangilanmoqda</b> |●◦◦◦◦|",
        "✨ <b>Yangilanmoqda</b> |●●◦◦◦|",
        "✨ <b>Yangilanmoqda</b> |●●●◦◦|",
        "✨ <b>Yangilanmoqda</b> |●●●●◦|"
    ]

    for stage in stages:
        await callback.message.edit_text(stage, parse_mode="HTML")
        await asyncio.sleep(0.5)

    try:
        total_users = user_db.count_users()
        daily_users = user_db.count_daily_users()
        weekly_users = user_db.count_weekly_users()
        monthly_users = user_db.count_monthly_users()
        active_daily = user_db.count_active_daily_users()
        active_weekly = user_db.count_active_weekly_users()
        active_monthly = user_db.count_active_monthly_users()

        stats_message = (
            "📊 <b>Statistika</b>\n"
            "─────────────────\n"
            "👥 Foydalanuvchilar: <b>{total_users}</b>\n"
            "─────────────────\n"
            "🗓 Kunlik: <b>{daily_users}</b> | Faol: <b>{active_daily}</b>\n"
            "📅 Haftalik: <b>{weekly_users}</b> | Faol: <b>{active_weekly}</b>\n"
            "📆 Oylik: <b>{monthly_users}</b> | Faol: <b>{active_monthly}</b>"
        ).format(
            total_users=total_users,
            daily_users=daily_users,
            weekly_users=weekly_users,
            monthly_users=monthly_users,
            active_daily=active_daily,
            active_weekly=active_weekly,
            active_monthly=active_monthly
        )

        markup = InlineKeyboardMarkup().add(
            InlineKeyboardButton("🔄 Yangilash", callback_data="refresh_stats")
        )
        await callback.message.edit_text(stats_message, parse_mode="HTML", reply_markup=markup)
        await callback.answer("✅ Muvaffaqiyatli yangilandi!", show_alert=False)
    except Exception as e:
        error_message = (
            "❌ <b>Xatolik!</b>\n"
            "Ma'lumotlarni yangilab bo‘lmadi.\n"
            "Qayta urinib ko‘ring!"
        )
        await callback.message.edit_text(
            error_message,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("♻️ Qayta urinish", callback_data="refresh_stats")
            )
        )
        logger.error(f"Error refreshing stats: {e}")
        await callback.answer("❌ Xatolik yuz berdi!", show_alert=False)

# Admin qo‘shish (faqat asosiy admin uchun)
@dp.message_handler(text="👤 Admin Qo‘shish")
async def admin_add_start(message: types.Message, state: FSMContext):
    if not is_main_admin(message.from_user.id):
        await message.answer("🚫 Faqat asosiy admin yangi admin qo‘sha oladi.")
        return
    await AdminAdd.telegram_id.set()
    await message.answer("👤 Yangi adminning Telegram ID sini kiriting:")

@dp.message_handler(state=AdminAdd.telegram_id, content_types=types.ContentType.TEXT)
async def admin_add_id(message: types.Message, state: FSMContext):
    if message.text == "🔙 Admin menyu":
        await state.finish()
        await message.answer("Jarayon bekor qilindi. Siz bosh menyudasiz.", reply_markup=admin_menu)
        return

    try:
        telegram_id = int(message.text)
        user = user_db.select_user(telegram_id)
        if not user:
            await message.answer("❌ Bu Telegram ID bilan foydalanuvchi topilmadi. Foydalanuvchi bot bilan suhbat boshlagan bo‘lishi kerak.")
            return
        if user_db.check_if_admin(telegram_id) or telegram_id in ADMINS:
            await message.answer("⚠️ Bu foydalanuvchi allaqachon admin.")
            return

        user_db.set_admin(telegram_id)
        if telegram_id not in ADMINS:
            ADMINS.append(telegram_id)
            try:
                update_env_admins(ADMINS)
                logger.info(f"Admin {telegram_id} added successfully.")
            except Exception as e:
                logger.error(f"Failed to update .env file for admin {telegram_id}: {e}")
                await message.answer("❌ .env faylini yangilashda xatolik yuz berdi. Admin ma'lumotlar bazasiga qo'shildi.")
                return
        await message.answer(f"✅ Foydalanuvchi (ID: {telegram_id}) admin sifatida qo‘shildi.")
        try:
            await bot.send_message(telegram_id, "🎉 Siz botning admini sifatida qo‘shildingiz!")
        except Exception as e:
            logger.error(f"Failed to notify new admin {telegram_id}: {e}")
        await state.finish()
        await message.answer("Admin menyusiga qaytish uchun tugmani bosing:", reply_markup=admin_menu)
    except ValueError:
        await message.answer("❌ Iltimos, Telegram ID ni faqat raqam shaklida kiriting.")

# Admin o‘chirish (faqat asosiy admin uchun)
@dp.message_handler(text="🗑 Admin O‘chirish")
async def admin_remove_start(message: types.Message, state: FSMContext):
    if not is_main_admin(message.from_user.id):
        await message.answer("🚫 Faqat asosiy admin adminlarni o‘chira oladi.")
        return
    await AdminRemove.telegram_id.set()
    await message.answer("🗑 O‘chirmoqchi bo‘lgan adminning Telegram ID sini kiriting:")

@dp.message_handler(state=AdminRemove.telegram_id, content_types=types.ContentType.TEXT)
async def admin_remove_id(message: types.Message, state: FSMContext):
    if message.text == "🔙 Admin menyu":
        await state.finish()
        await message.answer("Jarayon bekor qilindi. Siz bosh menyudasiz.", reply_markup=admin_menu)
        return

    try:
        telegram_id = int(message.text)
        if telegram_id == message.from_user.id:
            await message.answer("❌ O‘zingizni adminlikdan o‘chira olmaysiz.")
            return
        user = user_db.select_user(telegram_id)
        if not user:
            await message.answer("❌ Bu Telegram ID bilan foydalanuvchi topilmadi.")
            return
        if not user_db.check_if_admin(telegram_id) and telegram_id not in ADMINS:
            await message.answer("⚠️ Bu foydalanuvchi admin emas.")
            return

        async with state.proxy() as data:
            data['telegram_id'] = telegram_id
        markup = InlineKeyboardMarkup().add(
            InlineKeyboardButton("✅ Tasdiqlash", callback_data="confirm_remove_admin"),
            InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_remove_admin")
        )
        await message.answer(
            f"🗑 Foydalanuvchi (ID: {telegram_id}, Username: {user[2] or 'N/A'}) adminlikdan o‘chirilsinmi?",
            reply_markup=markup
        )
    except ValueError:
        await message.answer("❌ Iltimos, Telegram ID ni faqat raqam shaklida kiriting.")

@dp.callback_query_handler(lambda c: c.data in ["confirm_remove_admin", "cancel_remove_admin"], state=AdminRemove.telegram_id)
async def admin_remove_confirm(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        telegram_id = data['telegram_id']
    if callback.data == "confirm_remove_admin":
        user_db.remove_admin(telegram_id)
        if telegram_id in ADMINS:
            ADMINS.remove(telegram_id)
            try:
                update_env_admins(ADMINS)
                logger.info(f"Admin {telegram_id} removed successfully.")
            except Exception as e:
                logger.error(f"Failed to update .env file for admin {telegram_id}: {e}")
                await callback.message.edit_text("❌ .env faylini yangilashda xatolik yuz berdi. Admin ma'lumotlar bazasidan o'chirildi.")
                return
        await callback.message.edit_text(f"✅ Foydalanuvchi (ID: {telegram_id}) adminlikdan o‘chirildi.")
        try:
            await bot.send_message(telegram_id, "❌ Siz bot adminligidan olib tashlandiniz.")
        except Exception as e:
            logger.error(f"Failed to notify removed admin {telegram_id}: {e}")
    else:
        await callback.message.edit_text("❌ Jarayon bekor qilindi.")
    await state.finish()
    await callback.message.answer("Admin menyusiga qaytish uchun tugmani bosing:", reply_markup=admin_menu)
    await callback.answer()

# Adminlar ro‘yxatini ko‘rish (barcha adminlar uchun ruxsat berilgan)
@dp.message_handler(text="📋 Adminlar Ro‘yxati")
async def show_admins_list(message: types.Message):
    if not user_db.check_if_admin(message.from_user.id) and message.from_user.id not in ADMINS:
        await message.answer("🚫 Siz admin emassiz.")
        return
    try:
        admins = user_db.get_all_admins()
        if not admins:
            await message.answer("📋 Hozirda hech qanday admin yo‘q.")
            return
        admin_list = "\n".join([f"👤 ID: {admin[0]}, Username: {admin[1] or 'N/A'}" for admin in admins])
        await message.answer(f"📋 <b>Adminlar ro‘yxati:</b>\n{admin_list}", parse_mode="HTML")
    except Exception as e:
        await message.answer("❌ Adminlar ro‘yxatini olishda xatolik yuz berdi.")
        logger.error(f"Error fetching admins list: {e}")


# Bosh menyuga qaytish
@dp.message_handler(text="🔙 Admin menyu", state="*")
async def back_to_main_menu(message: types.Message, state: FSMContext):
    await state.finish()
    if user_db.check_if_admin(message.from_user.id) or message.from_user.id in ADMINS:
        await message.answer("Jarayon bekor qilindi. Siz Admin menyudasiz.", reply_markup=admin_menu)
    else:
        await message.answer("Jarayon bekor qilindi.", reply_markup=ReplyKeyboardRemove())

# Bekor qilish handleri
@dp.message_handler(
    lambda message: message.text in [
        "📊 Statistika", "📣 Reklama",
        "👤 Admin Qo‘shish", "🗑 Admin O‘chirish", "📋 Adminlar Ro‘yxati"
    ], state="*")
@dp.message_handler(lambda message: message.text.lower() in ["bekor qilish", "/cancel"], state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.finish()
    if user_db.check_if_admin(message.from_user.id) or message.from_user.id in ADMINS:
        await message.answer("Jarayon bekor qilindi. Siz Admin menyudasiz.", reply_markup=admin_menu)
    else:
        await message.answer("Jarayon bekor qilindi.", reply_markup=ReplyKeyboardRemove())

# Middleware ni faollashtirish
setup_subscription_middleware()