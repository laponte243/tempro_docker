import requests
import paho.mqtt.client as mqtt
broker = "192.168.0.150"
api = 'http://192.168.0.150:85/administrador/tempro/v2/'

def temperatura(mac,serial,temp):
    url=f'{api}cambio-temperatura/'
    data={'mac':mac,'serial':serial,'temperatura':temp}
    respuesta=requests.post(url,data=data, auth=('super','Z33tasp3mo!'))
    return respuesta.text

def puerta(mac,estado):
    url=f'{api}cambio-puerta/'
    data={'mac':mac,'estado':estado}
    respuesta=requests.post(url,data=data, auth=('super','Z33tasp3mo!'))
    return respuesta.text

def error(topic,by_length,receive,mac='N/A',serial_estado='N/A',temp='N/A'):
    url=f'{api}errores/'
    data={'error':'','receive':receive,'mac':'N/A','temperatura':'N/A','topic':'','serial':'N/A','estado':'N/A'}
    if topic=="temperatura":
        data['mac']=mac
        data['serial']=serial_estado
        data['temperatura']=temp
        data['topic']='temperatura'
        if not by_length:
            if type(mac)!=str:
                data['error']=data['error']+'/Direccion Mac erronea'
            if type(serial_estado)!=str:
                data['error']=data['error']+'/Serial erroneo'
            try:
                value = float(temp)
            except:
                data['error']=data['error']+'/Temperatura erronea'
        elif by_length > 3:
            data['error'] = data['error']+'/Sintaxis extra'
        elif by_length < 3:
            data['error'] = data['error']+'/Sintaxis faltante'
        respuesta=requests.post(url,data=data, auth=('super', 'Z33tasp3mo!'))
    if topic=="puerta":
        data['mac']=mac
        data['estado']=serial_estado
        data['topic']='puerta'
        if not by_length:
            if type(mac)!=str:
                data['error']=data['error']+'/Direccion Mac erronea'
            try:
                if int(serial_estado)<2 and int(serial_estado)>=0:
                    data['error']=data['error']+'/Valor del estado incorrecto'
            except:
                data['error']=data['error']+'/Estado erroneo'
        elif by_length > 2:
            data['error'] = data['error']+'/Sintaxis extra'
        elif by_length < 2:
            data['error'] = data['error']+'/Sintaxis faltante'
        respuesta=requests.post(url,data=data, auth=('super', 'Z33tasp3mo!'))
    return respuesta.text
    
# message = temperatura('23456789','654897321',0.0)
# message = puerta('3665498852',1)

def on_message(client,userdata,msg):
    #print("hola")
    receive = str(msg.payload.decode("utf-8"))
    data=receive.split('|')
    if msg.topic=="mensajes/temperatura":
        if len(data)==3:
            mac_nodo=data[0]
            serial_sensor=data[1]
            temp=data[2]
            try:
                tempera=float(temp)
            except:
                tempera=None
            if type(mac_nodo)==str and type(serial_sensor)==str and tempera:
                temperatura(mac_nodo,serial_sensor,temp)
            else:
                error('temperatura',False,receive,mac_nodo,serial_sensor,temp)
        else:
            error('temperatura',len(data),receive)
    if msg.topic=="mensajes/puerta":
        if len(data)==2:
            mac_nodo=data[0]
            estado=data[1]
            try:
                est=int(estado)
                if type(mac_nodo)==str and (est>=0 and est<2):
                    puerta(mac_nodo,est)
                else:
                    raise
            except:
                est=estado
                error('puerta',False,receive,mac_nodo,estado)
        else:
            error('puerta',len(data),receive)

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("mensajes/temperatura")
    client.subscribe("mensajes/puerta")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(broker)
client.loop_forever()