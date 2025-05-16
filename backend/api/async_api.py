import aiohttp
from bs4 import BeautifulSoup
import jwt

from yarl import URL

import asyncio

LOGIN_URL = "https://elschool.ru/logon/index"
DIARY_URL = "https://elschool.ru/users/diaries"
MARKS_URL = "https://elschool.ru/users/diaries/grades"

DIARY_PARAMS = {
    "rooId": 1,
    "instituteId": 2095,
    "departmentId": 323518,
    "pupilId": 2773814,
    "week": 10,
}

DAYS_OF_WEEK = {
    "Понедельник": 0,
    "Вторник": 1,
    "Среда": 2,
    "Четверг": 3,
    "Пятница": 4,
    "Суббота": 5,
}


async def create_session() -> aiohttp.ClientSession:
    return aiohttp.ClientSession()


async def login(session: aiohttp.ClientSession, login: str, password: str):
    login_data = {
        "login": login,
        "password": password
    }
    async with session.post(LOGIN_URL, data=login_data) as response:
        if response.status != 200:
            raise Exception(response.status)


async def get_jwt(session: aiohttp.ClientSession) -> str:
    try:
        cookies = session.cookie_jar.filter_cookies(URL(LOGIN_URL))
        token = cookies["JWToken"].value

        return token

    except Exception:
        raise Exception()


async def decode_jwt(token):
    try:
        data = jwt.decode(token, options={"verify_signature": False})

        pupil_id = data["Id"]
        role_parts = data["role"].split(",")
        _, _, _, roo_id, institute_id, department_id = role_parts[:6]

        return {
            "rooId": roo_id,
            "instituteId": institute_id,
            "pupilId": pupil_id,
            "departmentId": department_id,
        }

    except Exception:
        raise Exception()





async def get_diary(session: aiohttp.ClientSession, params: dict) -> dict:

    async with session.get(DIARY_URL, params=params) as response:
        content = await response.text()
        soup = BeautifulSoup(content, 'lxml')
        diary_entries = soup.find("div", class_="diaries").find_all("div", class_="col-6")

        day_homework = {}
        for entry in diary_entries:
            for item in entry.find_all("tbody"):
                homework = {}
                for a in item.find_all("tr", class_="diary__lesson"):
                    try:
                        homework[a.find("div", "flex-grow-1").text] = a.find("div", class_="diary__homework-text").text
                    except AttributeError:
                        pass
                    if a.find("p"):
                        x = a.find("p")
                day_homework[x.text.replace("\xa0", " ")] = homework
                break
        return day_homework


async def get_marks(session: aiohttp.ClientSession, params: dict) -> dict:

    try:

        async with session.get(MARKS_URL, params=params) as response:
            content = await response.text()
            soup = BeautifulSoup(content, 'lxml')
            marks_table = soup.find("table", class_="table table-bordered GradesTable MobileGrades")

            subjects_grades = {}

            for header in marks_table.find_all('thead'):
                for subject_header in header.find_all("th"):
                    subjects_grades[subject_header.text] = []

                body = header.find_next("tbody")
                grades = {}
                for i, row in enumerate(body.find_all("tr")):
                    quarter_grades = []
                    try:
                        ch_mark = row.find("td", class_=["grades-average mark2", "grades-average mark3",
                                                         "grades-average mark4", "grades-average mark5"]).text
                    except Exception:
                        ch_mark = ""
                    for grade in row.find_all("span"):
                        quarter_grades.append(grade.text)
                    grades[f"{i + 1} четверть"] = [quarter_grades, ch_mark]
                subjects_grades[subject_header.text] = grades

            return subjects_grades

    except Exception:
        raise Exception("Ошибка при получении оценок")


async def get_diary_by_day(session: aiohttp.ClientSession, day: str, params: dict) -> dict:

    try:
        async with session.get(DIARY_URL, params=params) as response:
            content = await response.text()
            soup = BeautifulSoup(content, 'lxml')
            diary_entries = soup.find("div", class_="diaries").find_all("div", class_="col-6")

            day_homework = {}
            for entry in diary_entries:
                for item in entry.find_all("tbody"):
                    homework = {}
                    for a in item.find_all("tr", class_="diary__lesson"):
                        try:
                            if a.find("p"):
                                x = a.find("p")
                            if not day.lower() in x.text.lower():                            continue
                            homework[a.find("div", "flex-grow-1").text] = a.find("div", class_="diary__homework-text").text
                        except AttributeError:
                            pass

                        day_homework[x.text.replace("\xa0", " ")] = homework
            return day_homework

    except Exception:
        raise Exception("Ошибка при получении домашнего задания")


async def main():
    e_login = "login"
    password = "password"

    session = await create_session()
    await login(session, e_login, password)

    params = await decode_jwt(await get_jwt(session))

    d = await get_diary(session, params)
    print(d)


if __name__ == "__main__":
    asyncio.run(main())