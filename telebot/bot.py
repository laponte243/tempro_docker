from requests.exceptions import Timeout
from constantes import *
from telebot import *
import matplotlib.pyplot as plt
import matplotlib.dates as md
import pandas as pd
import numpy as np
import datetime
import requests
import time

bot = telebot.TeleBot(API_KEY_BOT)

user_dc = {}
class User:
    def __init__(self, mail):
        self.mail_us = mail
        self.pssw_us = None
        self.chat_id = None

@bot.message_handler(commands=['start'])
def inicio(msg):
    chat_id = msg.chat.id
    try:
        data = {'chat_id':chat_id,'cambiar_alertar':False}
        url=BASE_URL_TEMPRO+'suscribir-usuario/'
        request = requests.post(url, data=data)
        if request.status_code==200:
            markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
            markup.add('/temperaturas','/alertar')
            msg = bot.send_message(chat_id, '¿Que quieres hacer?', reply_markup=markup)
        else:
            bot.reply_to(msg, "Este es el bot de asociado a Medical Administrador")
            bot.send_message(chat_id, "Primero inicie sesion para comenzar")
            bot.send_message(chat_id, "Inserte el correo del usuario")
            bot.register_next_step_handler(msg, correo_usuario)
    except Exception as e:
        print(e)
        bot.send_message(chat_id, "Ha habido un error")

@bot.message_handler(commands=['help'])
def ayuda(msg):
    with open("start_text.txt", "r") as file_txt:
        start_text = file_txt.read()
        splitted_text = util.split_string(start_text, 3000)
        for text in splitted_text:
            bot.reply_to(msg, text)

def correo_usuario(msg):
    chat_id = msg.chat.id
    try:
        mail = msg.text
        user = User(mail)
        user_dc[chat_id] = user
        bot.send_message(chat_id, "Inserte la clave/contraseña del usuario")
        bot.register_next_step_handler(msg, clave_usuario)
    except Exception as e:
        bot.send_message(chat_id, e)

def clave_usuario(msg):
    chat_id = msg.chat.id
    try:
        pssw_us = msg.text
        url=BASE_URL_APP+'api-token-auth/'
        data={'username':user_dc[chat_id].mail_us,'password':pssw_us,'chat_id':chat_id}
        request = requests.post(url,data)
        if request.status_code==200:
            bot.send_message(chat_id, "Acceso exitoso.\nEl chat ha sido registrado")
            markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
            markup.add('/temperaturas','/alertar')
            msg = bot.send_message(chat_id, '¿Que quieres hacer?', reply_markup=markup)
        else:
            raise Exception("Usuario o contraseña equivocado")
    except Exception as e:
        bot.send_message(chat_id, e)
        bot.send_message(chat_id, "Inserte el correo del usuario")
        bot.register_next_step_handler(msg, correo_usuario)
    

@bot.message_handler(commands=['temperaturas'])
def temperatura(msg):
    chat_id = msg.chat.id
    try:
        advertencia = bot.send_message(chat_id, 'Espere mientras obtenemos las temperaturas...')
        data = {'todos':True, 'chat':chat_id}
        url=BASE_URL_TEMPRO+'obtener-grafica/'
        promedios = requests.post(url, timeout=100, data=data)
        if promedios.status_code==404:
            bot.send_message(chat_id, 'Este chat no esta registrado en el sistema\nPor favor ingrese el correo')
            bot.register_next_step_handler(msg, correo_usuario)
        else:
            temp = []
            hora = []
            df = None
            for promedio in promedios.json():
                for p in promedio['grafica']:
                    hora.append(datetime.datetime.fromtimestamp(int(p['fecha_hora'])))
                    temp.append(p['promedio'])
                df = pd.DataFrame({'date_time':hora,'temperatura':temp})
                df['date_time'] = pd.to_datetime(df['date_time'], format='%Y-%m-%d %H:%M:%S')
                fig, ax = plt.subplots(figsize=(8,6))
                plt.plot('date_time', 'temperatura', data=df)
                ax.set_xlim(df['date_time'].min()-pd.Timedelta(1,'h'),df['date_time'].max()+pd.Timedelta(1,'h'))
                ax.xaxis.set_major_locator(md.HourLocator(interval=1))
                ax.xaxis.set_major_formatter(md.DateFormatter('%H:%M:%S'))
                fig.autofmt_xdate()
                constante = [hora[0], hora[-1]]
                if promedio['min'] != None:
                    temp_min = [promedio['min'],promedio['min']]
                    plt.plot(constante,temp_min)
                if promedio['max'] != None:
                    temp_max = [promedio['max'],promedio['max']]
                    plt.plot(constante,temp_max)
                plt.grid(True)
                plt.ylabel('Temperatura')
                plt.xlabel('Hora')
                plt.title('%s'%(promedio['nombre']))
                plt.savefig('graficatemp.png')
                grafico = open('graficatemp.png', 'rb')
                ultima_hora = datetime.datetime.strptime(promedio['ultima_hora'], "%Y-%m-%dT%H:%M:%S.%fZ")-datetime.timedelta(hours=4)
                if ultima_hora.minute < 10:
                    minuto = '0%s'%(ultima_hora.minute)
                else:
                    minuto = ultima_hora.minute
                bot.send_message(chat_id, 'Ultima temperatura registrada: %sºc a las %s:%s (%s)'%(round(promedio['ultima_temp'],2),ultima_hora.hour,minuto,promedio['nombre']))
                bot.send_photo(chat_id, grafico)
                temp = []
                hora = []
                df = None
    except Timeout as e:
        bot.send_message(chat_id, 'No se pudo establecer una conexion al servidor las graficas')
    except Exception as e:
        print(e)
        bot.send_message(chat_id, "Hubo un error")
    bot.last_message_sent = chat_id, advertencia.message_id
    bot.delete_message(*bot.last_message_sent)

@bot.message_handler(commands=['alertar'])
def alertas(msg):
    chat_id = msg.chat.id
    try:
        data = {'chat_id':chat_id,'cambiar_alertar':True}
        url=BASE_URL_TEMPRO+'suscribir-usuario/'
        request = requests.post(url,data=data).json()
        if request['cambiado_a'] == True:
            bot.send_message(chat_id, 'Desde ahora recibiras mensajes de alerta.')
        if request['cambiado_a'] == False:
            bot.send_message(chat_id, 'Ahora dejarás de recibir mensajes de alerta.')
    except Exception as e:
        print(e, datetime.now())
        bot.send_message(chat_id, 'Ha habido un error')

print("bot starting :)")
bot.polling()