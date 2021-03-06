# -*- coding: utf-8 -*-
'''
Author: Pedro Labrador @SrPedro at Telegram
'''

import telepot, time, urllib3, MySQLdb, scrap
from flask import Flask, request, render_template, flash, redirect, url_for, session
from passlib.hash import sha256_crypt
from functools import wraps
from telepot.namedtuple import ForceReply

def database_connection(self):
    db = MySQLdb.connect(host="HOST", user="USER", passwd="PASSWD", db="DB")
    return db

class controlpicbot(Flask):
    proxy_url = "http://proxy.server:3128"
    CONTROL_URL = 'CONTROL_API_URL'
    secret = "SECRET"
    API_KEY = "SECRET_API_KEY"
    WEBHOOK_URL = "WEBHOOK_URL/{}".format(secret)

    def __init__(self, name, template_folder):
        super(controlpicbot, self).__init__(name, template_folder=template_folder)
        telepot.api._pools = {'default': urllib3.ProxyManager(proxy_url=self.proxy_url, num_pools=3, maxsize=10, retries=False, timeout=30),}
        telepot.api._onetime_pool_spec = (urllib3.ProxyManager, dict(proxy_url=self.proxy_url, num_pools=1, maxsize=1, retries=False, timeout=30))

        self.add_url_rule('/{}'.format(self.secret), view_func=self.command_handler, methods=["POST"])

        self.bot = telepot.Bot(self.API_KEY)
        self.bot.setWebhook(self.WEBHOOK_URL, max_connections=100)
        self.secret_key = self.secret


    def get_chat_id(self, data):
        chat_id = data['message']['chat']['id']
        return chat_id


    def get_user_id(self, data):
        user_id = data['message']['from']['id']
        return user_id


    def get_user_firstname(self, data):
        user_firstname = data['message']['from']['first_name']
        return user_firstname


    def get_username(self, data):
        username = data['message']['from']['username'] if 'username' in data['message']['from'] else "No username"
        return username


    def get_chat_type(self, data):
        chat_type = data['message']['chat']['type']
        return chat_type


    def get_chat_title(self, data):
        chat_title = data['message']['chat']['title'] if 'title' in data['message']['chat'] else 'No title'
        return chat_title


    def get_message(self, data):
        message_text = data['message']['text']
        return message_text


    def get_control_pic_url(self, id, old_pic):
        if not old_pic:
            control_pic_url = self.CONTROL_URL.format("00" + id)
        else:
            control_pic_url = self.CONTROL_URL.format(id)
        return control_pic_url


    def send_message(self, data, message, reply_type = ''):
        chat_id = self.get_chat_id(data)
        user_id = self.get_user_id(data)
        user_firstname = self.get_user_firstname(data)

        mention = "<a href='tg://user?id={}'>{}</a>".format(user_id, user_firstname)
        
        self.bot.sendChatAction(chat_id, 'typing')

        if reply_type == 'ForceReply':
            markup = ForceReply(selective=True)
            response = self.bot.sendMessage(chat_id, message + ', ' + mention, parse_mode='HTML', reply_markup=markup)
            time.sleep(0.5)
            return response

        response = self.bot.sendMessage(chat_id, message)
        time.sleep(0.5)
        return response


    def send_control_pic(self, data, id, old_pic=False):
        chat_id = self.get_chat_id(data)
        url_pic = self.get_control_pic_url(id, old_pic)
        try:
            self.bot.sendChatAction(chat_id, 'upload_photo')
            response = self.bot.sendPhoto(chat_id, url_pic)
            time.sleep(0.5)
            return response
        except telepot.exception.TelegramError as b:
            self.bot.sendChatAction(chat_id, 'typing')
            self.bot.sendMessage(chat_id, "No se encuentra esta cedula almacenada")
            time.sleep(0.5)
        return "Ok"


    def find_name_lastname(self, data, name, lastname):
        msg = name + " " + lastname
        self.db_user_check(data, msg)
        db = database_connection()
        cursor = db.cursor()
        query = "SELECT * FROM users WHERE lastname = '{}' AND name = '{}'".format(lastname, name)
        cursor.execute(query)

        found_list = []

        for row in cursor.fetchall():
            found_list.append(row)
            print(row)

        db.close()

        return self.fetch_data(data, found_list)


    def find_name_career(self, data, name, career):
        msg = name + " " + career
        self.db_user_check(data, msg)
        banlist = ['maria', 'luis', 'daniela', 'jose', 'juan', 'david', 'alejandro', 'jesus', 'andrea']
        if name.lower() in banlist:
            return self.send_message(data, "Para evitar el envio masivo de mensajes, el nombre que intenta buscar ha sido prohibido :(\nIntente usar la opcion /buscar_nombre_apellido joven")
        db = database_connection()
        cursor = db.cursor()
        query = "SELECT * FROM users WHERE career = '{}' AND name = '{}'".format(career, name)
        cursor.execute(query)

        found_list = []

        for row in cursor.fetchall():
            found_list.append(row)

        db.close()

        return self.fetch_data(data, found_list)


    def fetch_data(self, data, found, old_pic=False):
        if not found:
            self.send_message(data, "No se encuentra a est@ joven en nuestros registros.")
            return "Failure"
        else:
            if len(found) > 1:
                self.send_message(data, "Estos son los resultados:")

            for current in found:
                row = [str(a).replace('None', '') for a in current]
                titles, user_data = scrap.get_cne_data('VE', row[4][1:])
                msg = row[5] + "\n" + row[2] + " " + row[3] + " " + row[0] + " " + row[1] + "\n" + row[4]

                if len(titles) > 0 and len(data) > 0:
                    state        = user_data[titles.index('Estado')]
                    municipality = user_data[titles.index('Municipio')]
                    msg += "\nEstado: " + state + "\nMunicipio: " + municipality

                self.send_message(data, msg)

                if len(found) == 1:
                    self.send_control_pic(data, row[4][1:], old_pic)

        return "Success"


    def find_id(self, data, id):
        self.db_user_check(data, id)
        old_pic = False
        if id.startswith('-'):
            old_pic = True
            id = id[1:]

        db = database_connection()
        cursor = db.cursor()
        query = "SELECT * FROM users WHERE id = 'V{}'".format(id)
        cursor.execute(query)
        found_list = []

        for row in cursor.fetchall():
            found_list.append(row)

        db.close()

        if not found_list:
            return self.send_control_pic(data, id, old_pic)
        else:
            return self.fetch_data(data, found_list, old_pic)
            

    def command_start(self, data, tokens):
        return self.send_message(data, "Hola bienvenid@!")


    def command_help(self, data, tokens):
        return self.send_message(data, "En Contruccion")


    def command_buscar_nombre_apellido(self, data, tokens):
        if len(tokens) < 3 or len(tokens) > 3:
            self.send_message(data, "+ Escriba el primer nombre y el primer apellido separados con un espacio", 'ForceReply')
            return "Not enough tokens"
        return self.find_name_lastname(data, tokens[1], tokens[2])


    def command_buscar_nombre_carrera(self, data, tokens):
        if len(tokens) < 3 or len(tokens) > 3:
            self.send_message(data, "- Escriba el primer nombre y la carrera separados con un espacio\nEjemplo: Luis Civil", 'ForceReply')
            return "Not enough tokens"
        return self.find_name_career(data, tokens[1], tokens[2])


    def command_buscar_cedula(self, data, tokens):
        if len(tokens) < 2 or len(tokens) > 2:
            self.send_message(data, "* Escriba el número de cédula que desea buscar", 'ForceReply')
            return "Not enough tokens"
        return self.find_id(data, tokens[1])


    def check_replies(self, data):
        if 'reply_to_message' in data['message']:
            try:
                operator = data['message']['reply_to_message']['text'][:1]
                tokens = data['message']['text'].split(" ")
            except Exception as e:
                print("An error has ocurred, maybe it's an emoji error")
                return False

            if operator in ('*', '+', '-'):
                if operator == '*':
                    if len(tokens) is 1:
                        self.find_id(data, tokens[0])
                    else:
                        self.send_message(data, "* Escriba el número de cédula que desea buscar", 'ForceReply')
                elif operator == '+':
                    if len(tokens) is 2:
                        self.find_name_lastname(data, tokens[0], tokens[1])
                    else:
                        self.send_message(data, "+ Escriba el primer nombre y el primer apellido separados con un espacio", 'ForceReply')
                elif operator == '-':
                    if len(tokens) is 2:
                        self.find_name_career(data, tokens[0], tokens[1])
                    else:
                        self.send_message(data, "- Escriba el primer nombre y la carrera separados con un espacio\nEjemplo: Luis Civil", 'ForceReply')
            else:
                return False

            return True  #Message replied
        else:
            return False #No message to reply


    def db_user_check(self, data, msg):
        db = database_connection()
        cursor = db.cursor()

        user_id = self.get_user_id(data)
        username = self.get_username(data)
        first_name = self.get_user_firstname(data)
        chat_id = self.get_chat_id(data)
        chat_type = self.get_chat_type(data)
        chat_title = self.get_chat_title(data)
        text = msg

        query = "SELECT * FROM registers WHERE telegram_user_id = '{}' LIMIT 1".format(user_id)
        result = cursor.execute(query)

        if not result > 0:
            query = "INSERT INTO registers (telegram_user_id, username, first_name) VALUES ('{}', '{}', '{}')".format(user_id, username, first_name)
            cursor.execute(query)
            db.commit()
            query = "SELECT * FROM registers WHERE telegram_user_id = '{}' LIMIT 1".format(user_id)
            cursor.execute(query)

        row = cursor.fetchone()
        register_id = row[0]
        try:
            query = "INSERT INTO history (register_id, chat_id, chat_title, chat_type, text) VALUes ('{}', '{}', '{}', '{}', '{}')".format(register_id, chat_id, chat_title, chat_type, text)
            cursor.execute(query)
            db.commit()
        except Exception as e:
            db.rollback()
            print("An error has ocurred :(")
            return "Error"

        db.close()

        return "OK"


    def command_handler(self):
        data = request.json

        if self.check_replies(data):
            return "OK"

        commands = {
            '/start': self.command_start,
            '/help': self.command_help,
            '/buscar_nombre_apellido': self.command_buscar_nombre_apellido,
            '/buscar_nombre_apellido@ControlPicBot': self.command_buscar_nombre_apellido,
            '/buscar_nombre_carrera': self.buscar_nombre_carrera,
            '/buscar_nombre_carrera@ControlPicBot': self.buscar_nombre_carrera,
            '/buscar_cedula': self.command_buscar_cedula,
            '/buscar_cedula@ControlPicBot': self.command_buscar_cedula
        }

        if 'entities' in data['message']:
            line = data['message']['text']
            tokens = line.split(" ")
            for i in data['message']['entities']:
                if 'bot_command' in i['type']:
                    handler = commands.get(tokens[0], None);
                    if self.handler:
                        handler(data, tokens)

        return "OK"


