# Данные хранятся в SQLite базе данных todo.db в таблице todos
# CREATE TABLE "todos" "todo_id" INTEGER PRIMARY KEY, "description" TEXT NOT NULL, "status" TEXT NOT NULL );

import sqlite3
from flask import jsonify, url_for
from fpdf import FPDF
import os

DB_PATH = './profiles.db' 

# Получить все элементы в таблице
def get_all_profiles():
    try:
        conn = sqlite3.connect(DB_PATH)
        # Обеспечивает работу с названиями колонок в таблице
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('select * from profiles')
        rows = c.fetchall()
        result = jsonify( { 'players': list(map(dict, rows)) } )
        return result
    except Exception as e:
        print('Error: ', e)
        return None

def get_profile_raw(login):
    try:
        conn = sqlite3.connect(DB_PATH)
        # Обеспечивает работу с названиями колонок в таблице
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("select * from profiles where login=?;" , [login])
        r = c.fetchone()
        return dict(r)
    except Exception as e:
        print('Error: ', e)
    return None

# Получить отдельный элемент
def get_profile(login):
    result = get_profile_raw(login)
    if result is None:
        return None

    return jsonify(result)

# Добавить элемент в таблицу
def add_to_list(profile):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('insert into profiles(login, avatar, sex, email) values(?,?,?,?)', (profile['login'], profile['avatar'], profile['sex'], profile['email']))
        conn.commit()
        result = get_profile(profile['login'])
        return result
    except Exception as e:
        print('Error: ', e)
        return None

def add_logs(game):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        for winner in game["winners"]:
            c.execute('insert into logs(login, won) values(?, ?)', (winner, True))
        
        for loser in game["losers"]:
            c.execute('insert into logs(login, won) values(?, ?)', (loser, False))

        conn.commit()
        return True
    except Exception as e:
        print('Error: ', e)
        return False

def create_cell(pdf, text):
    pdf.cell(200, 10, txt = text, 
         ln = 1, align = 'C')

async def get_stats(login):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        profile = get_profile_raw(login)
        if profile is None:
            return None
        
        c.execute('select * from logs where login = ?', [login])
        result = c.fetchall()

        stats = {"wins": 0, "games": 0}
        for record in result:
            print(record)
            stats['wins'] += int(record[1])
            stats['games'] += 1
        
        pdf_path = os.path.join(os.getcwd(), login + "_stats.pdf")
        pdf = FPDF()
        pdf.add_page()

        pdf.set_font("Arial", size = 12)
        create_cell(pdf, "login: " + profile['login'])
        create_cell(pdf, "avatar: " + profile['avatar'])
        create_cell(pdf, "sex: " + profile['sex'])
        create_cell(pdf, "email: " + profile['email'])
        create_cell(pdf, "wins: " + str(stats['wins']))
        create_cell(pdf, 'games: ' + str(stats['games']))

        pdf.output(pdf_path)   

        return jsonify(pdf_path)

    except Exception as e:
        print('Error: ', e)
        return None