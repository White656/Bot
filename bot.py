import logging
import asyncio
import io
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

from aiogram import Bot, Dispatcher, F, types, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import aiohttp

API_TOKEN = "7903004765:AAEapDcgiLPw8JDt6OxDssIyRzUKsXxH8w8"

# Ваш эндпоинт, куда загружаем файл (multipart/form-data)
YOUR_API_ENDPOINT = "https://api.student-space.ru/api/v1/docs/upload-pdf"

logging.basicConfig(level=logging.INFO)

# ------------------------------------------------------------------------------------
# Инициализация бота и диспетчера

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()

dp.include_router(router)

# Глобальный набор для блокировки пользователей
locked_users = set()


# ------------------------------------------------------------------------------------
# Состояния (FSM)

class Form(StatesGroup):
    waiting_for_action = State()
    waiting_for_pdf = State()


# ------------------------------------------------------------------------------------
# Создаём FastAPI-приложение
app = FastAPI()


# ------------------------------------------------------------------------------------
# 1. Хендлер /start

@router.message(Command("start"))
async def cmd_start_handler(message: types.Message, state: FSMContext):
    """Показываем меню выбора действия и переходим в состояние waiting_for_action."""
    await state.clear()
    await state.set_state(Form.waiting_for_action)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Пересказ", callback_data="retell"),
            InlineKeyboardButton(text="Лекции по вопросам", callback_data="lectures")
        ],
        [
            InlineKeyboardButton(text="Вопросы по лекциям", callback_data="questions"),
            InlineKeyboardButton(text="Перевод", callback_data="translate")
        ]
    ])
    await message.answer("Выберите действие:", reply_markup=keyboard)


# ------------------------------------------------------------------------------------
# 2. Обработчик нажатия кнопок (retell, lectures, questions, translate)
#    Срабатывает и в waiting_for_action, и в waiting_for_pdf.

@router.callback_query(
    F.data.in_({"retell", "lectures", "questions", "translate"}),
    StateFilter(Form.waiting_for_action, Form.waiting_for_pdf),
)
async def process_action_callback(callback_query: types.CallbackQuery, state: FSMContext):
    action = callback_query.data

    # Сохраняем действие в FSM
    await state.update_data(selected_action=action)

    # Собираем новую клавиатуру (галочки)
    retell_text = "✅ Пересказ" if action == "retell" else "Пересказ"
    lectures_text = "✅ Лекции по вопросам" if action == "lectures" else "Лекции по вопросам"
    questions_text = "✅ Вопросы по лекциям" if action == "questions" else "Вопросы по лекциям"
    translate_text = "✅ Перевод" if action == "translate" else "Перевод"

    new_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=retell_text, callback_data="retell"),
            InlineKeyboardButton(text=lectures_text, callback_data="lectures")
        ],
        [
            InlineKeyboardButton(text=questions_text, callback_data="questions"),
            InlineKeyboardButton(text=translate_text, callback_data="translate")
        ]
    ])

    current_state = await state.get_state()
    if current_state == Form.waiting_for_action:
        # Первый выбор действия: переводим пользователя в waiting_for_pdf
        text_for_user = "Вы выбрали действие. Теперь отправьте PDF-файл (до 5 МБ)."
        await state.set_state(Form.waiting_for_pdf)
    else:
        # Если пользователь УЖЕ в waiting_for_pdf и нажал другую кнопку —
        # просто меняем действие.
        text_for_user = "Вы сменили действие. Теперь отправьте PDF-файл (до 5 МБ)."

    # Обновляем сообщение
    await callback_query.message.edit_text(text=text_for_user, reply_markup=new_keyboard)
    await callback_query.answer()


# ------------------------------------------------------------------------------------
# 3. Пришёл документ в состоянии waiting_for_pdf

@router.message(F.document, Form.waiting_for_pdf)
async def process_pdf_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    document = message.document
    # Проверяем PDF
    if document.mime_type != "application/pdf":
        await message.answer("Это не PDF-файл. Пожалуйста, пришлите PDF.")
        return

    # Ограничение размера 5 МБ
    if document.file_size > 5 * 1024 * 1024:
        await message.answer("Файл слишком большой. Максимальный размер — 5 МБ.")
        return

    # Достаем выбранное действие
    data = await state.get_data()
    selected_action = data.get("selected_action", "no_action")

    # Скачиваем файл с Telegram
    file_info = await bot.get_file(document.file_id)
    file_bytes = await bot.download_file(file_info.file_path)

    # Готовим multipart/form-data
    form_data = aiohttp.FormData()
    form_data.add_field(
        name="file",
        value=file_bytes,
        filename=f"{uuid4()}.pdf",
        content_type="application/pdf"
    )
    form_data.add_field(name="user_id", value=str(user_id))
    # Если нужно, можно передать и действие
    # form_data.add_field(name="action", value=selected_action)

    headers = {
        "X-Admin-Header": "FsfY1VXAHrzTXUDZ57yiNrqXkRbF0"
    }

    async with aiohttp.ClientSession() as session:
        try:
            resp = await session.post(YOUR_API_ENDPOINT, headers=headers, data=form_data)
            if resp.status == 200:
                logging.info(f"Файл от user_id={user_id} успешно отправлен на API")
            else:
                logging.error(f"Ошибка загрузки файла: статус {resp.status} (user_id={user_id})")
        except Exception as e:
            logging.error(f"Исключение при отправке файла user_id={user_id}: {e}")

    await message.answer(
        "PDF получен и отправлен на сервер!\n"
        "Теперь подождите, пока файл будет обработан.\n"
        "После окончания обработки вы сможете отправить новый файл."
    )


# ------------------------------------------------------------------------------------
# 4. Если пользователь шлёт что-то не то (вместо PDF), когда мы ждём PDF

@router.message(StateFilter(Form.waiting_for_pdf))
async def process_non_pdf_handler(message: types.Message):
    await message.answer("Пожалуйста, пришлите PDF-файл (до 5 МБ).")


# ------------------------------------------------------------------------------------
# 5. Эндпойнт /external-webhook (от стороннего сервиса)
#    Здесь мы «разблокируем» пользователя и можем отправить файл обратно, если нужно.

@app.post("/external-webhook")
async def external_webhook(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    file_url = data.get("file_url")

    print(user_id)

    if not user_id:
        return JSONResponse({"ok": False, "error": "user_id is required"}, status_code=400)

    if file_url:
        # Отправляем документ напрямую (мы в асинхронном контексте, можно просто await)

        await bot.send_document(
            chat_id=user_id,
            document=file_url,
            caption="Вот ваш обработанный файл!"
        )

    return {"ok": True}


# ------------------------------------------------------------------------------------
# Запускаем и FastAPI, и бота вместе в одном event loop

async def run_fastapi():
    """Запуск Uvicorn-сервера (FastAPI) асинхронно."""
    config = uvicorn.Config(app, host="127.0.0.1", port=8100, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()  # Блокирующе, но асинхронно


async def run_bot():
    """Запуск aiogram (long polling)."""
    await dp.start_polling(bot)


async def main():
    # Запускаем обе задачи параллельно в одном event loop
    bot_task = asyncio.create_task(run_bot())
    fastapi_task = asyncio.create_task(run_fastapi())
    await asyncio.gather(bot_task, fastapi_task)


if __name__ == "__main__":
    asyncio.run(main())
