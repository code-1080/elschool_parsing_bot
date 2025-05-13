from aiogram import Router
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from backend.db import db
from backend.api import async_api as api

client = db.db_connect(host="")
users_databse = client["users"]
users_collection = users_databse["users"]

sessions = {}

router = Router()

class Registration(StatesGroup):
    waiting_for_login = State()
    waiting_for_password = State()
    waiting_for_day = State()

@router.message(Command("start"))
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Бот перезапущен", reply_markup=ReplyKeyboardRemove())

@router.message(Command("reg"))
async def registration(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_data = users_collection.find_one({"id": user_id})
    if user_data:
        await message.answer("Вы уже зарегестрированы")
        sessions[user_id] = await api.create_session()
        await api.login(sessions[user_id], user_data["login"], user_data["password"])
    else:
        await message.answer("Введите логин от elschool:")
        await state.set_state(Registration.waiting_for_login)

@router.message(Registration.waiting_for_login)
async def login(message: Message, state: FSMContext):
    login = message.text
    await state.update_data(login=login)
    await message.answer("Введите пароль от elschool:")
    await state.set_state(Registration.waiting_for_password)

@router.message(Registration.waiting_for_password)
async def password(message: Message, state: FSMContext):
    user_id = message.from_user.id
    state_data = await state.get_data()
    login = state_data["login"]
    password = message.text

    session = await api.create_session()
    await api.login(session, login, password)

    e_id = await api.get_id(session)
    users_collection.insert_one({"id": user_id, "login": login, "password": password, "e_id": e_id})
    sessions[user_id] = session

    await state.clear()
    await message.answer("Вы успешно зарегестрировались")

@router.message(Command("get_marks"))
async def get_marks(message: Message, state: FSMContext):
    if not sessions.get(message.from_user.id):
        await message.answer("Вы не зарегестрированы")
        return await registration(message, state)
    marks = await api.get_marks(sessions[message.from_user.id], int(users_collection.find_one({"id": message.from_user.id})["e_id"]))

    for key, value in marks.items():
        str_marks = f"{key}\n"

        for v_key, v_value in value.items():
            str_marks += f"{v_key}: {','.join(v_value[0])}\n"
            str_marks += f"Четвертная оценка: {v_value[1]}\n\n"
        await message.answer(str_marks)

@router.message(Command("get_diary"))
async def get_diary(message: Message, state: FSMContext):
    if not sessions.get(message.from_user.id):
        await message.answer("Вы не зарегестрированы")
        return await registration(message, state)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Понедельник")],
            [KeyboardButton(text="Вторник")],
            [KeyboardButton(text="Среда")],
            [KeyboardButton(text="Четверг")],
            [KeyboardButton(text="Пятница")]
        ],
        resize_keyboard=True
    )
    await state.set_state(Registration.waiting_for_day)
    await message.answer("Выберите вариант:", reply_markup=keyboard)

@router.message(Registration.waiting_for_day)
async def send_password(message: Message, state: FSMContext):
    day = message.text
    diary = await api.get_diary_by_day(sessions[message.from_user.id], day, users_collection.find_one({"id": message.from_user.id})["e_id"])

    answer = ""
    for key, value in diary.items():
        answer += f"{key}\n"
        for v_key, v_value in value.items():
            answer += f"{v_key}: {v_value}\n"

    await message.answer(answer, reply_markup=ReplyKeyboardRemove())
    await state.clear()

@router.message()
async def unknown_command(message: Message):
    await message.answer("Я не знаю как ответить на эту команду")