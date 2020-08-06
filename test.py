#!/usr/bin/env python3

from flask import Flask, render_template, request, session, redirect
from datetime import datetime, timedelta
import logging
import requests
import mysql.connector
import re
import pandas as pd 

def get_historical(time):
	data = pd.read_csv('/var/www/html/cse30246/gameon/flask/past_weather_needed.csv')
	df = pd.DataFrame(data)
	
	info = df.loc[df['dt_iso'].str.contains(time[:14])]
	if len(info) > 1: 
		info = info.iloc[0]
	temp = float(info['temp'])
	weather = info['weather_main'].item()
	desc = info['weather_description'].item()
	return temp, weather, desc

'''this function makes an API call for upcoming games that are in the future'''
# def get_historical_current(time):
# 	temp = time.split()
# 	time = temp[0] + 'T' + temp[1]
# 	r = requests.get('http://dataservice.accuweather.com/forecasts/v1/hourly/12hour/2258407?apikey=093u3d76eFMmAqlbGRoNO4ywjysLuArB')
# 	json_object = r.json()
# 	for i in range(12):
# 		if time in json_object[i]['DateTime']: 
# 			info = json_object[i]
# 	temp = float(info['Temperature']['Value'])
# 	desc = json_object[i]['IconPhrase']
# 	return temp, desc
	
d = (datetime.now() - timedelta(days=42))

mydb = mysql.connector.connect(
	host = 'localhost',
	user = 'shwang5',
	passwd = 'shwang5',
	database = 'shwang5')

ACCOUNT_SID = 'ACe1ebce5c1fd4d5876b5349334b8ed0d4'
AUTH_TOKEN = 'a1eb490febbb35e27d6c64d3a001c84a'
API = 'api.twilio.com/2010-04-01/Accounts/'
SEND = 'https://' + ACCOUNT_SID + ':' + AUTH_TOKEN + '@' + API + ACCOUNT_SID + '/Messages.json'

cursor = mydb.cursor()

print('\n\n')
print(datetime.now() - timedelta(days=42))

cursor.execute('SELECT id, time, sport, facility, home_team, away_team FROM imleagues WHERE time >= \"{}\" and time < \"{}\"'.format(d+timedelta(hours=1), d+timedelta(hours=2)))

#cursor.execute('SELECT id, time, sport, facility, home_team, away_team FROM imleagues WHERE time >= \"{}\"'.format(d+timedelta(hours=1)))
games = cursor.fetchall()		# tuples of game_id, time, sport, facility, home_team, away_team

game_id_list = []
for game in games:
	game_id_list.append(game[0])
game_id_list.append(-1)
game_id_list.append(-2)
print("SQL QUERY 1 RESULT: ", game_id_list)

cursor.execute('SELECT user_id, game_id FROM following WHERE game_id in {}'.format(tuple(game_id_list)))
users = cursor.fetchall()		# tuples of user_id, game_id

print("SQL QUERY 2 RESULT: ", users)

user_id_list = []
for user in users:
	user_id_list.append(user[0])
user_id_list.append(-1)
user_id_list.append(-2)

cursor.execute('SELECT id, phone FROM accounts WHERE id in {}'.format(tuple(user_id_list)))
phones = cursor.fetchall()		# tuples of user_id, phone
print("SQL QUERY 3 RESULT: ", phones)

for game in games:
	for user in users:
		for phone in phones:
			if (game[0] == user[1] and user[0] == phone[0]):
				temp, weather, desc = get_historical(str(game[1]))
				if temp < float(40): 
					desc += '\nStay warm!'
				if 'Rain' in weather: 
					desc += '\nBring an umbrella!'
				data = {'To':'+1' + phone[1],
						'From':'+18573040097',
						'Body':'GameOn!\n\nYou have an upcoming game!\nSport: {}\nTeams: {} vs. {}\nLocation: {}\nTime: {}\n\nHere is you weather forecast!\nTemperature: {}\nWeather Description: {}\n\nDon\'t forget to place your bets!\n\nDO NOT RESPOND TO THIS TEXT MESSAGE'.format(game[2], game[4], game[5], game[3], game[1], temp, desc)}

				r = requests.post(SEND, data)
				print(r.status_code, r.reason)
