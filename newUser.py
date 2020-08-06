#!/usr/bin/env python3

import mysql.connector
import requests
from datetime import datetime

CURRENT = 12

mydb = mysql.connector.connect(
	host = 'localhost',
	user = 'shwang5',
	passwd = 'shwang5',
	database = 'shwang5')

ACCOUNT_SID = 'ACe1ebce5c1fd4d5876b5349334b8ed0d4'
AUTH_TOKEN = 'a1eb490febbb35e27d6c64d3a001c84a'
API = 'api.twilio.com/2010-04-01/Accounts/'
SEND = 'https://' + ACCOUNT_SID + ':' + AUTH_TOKEN + '@' + API + ACCOUNT_SID + '/Messages.json'
data1 = {'To': '+14029609311',
		'From': '+18573040097',
		'Body': 'THERE IS A NEW USER!'}
data2 = {'To': '+15743396780',
		'From': '+18573040097',
		'Body': 'THERE IS A NEW USER!'}
cursor = mydb.cursor()

cursor.execute('SELECT count(*) FROM accounts')
numUsers = cursor.fetchone()

if numUsers[0] > CURRENT:
	r1 = requests.post(SEND, data1)
	print(r1.status_code, r1.reason)
	r2 = requests.post(SEND, data2)
	print(r2.status_code, r2.reason)
	print(datetime.now() - timedelta(days=42))
	print("\n\n")


