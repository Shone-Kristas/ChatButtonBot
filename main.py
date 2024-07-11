import asyncio
import logging
import sys
import requests
import gspread
import datetime

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext


from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.environ.get("TOKEN")
YOOMONEY_LINK = os.environ.get("YOOMONEY_LINK")
YANDEX_IMAGES_URL = os.environ.get("YANDEX_IMAGES_URL")
spreadsheet_id = os.environ.get("SPREADSHEET_ID")

dp = Dispatcher()
bot = Bot(token=TOKEN)

class SearchImage(StatesGroup):
    waiting_for_image_query = State()

class DateInput(StatesGroup):
    waiting_for_date = State()

def is_valid_date(date_text):
    try:
        datetime.datetime.strptime(date_text, '%Y-%m-%d')
        return True
    except ValueError:
        return False


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Кнопка 1")],
            [KeyboardButton(text="Кнопка 2")],
            [KeyboardButton(text="Кнопка 3")],
            [KeyboardButton(text="Кнопка 4")],
            [KeyboardButton(text="Ввести дату")],
        ],
        resize_keyboard=True
    )
    await message.answer("Нажмите на любую кнопку", reply_markup=keyboard)

@dp.message(lambda message: message.text == "Кнопка 1")
async def find_lenina(message: Message) -> None:
    address = "Ленина 1"
    address_for_url = address.replace(" ", "+")
    yandex_maps_url = f"https://yandex.ru/maps/?text={address_for_url}"

    await message.reply(f"Вот ссылка на Яндекс Карты по адресу '{address}':\n{yandex_maps_url}")


@dp.message(lambda message: message.text == "Кнопка 2")
async def pay_2_rubles(message: Message):

    await message.reply(f"Вот ссылка для оплаты 2 рублей через YooMoney:\n{YOOMONEY_LINK}")


@dp.message(lambda message: message.text == "Кнопка 3")
async def ask_for_image_query(message: Message, state: FSMContext):
    await message.answer("Пожалуйста, введите название картинки, которую хотите найти:")
    await state.set_state(SearchImage.waiting_for_image_query)


@dp.message(SearchImage.waiting_for_image_query)
async def send_random_image(message: Message, state: FSMContext):
    user_query = message.text
    search_url = f"{YANDEX_IMAGES_URL}{user_query}"
    response = requests.get(search_url)

    if response.status_code == 200:
        await message.answer(f"Ссылка на вашу картинку: {search_url}")
    else:
        await message.answer("Произошла ошибка при выполнении запроса к Яндекс Картинкам.")

    await state.clear()


@dp.message(lambda message: message.text == "Кнопка 4")
async def google_sheet_A2(message: Message):
    gc = gspread.service_account(filename='tableBot_key.json')
    sh = gc.open_by_key(spreadsheet_id)
    worksheet = sh.worksheet("Sheet1")
    cell_value = worksheet.acell('A2').value
    if cell_value:
        await message.reply(f"Значение ячейки A2: {cell_value}")
    else:
        await message.reply("Не удалось получить значение ячейки А2.")


@dp.message(lambda message: message.text == "Ввести дату")
async def ask_for_date(message: Message, state: FSMContext):
    await message.answer("Пожалуйста, введите дату в формате ГГГГ-ММ-ДД:")
    await state.set_state(DateInput.waiting_for_date)


@dp.message(DateInput.waiting_for_date)
async def validate_and_save_date(message: Message, state: FSMContext):
    date_text = message.text
    gc = gspread.service_account(filename='tableBot_key.json')
    sh = gc.open_by_key(spreadsheet_id)
    worksheet = sh.worksheet("Sheet1")
    if is_valid_date(date_text):
        cell = worksheet.find("")
        if cell:
            row_number = cell.row
        else:
            row_number = len(worksheet.col_values(2)) + 1

        worksheet.update_cell(row_number, 2, date_text)
        await message.answer("Дата верна и добавлена в таблицу.")
    else:
        await message.answer("Дата неверна. Попробуйте снова.")

    await state.clear()


async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())