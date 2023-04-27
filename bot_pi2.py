#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import time
import speedtest
import logging
from socket import timeout

import telebot
from telebot import types
import telegram
from telegram import ReplyKeyboardMarkup

# Constantes
TOKEN = 'mytoken'
COMMANDS = {
    'ayuda': 'Da información sobre los comandos disponibles',
    'temp': 'Comprueba la temperatura de la raspberry',
    'reboot': 'Reinicia el servidor',
    'ipp' : 'Te informa de la IP Pública',
    'speedtest': 'Te da la velocidad de conexión a internet de la Raspberry',
    'actualiza': 'Actualiza la raspberry'
}
DEFAULT_MESSAGE = "Lo siento, no entiendo lo que quieres decir. Prueba con /ayuda para obtener más información."

# Variables
known_users = []  
user_step = {}

# Inicialización del bot y log
bot = telebot.TeleBot(TOKEN)
logger = telebot.logger
telebot.logger.setLevel(logging.INFO)
keyboard = types.ReplyKeyboardMarkup(row_width=2)
keyboard.add(*[types.KeyboardButton(command) for command in COMMANDS.keys()])

# Funciones

def send_message(chat_id, text):
    """Envía un mensaje al chat especificado."""
    try:
        bot.send_message(chat_id=chat_id, text=text)
    except telebot.apihelper.ApiException as e:
        logger.error(f"Error al enviar mensaje a chat {chat_id}: {e}")

def listener(messages):
    for m in messages:
        if m.content_type == 'text':
            text = m.text
            logger.info(f"Mensaje recibido: {text}")
            full_text = m.text  # Guardar el texto completo del mensaje (con la barra)
            if m.text == "Hola":
                command_text_hi(m)
            elif m.text.startswith('/'):
                commands_dict = {
                    '/ayuda': command_help,
                    '/temp': command_temp,
                    '/reboot': command_reboot,
                    '/ipp': command_ipp,
                    '/speedtest': command_speedtest,
                    '/actualiza': command_actualiza,
                    '/start': command_start
                }
                commands_dict[text](m)  # Llamar a la función correspondiente
            else:
                print(f"Texto no reconocido: {text}")
                command_default(m)

# Command start with menu
def command_start(m):
    """Maneja el comando /start y muestra el menú."""
    print("command_start() called")
    cid = m.chat.id
    print(f"cid={cid}")
    if cid not in known_users:
        known_users.append(cid)
        user_step[cid] = 0
    bot.send_message(cid, "Hola! ¿Qué quieres hacer?", reply_markup=keyboard)

updates = bot.get_updates()

if updates:
    for update in updates:
        message = update.message
        chat_id = message.chat.id
        text = message.text

        # El código restante para responder al mensaje del usuario
else:
    print("No hay actualizaciones disponibles")

@bot.message_handler(commands=['hola'])
def command_hola(m):
    """Saluda al usuario."""
    cid = m.chat.id
    send_message(cid, "Hola! ¿Cómo estás?")

@bot.message_handler(func=lambda message: True)

def get_user_step(uid):
    """Obtiene el estado actual del usuario."""
    if uid in user_step:
        return user_step[uid]
    else:
        known_users.append(uid)
        user_step[uid] = 0
        logger.info("Nuevo usuario detectado, quien no ha usado /start aún")
        return 0

# Help page
def command_help(m):
    """Muestra información sobre los comandos disponibles."""
    cid = m.chat.id
    help_text = "Estos son los comandos disponibles: \n"
    for key in COMMANDS:
        help_text += "/" + key + ": "
        help_text += COMMANDS[key] + "\n"
    send_message(cid, help_text)

# Reinicia servidor
def command_reboot(m):
    cid = m.chat.id
    try:
        bot.send_message(cid, "Voy a reiniciar el servidor...")
        bot.send_chat_action(cid, 'typing')
        time.sleep(3)
        bot.send_message(cid, ".")
        os.system("sudo shutdown -r now")
        bot.send_message(cid, "El servidor se ha reiniciado con éxito.")
    except:
        bot.send_message(cid, "Ha ocurrido un error al reiniciar el servidor.")

# Mira temperaturas
def command_temp(m):
    """Muestra la temperatura de la Raspberry Pi."""
    cid = m.chat.id
    send_message(cid, "Vamos a comprobar si has puesto caliente a tu equipo...")
    bot.send_chat_action(cid, 'typing')  # show the bot "typing" (max. 5 secs)
    time.sleep(2)
    try:
        f = os.popen("temperaturas")
        result = f.read()
        send_message(cid, result)
    except Exception as e:
        logger.error(f"Error al obtener la temperatura: {e}")
        send_message(cid, "Lo siento, no pude obtener la temperatura en este momento.")

# Actualiza la raspberry
def command_actualiza(m):
    cid = m.chat.id
    try:
        bot.send_message(cid, "Comprobando actualizaciones...")
        bot.send_chat_action(cid, 'typing')
        time.sleep(1)
        f = os.popen("bash /home/pi/actualizar.sh")
        result = f.read()
        if result == "":
            bot.send_message(cid, "No hay actualizaciones disponibles.")
        else:
            bot.send_message(cid, "Las siguientes actualizaciones se han instalado:\n" + result)
    except:
        bot.send_message(cid, "Ha ocurrido un error al actualizar la Raspberry.")

# Comprueba la ip pública
def command_ipp(m):
    cid = m.chat.id
    try:
        bot.send_message(cid, "Obteniendo la dirección IP pública...")
        bot.send_chat_action(cid, "typing")
        time.sleep(2)
        f = os.popen("curl icanhazip.com")
        result = f.read()
        if result == "":
            bot.send_message(cid, "No se pudo obtener la dirección IP pública. Por favor, inténtalo de nuevo más tarde.")
        else:
            bot.send_message(cid, "La dirección IP pública es: " + result)
    except:
        bot.send_message(cid, "Ha ocurrido un error al obtener la dirección IP pública. Por favor, inténtalo de nuevo más tarde.")

# Comprueba la velocidad de conexión
def command_speedtest(m):
    cid = m.chat.id
    try:
        bot.send_message(cid, "Realizando prueba de velocidad de Internet...")
        bot.send_chat_action(cid, "typing")
        time.sleep(2)
        st = speedtest.Speedtest()
        st.get_best_server()
        download_speed = st.download()
        upload_speed = st.upload()
        download_speed_mbps = round(download_speed / 1000000, 2)
        upload_speed_mbps = round(upload_speed / 1000000, 2)
        bot.send_message(cid, f"Velocidad de descarga: {download_speed_mbps} Mbps\nVelocidad de carga: {upload_speed_mbps} Mbps")
    except Exception as e:
        error_message = f"Ha ocurrido un error al realizar la prueba de velocidad de Internet: {e}"
        print(error_message)
        bot.send_message(cid, error_message)

def command_text_hi(m):
    """Responde al saludo 'Hola'."""
    send_message(m.chat.id, "Muy buenas")

def command_default(message):
    send_message(message.chat.id, DEFAULT_MESSAGE)

def main():
    print("BOT UP") 
 
    bot.set_update_listener(listener)

    try:
        bot.polling(none_stop = True, interval = 0, timeout = 30)
        while 1:
            time.sleep(3)
    except Exception as e:
        print("Telegram API timeout ...") 
        print(e)
        logger.critical(e)
        bot.stop_polling()
        time.sleep(30)
        print("Reboot") 
        main()

if __name__ == '__main__':
    main()
