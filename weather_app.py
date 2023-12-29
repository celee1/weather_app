from flask import Flask, request, render_template
from flask_restful import Api
from datetime import datetime
import requests
import sqlite3
from info import key, db_path


def get_db_connection():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


app = Flask(__name__)
api = Api(app)


@ app.route('/', methods=['GET'])
def get_login():
    return render_template('login.html', failed=False)


@ app.route('/', methods=['POST'])
def login():
    conn = get_db_connection()
    username = request.form.get('username')
    password = request.form.get('password')
    user_exists = conn.execute(
        f'SELECT * FROM user WHERE user = "{username}"').fetchall()
    if user_exists:
        if user_exists[0][1] == password:
            return render_template('app.html', username=username, previous=False, result=False, not_city=False, welcome=True)
    return render_template('login.html', failed=True)


@ app.route('/register', methods=['POST'])
def register():
    return render_template('register.html', register=True, checked=False, fill=False, success=False)


@ app.route('/register/check', methods=['POST'])
def check():
    conn = get_db_connection()
    username = request.form.get('username').lower()
    password = request.form.get('password').lower()
    if username != '' and password != '':
        user_exists = user_exists = conn.execute(
            f'SELECT * FROM user WHERE user = "{username}"').fetchall()
        if user_exists:
            return render_template('register.html', username=username, password=password, available='not available', register=True, checked=True, fill=False, success=False)
        else:
            conn.execute(
                f'INSERT INTO user VALUES ("{username}", "{password}");')
            conn.commit()
            return render_template('register.html', username=username, password=password, register=False, checked=False, fill=False, success=True)
    else:
        return render_template('register.html', username=username, password=password, register=True, checked=False, fill=True, success=False)


@ app.route('/app', methods=['GET', 'POST'])
def get_app():
    username = request.form.get('username')
    fav = request.form.get('favorite')
    city = request.form.get('city')
    if fav:
        conn = get_db_connection()
        conn.execute(
            f'INSERT INTO favorite_locations VALUES ("{city}", "{username}")')
        conn.commit()
    return render_template('app.html', username=username, result=False, not_city=False, previous=False, welcome=request.form.get('welcome'), welcome_back=request.form.get('back'))


@ app.route('/app/temperature', methods=['POST'])
def get_temp():
    conn = get_db_connection()
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    api_key = key
    city = request.form.get('city')
    username = request.form.get('username')
    temperature = False

    favorites = [favourite[0] for favourite in conn.execute(
        f'SELECT * FROM favorite_locations WHERE username = "{username}"').fetchall()]

    for i in range(len(favorites)):
        if '_' in favorites[i]:
            favorites[i] = favorites[i].replace('_', ' ')

    if city != None:
        if city != '':

            complete_url = base_url + "appid=" + \
                api_key + "&q=" + city

            favorites_url = [base_url + 'appid=' + api_key +
                             '&q=' + favorite for favorite in favorites]

            try:
                favorite_list = []

                for i in range(len(favorites_url)):
                    temperature = round(float(requests.get(favorites_url[i]).json()
                                              ['main']['temp']) - 273.15, 2)
                    favorite_list.append([favorites[i], temperature])

                temperature = round(float(requests.get(complete_url).json()
                                          ['main']['temp']) - 273.15, 2)

                n_of_rows = len(conn.execute(
                    'SELECT * FROM input').fetchall())
                date = datetime.now().strftime("%Y/%m/%d, %H:%M:%S")
                conn.execute(
                    f'INSERT INTO input VALUES ("{n_of_rows}", "{city}", "{temperature}", "{username}", "{date}")')
                conn.commit()
            except KeyError:
                pass

    results = [f'{item[0]}, {item[1]} °C. {item[2]}' for item in conn.execute(
        'SELECT city, temperature, date FROM input').fetchall()][-5:]

    results.reverse()

    if temperature:
        return render_template('app.html', city=city, temperature=temperature, results=results, username=username, previous=True, result=True, not_city=False, favorites=favorite_list, welcome=False)
    return render_template('app.html', city=city, results=results, username=username, previous=True, result=False, not_city=True, welcome=False)


@ app.route('/app/manage', methods=['POST'])
def manage_app():
    username = request.form.get('username')
    favorite = request.form.get('favorite')
    conn = get_db_connection()
    if favorite:
        conn.execute(
            f'DELETE FROM favorite_locations WHERE username = "{username}" AND location = "{favorite}";')
        conn.commit()
    favorites = [favorite[0] for favorite in conn.execute(
        f'SELECT location FROM favorite_locations WHERE username = "{username}"').fetchall()]
    return render_template('manage.html', favorites=favorites, username=username)

# u manage jos dodat:
# mogucnost dodavanja lokacije u favorite
# ogranicit broj favorita na 5?


if __name__ == '__main__':
    app.run(debug=True)


BASE = 'http://127.0.0.1:5000/'
