from flask import Flask, request , Response # Импортируем request из flask
import requests as rq
import subprocess
import coordinates_pb2 as c_pb2 # импорт сообщения - поправки координат
import  satellites_pb2 as s_pb2 # импорт сообщения - списка используемых спутников
from urllib.parse import urljoin
import math

lst_salellites = [] # список спутников используемых потребителем

lst_ip_bs = [
        { 'station': 1,
            'port':5001,
            'x': 2850631.2464619204 ,
            'y': 2195281.5913748345 ,
            'z': 5248946.485037155
        },
        
        { 'station': 2,
            'port':5002,
            'x': 2873213.842526767 ,
            'y': 2180888.0077110133 ,
            'z': 5242672.249382722
                }
            ] # список ip базовых станций для теста - порты

X_user = None
Y_user = None
Z_user = None

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'



@app.route('/correction', methods=['GET','POST'])
def correction():
    global X_user, Y_user, Z_user
    # if  request.method == 'GET':

    #     for ip in lst_ip_bs:
    #         baseurl = 'http://' + str(ip) + ':5001'
    #         x, y, z = X_user or 0, Y_user or 0, Z_user or 0
    #         path = f'/correct/{x}/{y}/{z}'
    #         URL = urljoin(baseurl, path)
    #         response = rq.get(URL)
    #         print(response.status_code)
    #     return Response(response.content, status=response.status_code,
    #                     content_type=response.headers.get('Content-Type', 'text/plain'))
    
    if request.method == 'POST':
        binary_data = request.data
        coords = c_pb2.Coordinates()
        coords.ParseFromString(binary_data)
        X_user = coords.x
        Y_user = coords.y
        Z_user = coords.z
        #  код рабочий
        # URL = 'http://127.0.0.1:5001/correct'

        # response = rq.post(
        #     URL,
        #     data = binary_data,
        #     headers={
        #             "Content-Type": "application/x-protobuf",
        #             "Accept": "application/x-protobuf",
        #     },
        # )
        # print("Статус-код:", response.status_code)
        # print(f'x={X_user} y={Y_user} z={Z_user}')

        # return Response(response.content, status=response.status_code,
        #                 content_type=response.headers.get('Content-Type', 'text/plain'))

        #  то же самое в цикле
        correction = [] # весовые коэффициенты для IDW коррекции
        for station in lst_ip_bs:
            URL = 'http://127.0.0.1:' + str(station['port']) + '/correct'
            response = rq.post(
                        URL,
                        data = binary_data,
                        headers={
                                "Content-Type": "application/x-protobuf",
                                "Accept": "application/x-protobuf",
                        },
                    )
            W = 1/math.sqrt( (X_user - station['x'])**2 + (Y_user - station['y'])**2 + \
                                ((Z_user - station['z'])**2) ) 
            delta_coords = c_pb2.Coordinates()
            delta_coords.ParseFromString(response.content)

            correction.append({
                        'station':station['station'],
                        'w':W,
                        'dx':coords.x,
                        'dy':coords.y,
                        'dz':coords.z
            })



            
            print("Статус-код:", response.status_code)
            print(f'станция { station['station'] }')

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
