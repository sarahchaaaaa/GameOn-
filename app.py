#!/usr/bin/env python3
from flask import Flask, render_template, request, session, redirect
from datetime import datetime, timedelta
from subprocess import call
import logging
import time

import matplotlib.pyplot as plt
plt.switch_backend('agg')

import mysql.connector
import re
import numpy as np

d = datetime.now() - timedelta(days=42) # time travel to demonstrate how we update game scores

app = Flask(__name__)
app.secret_key = 'your secret key'

mydb = mysql.connector.connect(
    host='localhost',
    user='shwang5',
    passwd='shwang5',
    database='shwang5'
)
dormNames = ['Alumni Hall', 'Baumer Hall', 'Carroll Hall', 'Dillon Hall', 'Duncan Hall', 'Dunne Hall', 'Fisher Hall', 'Keenan Hall', 'Keough Hall', 'Knott Hall', 'O\'Neill Family Hall', 'Morrissey Hall', 'Siegfried Hall', 'Sorin Hall', 'Stanford Hall', 'St. Edward\'s Hall', 'Zahm Hall', 'Pasquerilla East Hall', 'Welsh Family Hall']

@app.route('/')
def home():
    '''routes back to the home page if user not logged in'''
    if 'logged_in' not in session:
        return render_template('login.html')
    else:
        return render_template('home.html', username=session['username'], date=d.date(), time=d)

@app.route('/login', methods=['POST', 'GET'])
def login():
    '''login page that makes sure that the user has an account to log in to'''
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        dbcursor = mydb.cursor()
        dbcursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password))
        account = dbcursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['logged_in'] = True
            session['id'] = account[0]
            session['username'] = username
            # Redirect to home page
            return redirect('/')
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    mydb.commit()
    return render_template('login.html', msg=msg)

@app.route("/logout")
def logout():
    '''logs the user out and resets the session'''
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    mydb.commit()
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    '''registers a new user'''
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form and 'phone' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        phone = request.form['phone']
        dorm = request.form['dorm']
        # Check if account exists using MySQL
        cursor = mydb.cursor()
        selectUserQuery = 'SELECT * FROM accounts WHERE username = %s'
        selectUserArgs = (username,)
        cursor.execute(selectUserQuery, selectUserArgs)
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not re.match(r'[0-9]+', phone):
            msg = 'Phone number must contain only numbers!'
        elif not len(password) >= 6:
            msg = 'Password length must be at least 6 characters long'
        elif not len(phone) != 9:
            msg = 'Phone number must begin with area code!'
        elif not username or not password or not email or not phone:
            msg = 'Please fill out the form!'
        elif not dorm in dormNames:
            msg = 'Please enter a dorm at Notre Dame'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s, %s, 0, %s)', (username, password, email, phone, dorm))
            selectUserQuery = 'SELECT * FROM accounts WHERE username = %s'
            selectUserArgs = (username,)
            cursor.execute(selectUserQuery, selectUserArgs)
            account = cursor.fetchone()

            #creates flask session with new credentials
            session['logged_in'] = True
            session['id'] = account[0]
            session['username'] = username
            mydb.commit()
            # Redirect to home page
            return redirect('/')
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    mydb.commit()
    return render_template('register.html', msg=msg)

@app.route('/profile', methods=['POST', 'GET'])
def profile():
    '''shows the information of the current logged in user'''
    user_id = session['id']
    changeButton = ""
    msg=''
    updateStatus = ""
    # Check if user is loggedin
    if 'logged_in' in session:
        cursor = mydb.cursor()
        if request.method == 'POST' and 'game_id' in request.form:
            #if the user is an admin, can access the forms to submit the results of past games
            game_id = request.form['game_id']
            home_result= request.form['home_result'] 
            home_score= request.form['home_score']
            away_result= request.form['away_result']
            away_score= request.form['away_score']
            # checks to make sure the admin entered the logical scores
            if home_result == 'W' and home_score > away_score and away_result == 'L':
                cursor.execute('UPDATE imleagues SET home_result=%s, home_score=%s, away_result=%s, away_score=%s where id=%s', (home_result, home_score, away_result, away_score, game_id))
            elif home_result == 'L' and home_score < away_score and away_result == 'W':
                cursor.execute('UPDATE imleagues SET home_result=%s, home_score=%s, away_result=%s, away_score=%s where id=%s', (home_result, home_score, away_result, away_score, game_id))
            elif home_result == 'T' and home_score == away_score and away_result == 'T':
                cursor.execute('UPDATE imleagues SET home_result=%s, home_score=%s, away_result=%s, away_score=%s where id=%s', (home_result, home_score, away_result, away_score, game_id))
            else:
                updateStatus = 'Error in updating scores, please check that you entered the correct results'
            mydb.commit()

        # shows the button to change password
        if request.method == 'POST' and 'changeButton' in request.form:
            changeButton = 0

        # makes sure the new password and the password check match before it's submitted
        if request.method == 'POST' and 'new_password' in request.form and 'new_password_check' in request.form and 'new_password' != "":
            new_password = request.form['new_password']
            new_password_check = request.form['new_password_check']
            if new_password == new_password_check:
                cursor.execute('update accounts set password=%s where id=%s', (new_password, session['id']))
                mydb.commit()
                msg = 'Password successfully changed!'
            else:
                msg = 'Error! The passwords must match!'
        # We need all the account info for the user so we can display it on the profile page
        cursor.execute('SELECT * FROM accounts WHERE id = %s', [session['id']])
        account = cursor.fetchone()
        cursor.execute('select * from imleagues where home_result!="W" and home_result !="L" and home_result !="T" and home_team != "" and away_team != ""') # TODO: figure out how to not hardcode the date and time in
        games = cursor.fetchall()
        if len(games) == 0:
            games = ""
        # Show the profile page with account info
        return render_template('profile.html', account=account, user_id=user_id, games=games, changeButton=changeButton, msg=msg, updateStatus=updateStatus )
    # User is not loggedin redirect to login page
    return redirect('/login')

