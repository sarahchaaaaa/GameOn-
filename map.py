#!/usr/bin/env python3

from flask import Flask, render_template, request, session, redirect
from datetime import datetime, timedelta
import logging
import requests
import mysql.connector
import re
import json

mydb = mysql.connector.connect(
	host = 'localhost',
	user = 'shwang5',
	passwd = 'shwang5',
	database = 'shwang5')
cursor = mydb.cursor()

d = (datetime.now() - timedelta(days=42))
print('\n\n')
print(d)

MAP_URL = 'https://maps.googleapis.com/maps/api/directions/json'
ORIGIN = ''
DEST = ''
KEY = 'AIzaSyCdWAnvnApHQQQrEWASi4kenttQoeLiNu0'
ACCOUNT_SID = 'ACe1ebce5c1fd4d5876b5349334b8ed0d4'
AUTH_TOKEN = 'a1eb490febbb35e27d6c64d3a001c84a'
PHONE_URL = 'api.twilio.com/2010-04-01/Accounts/'
SEND = 'https://' + ACCOUNT_SID + ':' + AUTH_TOKEN + '@' + PHONE_URL + ACCOUNT_SID + '/Messages.json'

# https://maps.googleapis.com/maps/api/directions/json?origin=Disneyland&destination=Universal+Studios+Hollywood&key=YOUR_API_KEY

cursor.execute('SELECT DISTINCT imleagues.time, imleagues.facility, accounts.dorm, accounts.phone FROM imleagues, following, accounts WHERE imleagues.id = following.game_id and following.user_id = accounts.id and imleagues.time >= \"{}\" and time < \"{}\"'.format(d+timedelta(minutes=15), d+timedelta(minutes=30)))
routes = cursor.fetchall()
print(routes)

for text in routes:
	# send GET request
	ORIGIN = ORIGIN + text[2].replace(' ', '+')
	DEST = DEST + text[1].replace(' ', '+')
	map_data = {'origin':ORIGIN,
				'destination':DEST,
				'mode':'walking',
				'key':KEY}
	r = requests.get(MAP_URL, map_data)
	r_json = json.loads(r.text)
	directions = ''
	for x in r_json['routes'][0]['legs'][0]['steps']:
		inst = x['html_instructions']
		inst = inst.replace('<b>', "")
		inst = inst.replace('</b>', "")
		inst = inst.replace('<div style="font-size:0.9em">', ' ')
		inst = inst.replace('</div>', '')
		dist = x['distance']['text']
		directions += inst + ' ' + dist +'\n'

	duration = r_json['routes'][0]['legs'][0]['duration']['text']
	distance = r_json['routes'][0]['legs'][0]['distance']['text']
	# print(duration)
	# print(distance)

	# print(r_json)

	# send POST request
	phone_data = {'To':'+1' + text[3],
				'From':'+18573040097',
				'Body':'GameOn!\n\nBe sure to go to {} by {}! It will take approximately {} minutes to walk {}.\nDon\'t forget to place your bets!\nTo get to the location:\n{}\n\nDO NOT RESPOND TO THIS TEXT MESSAGE'.format(text[1], text[0], duration, distance, directions)}
	p = requests.post(SEND, phone_data)
	print(p.status_code, p.reason)
