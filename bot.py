from flask import Flask, request
import telepot
import urllib3
import MySQLdb

proxy_url = "http://proxy.server:3128"
telepot.api._pools = {
    'default': urllib3.ProxyManager(proxy_url=proxy_url, num_pools=3, maxsize=10, retries=False, timeout=30),
}
telepot.api._onetime_pool_spec = (urllib3.ProxyManager, dict(proxy_url=proxy_url, num_pools=1, maxsize=1, retries=False, timeout=30))

CONTROL_URL = 'CONTROL_API_URL'
secret = "SECRET"
bot = telepot.Bot('SECRET_API_KEY')
bot.setWebhook("WEBHOOK_URL".format(secret), max_connections=100)
app = Flask(__name__)

def get_chat_id(data):
	chat_id = data['message']['chat']['id']
	return chat_id

def get_message(data):
    message_text = data['message']['text']
    return message_text

def get_control_pic_url(message):
    control_pic_url = CONTROL_URL.format(message)
    return control_pic_url

def send_message(data, message):
    chat_id = get_chat_id(data)
    response = bot.sendMessage(chat_id, message)
    return response

def send_control_pic(data, message):
    chat_id = get_chat_id(data)
    url_pic = get_control_pic_url(message)
    response = bot.sendPhoto(chat_id, url_pic)
    return response

def find_name_lastname(data, name, lastname):
    db = MySQLdb.connect(host="HOST",
        user="USER",
        passwd="PASSWD",
        db="DB")

    cur = db.cursor()
    query = "SELECT * FROM students WHERE lastname = '{}' AND name = '{}'".format(lastname, name)
    cur.execute(query)

    found_list = []

    for row in cur.fetchall():
        found_list.append(row)

    db.close()

    return fetch_data(data, found_list)

def fetch_data(data, found):
    if not found:
        send_message(data, "No se encuentra a est@ joven en nuestros registros.")
        return "Failure"
    else:
        if len(found) == 1:
            row = found[0]
            send_message(data, row[5] + "\n" + row[2] + " " + row[3] + " " + row[0] + " " + row[1] + "\n" + row[4])
            send_control_pic(data, row[4][1:])
        else:
            send_message(data, "Estos son los resultados:")
            for row in found:
                send_message(data, row[5] + "\n" + row[2] + " " + row[3] + " " + row[0] + " " + row[1] + "\n" + row[4])
    return "Success"

def find_dni(data, dni):
	response = send_control_pic(data, dni)
	print (response)

def command_handler(data):
	line = data['message']['text']
	tokens = line.split(" ")

	if '/start' in tokens:
		send_message(data, "Hola bienvenido!")
	elif '/ayuda' in tokens:
		send_message(data, "En Contruccion")
	elif '/buscar_nombre_apellido' in tokens or '/buscar_nombre_apellido@ControlPicBot' in tokens:
		if len(tokens) < 3 or len(tokens) > 3:
			send_message(data, "Recuerda que para buscar por nombre y apellido, debes ingresar el nombre y el apellido")
			return False
		status = find_name_lastname(data, tokens[1], tokens[2])
	elif '/buscar_cedula' in tokens or '/buscar_cedula@ControlPicBot' in tokens:
		if len(tokens) < 2 or len(tokens) > 2:
			send_message(data, "Escriba /buscar_cedula seguido de un numero de cedula, joven")
			return False
		find_dni(data, tokens[1])
	else:
	    print("Por favor intenta usar alguno de nuestros comandos")
	    #send_message(data, "Por favor intenta usar alguno de nuestros comandos")

@app.route('/{}'.format(secret), methods=["POST"])
def telegram_webhook():
    data = request.get_json()

    command_handler(data)
    return "OK"