@app.route('/explore', methods=['GET', 'POST'])
def explore():
    '''allows users to search by either team or sport and allow them to follow'''
    cursor = mydb.cursor(buffered=True)
    data = ""
    message = ""
    sport = ""
    teams = ""
    games = ""
    results = "Enter your search!"
    # ensures the user is logged in
    if 'logged_in' in session:
        if request.method == "POST" and 'toggle_status' not in request.form and 'team_name' not in request.form:
            # if the box isn't checked, the user searches by sport
            if 'game_id' in request.form:
                game_id = request.form['game_id']
                cursor = mydb.cursor()
                cursor.execute('INSERT INTO following VALUES (%s, %s, %s)', (int(session['id']), int(game_id), 3))
                message = "Game successfully followed!"
                mydb.commit()
                sport_check = request.form['sport_check']
                sport = sport_check
                print('made it here')
                print(sport)
            else:
                sport = request.form['search']
            cursor.execute('SELECT time, facility, sport, home_team, away_team, id from imleagues WHERE id NOT IN (SELECT game_id FROM following WHERE user_id=%s) AND sport LIKE %s AND time > %s', (session['id'], '%' + sport + '%', d)) # TODO: figure out how to not hardcode the date and time in
            games = cursor.fetchall()
            results = "No Results, Search Again"
            if len(games) == 0:
                games = ""
        elif request.method == "POST":
            # if the box is checked, search by team
            results = "No Results, Search Again"
            if 'team_name' in request.form:
                team_name = request.form['team_name']
                cursor.execute('SELECT id from imleagues where home_team = %s', (team_name,))
                game_ids_from_team = cursor.fetchall()
                for i in game_ids_from_team:
                    cursor.execute('INSERT INTO following VALUES (%s, %s, %s)', (int(session['id']), int(i[0]), 3))
                mydb.commit()
                team = request.form['team_check']
                team = team_name
            else:
                team = request.form['search']
            cursor.execute('SELECT DISTINCT home_team FROM imleagues WHERE id NOT IN (SELECT game_id FROM following WHERE user_id=%s) AND home_team LIKE %s', (session['id'], '%' + team + '%')) # TODO: should we add away team too?
            mydb.commit()
            uniqueTeams = cursor.fetchall()
            uniqueTeamsTuple = ()
            for team in uniqueTeams:
                uniqueTeamsTuple = uniqueTeamsTuple + team

            # add dummy values for sql query
            uniqueTeamsTuple = uniqueTeamsTuple  + ("-1",)
            uniqueTeamsTuple = uniqueTeamsTuple + ("-2",)

            mydb.commit()
            teams = cursor.fetchall()
            teamNames = []
            for team in teams:
                teamNames.append(team[0])
            cursor.execute('SELECT home_team, sport, league, COUNT(*) FROM imleagues WHERE home_team IN {} GROUP BY home_team, sport, league'.format(uniqueTeamsTuple)) # TODO: should we add away team too?
            mydb.commit()
            teams = cursor.fetchall()
        return render_template('explore.html', results=results, data=data, message=message, sport=sport, teams=teams, games=games)
    return redirect('/login')
  
