from flask import Flask, request , Response # Импортируем request из flask
import requests as rq
import subprocess
import coordinates_pb2 as c_pb2 # импорт сообщения - поправки координат
import  satellites_pb2 as s_pb2 # импорт сообщения - списка используемых спутников
from urllib.parse import urljoin

lst_salellites = [] # список спутников используемых потребителем

lst_ip_bs = ['127.0.0.2'] # список ip базовых станций

X_user = None
Y_user = None
Z_user = None

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'



@app.route('/correction', methods=['GET','POST'])
def correction():
    if  request.method == 'GET':

        for ip in lst_ip_bs:
            baseurl = 'http://' + str(ip) + ':5000'
            path = '/correct/X_user/Y_user/Z_user'
            URL = urljoin(baseurl, path)
            response = rq.get(URL)
            print(response.status_code)
        return  response.status_code
    
    if request.method == 'POST':
        binary_data = request.data
        coords = c_pb2.Coordinates()
        coords.ParseFromString(binary_data)
        global X_user, Y_user, Z_user
        
        return Response(b"OK", status=200, mimetype='text/plain')


@app.route('/satellites', methods=['GET','POST'])
def get_satellites():
# передается список номеров спутников от потребителя
    if request.method == 'POST':

        binary_data = request.data
        global lst_salellites
        satellites = s_pb2.SatelliteList()
        satellites.ParseFromString(binary_data)
        lst_salellites = list(satellites.names) 

        return Response(b"OK", status=200, mimetype='text/plain')

    
if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)