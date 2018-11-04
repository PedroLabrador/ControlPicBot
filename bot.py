# -*- coding: utf-8 -*-
'''
Author: Pedro Labrador @SrPedro at Telegram
'''
from flask import Flask, request
import telepot
from telepot.namedtuple import ForceReply
import urllib3
import MySQLdb

class controlpicbot(Flask):
    proxy_url = "http://proxy.server:3128"
    CONTROL_URL = 'CONTROL_API_URL'
    secret = "SECRET"
    API_KEY = "SECRET_API_KEY"
    WEBHOOK_URL = "WEBHOOK_URL/{}".format(secret)

    def __init__(self, name):
        super(controlpicbot, self).__init__(name)
        telepot.api._pools = {'default': urllib3.ProxyManager(proxy_url=self.proxy_url, num_pools=3, maxsize=10, retries=False, timeout=30),}
        telepot.api._onetime_pool_spec = (urllib3.ProxyManager, dict(proxy_url=self.proxy_url, num_pools=1, maxsize=1, retries=False, timeout=30))

        self.add_url_rule('/{}'.format(self.secret), view_func=self.command_handler, methods=["POST"])

        self.bot = telepot.Bot(self.API_KEY)
        self.bot.setWebhook(self.WEBHOOK_URL, max_connections=100)


    def get_chat_id(self, data):
        chat_id = data['message']['chat']['id']
        return chat_id


    def get_user_id(self, data):
        user_id = data['message']['from']['id']
        return user_id


    def get_user_firstname(self, data):
        user_firstname = data['message']['from']['first_name']
        return user_firstname


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

        if reply_type == 'ForceReply':
            markup = ForceReply(selective=True)
            response = self.bot.sendMessage(chat_id, message + ', ' + mention, parse_mode='HTML', reply_markup=markup)
            return response
        response = self.bot.sendMessage(chat_id, message)
        return response


    def send_control_pic(self, data, id, old_pic=False):
        chat_id = self.get_chat_id(data)
        url_pic = self.get_control_pic_url(id, old_pic)
        try:
            response = self.bot.sendPhoto(chat_id, url_pic)
            return response
        except telepot.exception.TelegramError as b:
            self.bot.sendMessage(chat_id, "No se encuentra esta cedula almacenada")
        return "Ok"


    def database_connection(self):
        db = MySQLdb.connect(host="HOST", user="USER", passwd="PASSWD", db="DB")
        return db


    def find_name_lastname(self, data, name, lastname):
        db = self.database_connection()
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
        db = self.database_connection()
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
            return "Not OK"
        else:
            if len(found) == 1:
                row = found[0]
                self.send_message(data, str(row[5]) + "\n" + str(row[2]) + " " + str(row[3]) + " " + str(row[0]) + " " + str(row[1]) + "\n" + str(row[4]))
                self.send_control_pic(data, str(row[4])[1:], old_pic)
            else:
                self.send_message(data, "Estos son los resultados:")
                for row in found:
                    self.send_message(data, str(row[5]) + "\n" + str(row[2]) + " " + str(row[3]) + " " + str(row[0]) + " " + str(row[1]) + "\n" + str(row[4]))
        return "OK"


    def find_id(self, data, id):
        old_pic = False
        if id.startswith('-'):
            old_pic = True
            id = id[1:]

        db = self.database_connection()
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
        try:
            if 'reply_to_message' in data['message']:
                line = data['message']['reply_to_message']['text'][:1]
                tokens = data['message']['text']

                if line == '*':
                    self.find_id(data, tokens[0])
                if line == '+':
                    self.find_name_lastname(data, tokens[0], tokens[1])
                if line == '-':
                    self.find_name_career(data, tokens[0], tokens[1])
                return True  #Message replied
            else:
                return False #No message to reply
        except KeyError as k:
            print(k)
            return False

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


app = controlpicbot(__name__)