@app.route('/following', methods=['GET', 'POST'])
def following():
    '''shows all the games that the user is following'''
    # Check if user is loggedin
    if 'logged_in' in session:
        message = ''
        pastBets = []
        upcoming = 'None'
        upcomingBets = []
        past = []
        # We need all the account info for the user so we can display it on the profile page
        if 'bet' in request.form:
            # gets the bet from the user input and inserts it into the db
            bet = request.form['bet']
            game_id = request.form['bet_game_id']
            cursor = mydb.cursor()            
            cursor.execute('SELECT bet from following WHERE user_id=%s and game_id=%s', (session['id'], game_id))
            checkBets = cursor.fetchall()
            if bet == 'No Bet':
                saveBet = 3
            elif bet == 'Home Team Win':
                saveBet = 1
            else:
                saveBet = 0
            if checkBets == []:
                cursor.execute('INSERT into following VALUES (%s, %s, %s)', (saveBet, session['id'], game_id))
            else:
                cursor.execute('UPDATE following SET bet=%s WHERE user_id=%s and game_id=%s', (saveBet, session['id'], game_id))
            mydb.commit()

        if 'game_id' in request.form:
            game_id = request.form['game_id']
            cursor = mydb.cursor()
            cursor.execute('SELECT game_id from following where game_id=%s and user_id=%s', (int(game_id), int(session['id'])))
            check = cursor.fetchall()
            cursor.execute('DELETE FROM following where user_id=%s and game_id=%s', (int(session['id']), int(game_id)))
            message = "Game successfully unfollowed!"
            mydb.commit()

        cursor = mydb.cursor()
        cursor.execute('SELECT game_id, user_id FROM following WHERE user_id = %s', [session['id']])
        following = cursor.fetchall() # user_id, game_id tuple
        game_id_tuple = get_gameid_tuples(following)

        # finds all the games the user is following
        if following != []:
            cursor.execute('SELECT id, time, facility, sport, home_team, away_team FROM imleagues WHERE id IN {} AND time > \'{}\''.format(game_id_tuple, d))
            upcoming = cursor.fetchall()
            cursor.execute('SELECT id, time, facility, sport, home_team, away_team, home_result, home_score, away_result, away_score FROM imleagues WHERE id IN {} AND time < \'{}\''.format(game_id_tuple, d))
            past = cursor.fetchall()
            print(past)

        # finds all the upcoming games
        if upcoming != []:
            game_id_tuple = get_gameid_tuples(upcoming)
            cursor.execute('SELECT bet FROM following WHERE following.game_id IN {} AND following.user_id = {} order by game_id'.format(game_id_tuple, session['id']))
            upcomingBets = cursor.fetchall()

        # finds all the past games
        game_id_tuple = get_gameid_tuples(past)
        if past != []:
            cursor.execute('SELECT bet FROM following WHERE following.game_id IN {} AND following.user_id = {}'.format(game_id_tuple, session['id']))
            pastBets = cursor.fetchall()
            print('it goes in there')
        return render_template('following.html', message=message, upcoming=upcoming, past=past, upcomingBets=upcomingBets, pastBets=pastBets)
    # User is not loggedin redirect to login page
    return redirect('/login')

"""Helper function that returns a tuple of all the game IDs of a passed in SQL query result"""
def get_gameid_tuples(gameAttributes):
    game_id_list = []
    if len(gameAttributes) == 0:
        return ()
    # get just game_id's
    for value in gameAttributes:
        game_id_list.append(value[0])
    # add two dummy values to prevent syntax errors from SQL 'IN' command (must have > 1 value)
    game_id_list.append(-1)
    game_id_list.append(-2)

    game_id_tuple = tuple(game_id_list)
    return game_id_tuple


@app.route('/leaderboard', methods=['POST', 'GET'])
def leaderboard():
    '''shows the leaderboard with all of the points'''
     # Check if user is loggedin
    if 'logged_in' in session:
        # We need all the account info for the user so we can display it on the profile page
        cursor = mydb.cursor()
        cursor.execute('SELECT username, points FROM accounts where id != 0 ORDER BY points desc')
        accounts = cursor.fetchall() # user_id, game_id tuple
        game_id_list = []
        print(accounts)
        return render_template('leaderboard.html', accounts=accounts)
    # User is not loggedin redirect to login page
    return redirect('/login')

