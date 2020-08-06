#!/usr/bin/env python3

from datetime import datetime, timedelta
import requests

ACCOUNT_SID = 'ACe1ebce5c1fd4d5876b5349334b8ed0d4'
AUTH_TOKEN = 'a1eb490febbb35e27d6c64d3a001c84a'
API = 'api.twilio.com/2010-04-01/Accounts/'
SEND = 'https://' + ACCOUNT_SID + ':' + AUTH_TOKEN + '@' + API + ACCOUNT_SID + '/Messages.json'

r = requests.post(SEND, data)
print(r.status_code, r.reason)
print(datetime.now() - timedelta(days=42))
print("\n\n")
