from multiprocessing.dummy import active_children
from flask import Flask 
import typing
import strawberry
import sqlite3

DB_PATH = './games.db' 

@strawberry.type
class Scoreboard:
    winners: str
    losers: str

@strawberry.type
class Game:
    number: int
    comment: str
    scoreboard: 'Scoreboard'

    

@strawberry.type
class User:
    name: str

@strawberry.type
class Query:
    @strawberry.field
    def last_user(self) -> User:
        return User(name="Marco")

    @strawberry.field
    def active_games(self) -> typing.List[Game]:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('select * from games where is_active = 1')
        rows = c.fetchall()
        result = list(map(dict, rows))
        active_games = []

        for game in result:
            active_games.append(Game(
                number = game['number'],
                comment = game['comment'],
                scoreboard = Scoreboard (
                    winners = game['winners'],
                    losers = game['losers']
                )
            ))
        return active_games

    @strawberry.field
    def ended_games(self) -> typing.List[Game]:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('select * from games where is_active = ?', 0)
        rows = c.fetchall()
        result = list(map(dict, rows))
        ended_games = []

        for game in result:
            ended_games.append(Game(
                number = game['number'],
                comment = game['comment'],
                scoreboard = Scoreboard (
                    winners = game['winners'],
                    losers = game['losers']
                )
            ))
        return ended_games



@strawberry.type
class Mutation:
    @strawberry.field
    def add_comment(self, number: int, comment: str) -> Game:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('update games set comment = ? where number = ?', (comment, str(number)))
        conn.commit()
        c.execute('select * from games where number = ?', str(number))
        res = dict(c.fetchone())
        return Game(
            number = res['number'],
            comment = res['comment'],
            scoreboard = Scoreboard (
                winners = res['winners'],
                losers = res['losers']
            )
        )


schema = strawberry.Schema(query=Query, mutation=Mutation)

