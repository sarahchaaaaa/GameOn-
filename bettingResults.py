#!/usr/bin/env python3

from flask import Flask, render_template, request, session, redirect
from datetime import datetime, timedelta
import logging
import requests
import mysql.connector
import re
import pandas as pd 

today = datetime.now() - timedelta(days=42) # time travel to demonstrate how we update game scores
yesterday = datetime.now() - timedelta(days=43) # time travel to demonstrate how we update game scores

mydb = mysql.connector.connect(
	host = 'localhost',
	user = 'shwang5',
	passwd = 'shwang5',
	database = 'shwang5')

cursor = mydb.cursor()

"""Helper function that returns a tuple of all the game IDs of a passed in SQL query result"""
def get_gameid_tuples(gameAttributes):
    game_id_list = []
    if len(gameAttributes) == 0:
        return ()
    # get just game_id's
    for value in gameAttributes:
        game_id_list.append(value[1])
    # add two dummy values to prevent syntax errors from SQL 'IN' command (must have > 1 value)
    game_id_list.append(-1)
    game_id_list.append(-2)

    game_id_tuple = tuple(game_id_list)
    return game_id_tuple

print('\n\n')
yesterdays_game_ids = []
yesterdays_game_ids.append(-1)
yesterdays_game_ids.append(-2)
cursor.execute('SELECT id FROM imleagues WHERE time >= \"{}\" and time < \"{}\"'.format(yesterday, today))
yesterdays_games = cursor.fetchall()

for gameID in yesterdays_games:
	yesterdays_game_ids.append(gameID[0])

cursor.execute('SELECT user_id, game_id, bet FROM following WHERE game_id IN {}'.format(tuple(yesterdays_game_ids)))

following = cursor.fetchall()

following_game_id_tuple = get_gameid_tuples(following)
print(following_game_id_tuple)
cursor.execute('SELECT following.user_id, imleagues.home_result, following.bet, imleagues.id FROM following INNER JOIN imleagues ON following.game_id=imleagues.id AND following.game_id in {}'.format(following_game_id_tuple))
joinedTable = cursor.fetchall()

for user_id, game_result, user_bet, game_id in joinedTable:
	if (user_bet == 1 and game_result == 'W') or (user_bet == 0 and game_result == 'L'):
		print("good job u won")
		cursor.execute('UPDATE accounts SET points=points+3 WHERE id=%s', (user_id,))
		mydb.commit()
	elif (user_bet == 1 and game_result == 'T') or (user_bet == 0 and game_result == 'T'):
		print("nice try loser")
		cursor.execute('UPDATE accounts SET points=points+1 WHERE id=%s', (user_id,))
		mydb.commit()
