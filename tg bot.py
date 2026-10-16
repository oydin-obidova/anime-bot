import asyncio
import json
import os
from aiogram import Bot, Dispatcher, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command, CommandStart
from aiogram.enums import ChatMemberStatus


Token = '8838945535:AAFID9OwrGVTLUgAvRirPdr2JoYPVYzW4-Q'
bot = Bot(token=Token)
dp=Dispatcher()

Admin_id = [7592919584]
CHENNEL_ID = -1004435220528
DB_FILE = "anime_db.json"

class Anime(StatesGroup):
    video = State()
    code = State()
    description = State()

def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as file:
            return  json.load(file)
    except json.JSONDecodeError:
        return {}

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)



channel_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url="https://t.me/code_blossom_din")],
        [InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_subscription")]
    ]
)


async def is_subscribed(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHENNEL_ID, user_id=user_id)
        return member.status not in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]
    except Exception as e:
        print(f"Obunani tekshirishda xatolik: {e}")
        return False

class DeleteAnime(StatesGroup):
    code = State()

@dp.message(Command("delete"))
async def delete_anime(message: Message, state: FSMContext):
    if message.from_user.id not in Admin_id:
        await message.answer("❌ Faqat admin o'chira oladi!")
        return

    await message.answer("O'chirmoqchi bo'lgan anime kodini yubor:")
    await state.set_state(DeleteAnime.code)


@dp.message(DeleteAnime.code)
async def confirm_delete(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Anime kodini matn ko'rinishida yubor!")
        return

    kod = message.text.strip()
    db = load_db()

    if kod in db:
        del db[kod]
        save_db(db)
        await message.answer("✅ Anime muvaffaqiyatli o'chirildi!")
    else:
        await message.answer("❌ Bunday anime topilmadi!")

    await state.clear()

@dp.message(CommandStart())
async def start(message: Message):
    if message.from_user.id in Admin_id:
        await message.answer("Salom admin! Yangi Anime qo'shish uchun /add buyrug'ini yuboring.")
        return

    user = message.from_user.first_name
    if await is_subscribed(message.from_user.id):
        await message.answer(f"Hurmatli {user}, botga xush kelibsiz!\nAnime kodini yuboring:")
    else:
        await message.answer(
            f"Hurmatli {user}, botdan foydalanish uchun quyidagi kanalimizga obuna bo'ling:",
            reply_markup=channel_keyboard
        )


@dp.callback_query(F.data == "check_subscription")
async def check_sub_btn(callback: CallbackQuery):
    if await is_subscribed(callback.from_user.id):
        await callback.message.delete()
        await callback.message.answer("✅ Obuna tasdiqlandi! Endi Anime kodini yuborishingiz mumkin.")
    else:
        await callback.answer("❌ Siz hali kanalga obuna bo'lmadingiz!", show_alert=True)


@dp.message(Command("add"))
async def add(message: Message, state: FSMContext):
    if message.from_user.id in Admin_id:
        await message.answer("Animening videosini jo'nating:")
        await state.set_state(Anime.video)


@dp.message(Anime.video)
async def video(message: Message, state: FSMContext):
    if not message.video:
        await message.answer("Iltimos, video fayl yuboring!")
        return

    await state.update_data(anime=message.video.file_id)
    await message.answer("Animening kodini jo'nating:")
    await state.set_state(Anime.code)


@dp.message(Anime.code)
async def code(message: Message, state: FSMContext):
    await state.update_data(code=message.text.strip())
    await message.answer("Animening izohini jo'nating:")
    await state.set_state(Anime.description)


@dp.message(Anime.description)
async def description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    malumot = await state.get_data()

    anime = malumot["anime"]
    code = malumot["code"]
    desc = malumot["description"]

    db = load_db()
    db[code] = {
        "file_id": anime,
        "description": desc
    }
    save_db(db)

    await message.answer(f"✅ Anime muvaffaqiyatli saqlandi! Kod: {code}")
    await state.clear()


@dp.message()
async def find_anime(message: Message):
    kod = message.text.strip() if message.text else ""

    if message.from_user.id not in Admin_id:
        if not await is_subscribed(message.from_user.id):
            await message.answer(
                "❌ Botdan foydalanish uchun avval kanalga obuna bo'ling!",
                reply_markup=channel_keyboard
            )
            return

    db = load_db()
    if kod in db:
        find_anime = db[kod]
        await message.answer_video(
            video=find_anime["file_id"],
            caption=f"🎬 <b>Anime kodi:</b> {kod}\n📝 <b>Tavsif:</b> {find_anime['description']}",
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Bunday kodli kino topilmadi. Qayta tekshirib ko'ring.")


async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())