app = controlpicbot(__name__, template_folder='folder')


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("Unathorized, please log in", 'danger')
            return redirect(url_for('login'))
    return wrap


@app.route('/', methods=['GET'])
def index():
    return "Hola"


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']

        db = database_connection()
        cursor = db.cursor()
        query = "SELECT * FROM users WHERE username='{}' LIMIT 1".format(username)
        result = cursor.execute(query)

        if result > 0:
            data = cursor.fetchone()
            cursor.close()
            password = data[4]

            if sha256_crypt.verify(password_candidate, password):
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                return render_template("login.html", error="Username or Password incorrect")
        else:
            cursor.close()
            return render_template("login.html", error="Username or Password incorrect")
    return render_template("login.html")


@app.route('/dashboard')
@is_logged_in
def dashboard():
    db = database_connection()
    cursor = db.cursor()
    query = """SELECT r.id, r.telegram_user_id, r.username, r.first_name, h.date
            FROM history h
            JOIN (SELECT h.register_id rid, MAX(h.date) rdate
                  FROM history h
                  GROUP BY h.register_id) o ON h.register_id = o.rid AND h.date = o.rdate
            JOIN registers r
            ON h.register_id = r.id
            ORDER BY h.date DESC"""
    cursor.execute(query)
    data = cursor.fetchall()
    db.close()

    return render_template('dashboard.html', registers=data)


@app.route('/registers/<string:user_id>')
@is_logged_in
def user_registers(user_id):
    db = database_connection()
    cursor = db.cursor()
    query = """SELECT h.id, r.username, r.first_name, h.chat_id, h.chat_type, h.chat_title, h.text, h.date
                FROM history h
                JOIN registers r on h.register_id = r.id
                WHERE r.telegram_user_id = '{}'""".format(user_id)
    result = cursor.execute(query)
    data = cursor.fetchall()
    db.close()
    if result > 0:
        return render_template('registers.html', registers=data, user_id=user_id)
    else:
        return redirect(url_for('dashboard'))


@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash("You are now logged out", 'success')
    return redirect(url_for('login'))
