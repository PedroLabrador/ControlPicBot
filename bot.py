# -*- coding: utf-8 -*-
'''
Author: Pedro Labrador @SrPedro at Telegram
'''
from flask import Flask, request
import telepot
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


    def get_message(self, data):
        message_text = data['message']['text']
        return message_text


    def get_control_pic_url(self, message):
        control_pic_url = self.CONTROL_URL.format(message)
        return control_pic_url


    def send_message(self, data, message):
        chat_id = self.get_chat_id(data)
        response = self.bot.sendMessage(chat_id, message)
        return response


    def send_control_pic(self, data, message):
        chat_id = self.get_chat_id(data)
        url_pic = self.get_control_pic_url(message)
        response = self.bot.sendPhoto(chat_id, url_pic)
        return response


    def find_name_lastname(self, data, name, lastname):
        db = MySQLdb.connect(host="HOST", user="USER", passwd="PASSWD", db="DB")
        cursor = db.cursor()
        query = "SELECT * FROM users WHERE lastname = '{}' AND name = '{}'".format(lastname, name)
        cursor.execute(query)

        found_list = []

        for row in cursor.fetchall():
            found_list.append(row)
            print(row)

        db.close()

        return self.fetch_data(data, found_list)


    def fetch_data(self, data, found):
        if not found:
            self.send_message(data, "No se encuentra a est@ joven en nuestros registros.")
            return "Failure"
        else:
            if len(found) == 1:
                row = found[0]
                self.send_message(data, row[5] + "\n" + row[2] + " " + row[3] + " " + row[0] + " " + row[1] + "\n" + row[4])
                self.send_control_pic(data, row[4][1:])
            else:
                self.send_message(data, "Estos son los resultados:")
                for row in found:
                    self.send_message(data, row[5] + "\n" + row[2] + " " + row[3] + " " + row[0] + " " + row[1] + "\n" + row[4])
        return "Success"


    def find_id(self, data, id):
        try:
            response = self.send_control_pic(data, id)
        except Exception as e:
            self.send_message(data, "No se encuentra a est@ joven :(")
        return response


    def command_start(self, data, tokens):
        return self.send_message(data, "Hola bienvenid@!")


    def command_help(self, data, tokens):
        return self.send_message(data, "En Contruccion")


    def command_buscar_nombre_apellido(self, data, tokens):
        if len(tokens) < 3 or len(tokens) > 3:
            self.send_message(data, "Recuerda que para buscar por nombre y apellido, debes ingresar el nombre y el apellido")
            return "Failure"
        return self.find_name_lastname(data, tokens[1], tokens[2])


    def command_buscar_cedula(self, data, tokens):
        if len(tokens) < 2 or len(tokens) > 2:
            self.send_message(data, "Escriba /buscar_cedula seguido de un numero de cedula, joven")
            return "Failure"
        return self.find_id(data, tokens[1])


    def command_handler(self):
        data = request.json

        commands = {
            '/start': self.command_start,
            '/help': self.command_help,
            '/buscar_nombre_apellido': self.command_buscar_nombre_apellido,
            '/buscar_nombre_apellido@ControlPicBot': self.command_buscar_nombre_apellido,
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
                        status = handler(data, tokens)
                        print (status)

        return "OK"


app = controlpicbot(__name__)
