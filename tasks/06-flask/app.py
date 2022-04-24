# На основе материалов туториала https://blog.miguelgrinberg.com/post/designing-a-restful-api-with-python-and-flask
# Исходный код туториала: https://github.com/geonaut/flask-todo-rest-api
# Настройка VS Code: https://code.visualstudio.com/docs/python/tutorial-flask
# TODO: доделать авторизацию https://blog.miguelgrinberg.com/post/restful-authentication-with-flask
# Авторизация JWT: https://realpython.com/token-based-authentication-with-flask/

from urllib import response
import helper
from flask import Flask, abort, request
from datetime import datetime
import re

app = Flask(__name__)

@app.route('/mafia/api/v1.0/players/<string:login>', methods=['GET'])
def get_profile(login):
    # Получаем запись из базы данных
    response = helper.get_profile(login)

    # Если не найдено - ошибка 404
    if response is None:
        abort(404)
    
    return response

# Получаем список всех элементов коллекции
@app.route('/mafia/api/v1.0/players', methods=['GET'])
def get_all_players():
    return helper.get_all_profiles()

# Добавить элемент в коллекцию. В теле запроса должен быть передан JSON с полем 'description'
@app.route('/mafia/api/v1.0/players', methods=['POST'])
def add_todo():
    
    # Если в параметрах запроса нет тела, либо нет поля 'description' - отбой 
    if not request.json or not 'profile' in request.json:
        abort(400)
    
    # Получаем поле из запроса
    profile = request.get_json()['profile']

    # Добавляем элемент в базу данных
    response = helper.add_to_list(profile)

    # Если не удачно - возвращаем ошибку 400
    if response is None:
        abort(400)

    # Возвращаем полное описание добавленного элемента
    return response

@app.route('/mafia/api/v1.0/game_result', methods=['POST'])
def add_game():

    if not request.json or "winners" not in request.json or "losers" not in request.json:
        abort(400)
    
    game = request.get_json()
    response = helper.add_logs(game)

    if not response:
        abort(400)
    
    return "OK"

@app.route('/mafia/api/v1.0/stats/<string:login>', methods=['GET'])
async def get_stats(login):
    response = await helper.get_stats(login)
    
    if response is None:
        abort(400)

    return response

