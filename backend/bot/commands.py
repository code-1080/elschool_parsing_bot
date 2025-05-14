import logging

from aiogram import Router
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from sqlalchemy import select, update

import asyncio

from backend.db import db
from backend.api import async_api as api
from backend.db.models.user import UserModel

sessions = {}

router = Router()

class Registration(StatesGroup):
    waiting_for_login = State()
    waiting_for_password = State()
    waiting_for_day = State()
    waiting_for_confirm = State()

cancel_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Отменить")]],
    resize_keyboard=True
)


@router.message(Command("start"))
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Бот перезапущен", reply_markup=ReplyKeyboardRemove())


@router.message(Command("reg"))
async def registration(message: Message, state: FSMContext):
    user_id = message.from_user.id

    await message.answer("Введите логин от elschool:", reply_markup=cancel_keyboard)
    await state.set_state(Registration.waiting_for_login)


@router.message(Registration.waiting_for_login)
async def login(message: Message, state: FSMContext):
    if message.text == "Отменить":
        await state.clear()
        await message.answer("Регистрация отменена.", reply_markup=ReplyKeyboardRemove())
        return

    login = message.text
    await state.update_data(login=login)
    await message.answer("Введите пароль от elschool:", reply_markup=cancel_keyboard)
    await state.set_state(Registration.waiting_for_password)


@router.message(Registration.waiting_for_password)
async def password(message: Message, state: FSMContext):
    if message.text == "Отменить":
        await state.clear()
        await message.answer("Регистрация отменена.", reply_markup=ReplyKeyboardRemove())
        return

    try:
        user_id = message.from_user.id
        state_data = await state.get_data()
        login = state_data["login"]
        password = message.text

        db_session = await db.get_session()

        result = await db_session.execute(
            select(UserModel).where(UserModel.telegram_id == user_id)
        )
        user_data = result.scalars().first()

        if user_data:
            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="Да")],
                    [KeyboardButton(text="Нет")],
                ],
                resize_keyboard=True
            )
            await message.answer("Вы уже зарегистрированы. Заменить учётную запись?", reply_markup=keyboard)
            await state.set_state(Registration.waiting_for_confirm)
            await state.update_data(login=login, password=password)
            return

        session = await api.create_session()
        await api.login(session, login, password)
        e_id = await api.get_id(session)

        new_user = UserModel(
            telegram_id=user_id,
            elschool_id=e_id,
            elschool_login=login,
            elschool_password=password
        )
        db_session.add(new_user)
        await db_session.commit()
        sessions[user_id] = session

        await state.clear()
        await message.answer("Вы успешно зарегистрировались", reply_markup=ReplyKeyboardRemove())

    except Exception as error:
        logging.error(error, exc_info=True)
        await message.answer("Ошибка регистрации", reply_markup=ReplyKeyboardRemove())

    finally:
        await db_session.close()


@router.message(Registration.waiting_for_confirm)
async def confirm(message: Message, state: FSMContext):
    if message.text == "Да":
        try:
            data = await state.get_data()

            db_session = await db.get_session()
            login = data["login"]
            password = data["password"]

            session = await api.create_session()
            await api.login(session, login, password)
            e_id = await api.get_id(session)

            sessions[message.from_user.id] = session

            await db_session.execute(update(UserModel).where(UserModel.telegram_id == message.from_user.id).values(elschool_id=e_id, elschool_login=login, elschool_password=password))
            await db_session.commit()

            await message.answer("Вы успешно зарегестрировались", reply_markup=ReplyKeyboardRemove())

            print(sessions)

        except Exception as error:
            await message.answer("Ошибка регистрации", reply_markup=ReplyKeyboardRemove())

        finally:
            await state.clear()
            await db_session.close()


@router.message(Command("get_marks"))
async def get_marks(message: Message, state: FSMContext):
    try:
        if not sessions.get(message.from_user.id):
            await message.answer("Вы не зарегестрированы")
            return await registration(message, state)

        db_session = await db.get_session()
        result = await db_session.execute(select(UserModel.elschool_id).where(UserModel.telegram_id == message.from_user.id))

        user_id = result.scalars().first()

        marks = await api.get_marks(sessions[message.from_user.id], user_id)

        for key, value in marks.items():
            str_marks = f"{key}\n"

            for v_key, v_value in value.items():
                str_marks += f"{v_key}: {','.join(v_value[0])}\n"
                str_marks += f"Четвертная оценка: {v_value[1]}\n\n"
            await message.answer(str_marks)

    except Exception as error:
        await message.answer(str(error), reply_markup=ReplyKeyboardRemove())

    finally:
        await db_session.close()


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
    try:
        day = message.text

        db_session = await db.get_session()
        result = await db_session.execute(select(UserModel.elschool_id).where(UserModel.telegram_id == message.from_user.id))
        user_id = result.scalars().first()


        diary = await api.get_diary_by_day(sessions[message.from_user.id], day, user_id)

        answer = ""
        for key, value in diary.items():
            answer += f"{key}\n"
            for v_key, v_value in value.items():
                answer += f"{v_key}: {v_value}\n"

        await message.answer(answer, reply_markup=ReplyKeyboardRemove())

    except Exception as error:
        await message.answer(str(error))

    finally:
        await db_session.close()
        await state.clear()


@router.message()
async def unknown_command(message: Message):
    await message.answer("Я не знаю как ответить на эту команду")