@app.route('/statistics', methods=['POST', 'GET'])
def statistics():
    '''shows the statistics of a certain searched for team'''
    searchQ="-1"
    accounts=""
    numWins = 0
    numLosses = 0
    winRate = 0
    sport = ""
    league = ""
    team_name=""
    results = "Enter your search!"
     # Check if user is loggedin
    if 'logged_in' in session:
        # We need all the account info for the user so we can display it on the profile page
        if request.method == 'POST':
            searchQ = request.form['search']
            results = 'No Results'
            # searchQ is the query from the search bar
        cursor = mydb.cursor()
        print(type(searchQ))
        newSearch = searchQ
        cursor.execute('select home_team, sport, league from imleagues where home_team LIKE %s limit 1', ('%' + newSearch + '%',))
        team_info = cursor.fetchone()
        '''finds the team information and calculates statistics'''
        if team_info:
            (team_name, sport, league) = team_info
            cursor.execute('select COUNT(*) FROM imleagues where home_team like %s and home_result="W"', ('%' + team_name + '%',))
            numWinsTuple = cursor.fetchone()
            team_info=team_info+numWinsTuple
            numWins = int(numWinsTuple[0])

            cursor.execute('select COUNT(*) FROM imleagues where home_team like %s and home_result="L"', ('%' + team_name + '%',))
            numLossesTuple = cursor.fetchone()
            team_info=team_info+numLossesTuple
            numLosses = int(numLossesTuple[0])
        else:
            team_info=""
        print(team_info)
        if (numWins+numLosses) > 0:
            win_rate = numWins/(numWins + numLosses)
        else:
            win_rate = 0

        # get info of upcoming game
        cursor.execute('SELECT time, facility, home_team, away_team FROM imleagues WHERE sport = %s and (home_team = %s or away_team = %s) and time > %s ORDER BY time LIMIT 1', (sport, team_name, team_name, d))
        next_game = cursor.fetchall()

        ### NEW STUFF ###
        home_games, away_games, games = home_away(newSearch)

        x_axis = []
        game_idx = 1
        for item in games:
            x_axis.append(game_idx)
            game_idx += 1

        y_axis = []
        total_wins = 0
        for i, item in enumerate(games):
            if item[1] == 'W':
                total_wins += 1
            elif item[1] == 'T':
                total_wins += 0.5
            y_axis.append(total_wins/x_axis[i])

        plt.plot(y_axis)
        plt.axis([0,12,0,1])
        plt.ylabel('Win Percentage')
        plt.xlabel('Progression of Season')
        plt.savefig('static/linegraph.png')
        plt.clf()

        bar_home = 0
        bar_away = 0

        for item in home_games:
            if item[1] == 'W':
                bar_home += 1
            elif item[1] == 'T':
                bar_home += 0.5

        for item in away_games:
            if item[1] == 'W':
                bar_away += 1
            elif item[1] == 'T':
                bar_away += 0.5

        objects = ('Home', 'Away')
        y_pos = np.arange(len(objects))
        bars = plt.bar(y_pos, [bar_home, bar_away])
        plt.xticks(y_pos, ['Home', 'Away'])
        bars[0].set_color('#c5f8cd')
        bars[1].set_color('#afeeee')
        plt.ylabel('Number of Wins')
        plt.savefig('static/bargraph.png')
        plt.clf()

        name = newSearch

        cursor.execute('SELECT time, facility, home_team, away_team FROM imleagues WHERE sport = %s and (home_team = %s or away_team = %s) and time > %s ORDER BY time LIMIT 1', (sport, name, name, d))
        next_game = cursor.fetchall()
        home_wins = bar_home + bar_away
        if next_game:
            home_games, away_games, games = home_away(next_game[0][3])
            for item in home_games:
                if item[1] == 'W':
                    bar_home += 1
                elif item[1] == 'T':
                    bar_home += 0.5

            for item in away_games:
                if item[1] == 'W':
                    bar_away += 1
                elif item[1] == 'T':
                    bar_away += 0.5
            away_wins = bar_home + bar_away

            labels = 'Home', 'Away'
            sizes = [home_wins, away_wins]
            colors = ['#c5f8cd', '#afeeee']
            plt.pie(sizes, labels=labels, colors=colors, autopct='%1.0f%%', startangle=90)
            plt.axis('equal')
            plt.savefig('static/piechart.png')
            plt.clf()
        else:
            print('nothing')
        print(team_info)
        return render_template('statistics.html', results=results, team_info=team_info, winRate=win_rate, next_game=next_game) # team_name, sport, league, wins, losses
        
    # User is not loggedin redirect to login page
    return redirect('/login')

def home_away(name):
    '''helper function to find all the necessary information for the home team'''
    cursor = mydb.cursor()
    cursor.execute('SELECT time, home_result FROM imleagues WHERE home_team = %s and (home_result = \"W\" or home_result = \"L\" or home_result = \"T\") ORDER BY time', (name,))
    home_games = cursor.fetchall()

    cursor.execute('SELECT time, away_result FROM imleagues WHERE away_team = %s and (away_result = \"W\" or away_result = \"L\" or away_result = \"T\") ORDER BY time', (name,))
    away_games = cursor.fetchall()

    games = home_games + away_games
    games = sorted(games)
    return home_games, away_games, games

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r

if __name__ == "__main__":
    app.run(host='db.cse.nd.edu',port='5005')
