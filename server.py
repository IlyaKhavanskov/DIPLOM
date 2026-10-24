from flask import Flask, request , Response # Импортируем request из flask
import requests as rq
import base_station as bs
import subprocess
import coordinates_pb2 as c_pb2 # импорт сообщения - поправки координат
import  satellites_pb2 as s_pb2 # импорт сообщения - списка используемых спутников

lst_salellites = []


app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/correct/<float:x>/<float:y>/<float:z>', methods=['GET','POST'])
@app.route('/correct/<int:x>/<int:y>/<int:z>', methods=['GET','POST'])
def get_xyz(x, y, z):  
    if request.method == 'GET':
        answer = subprocess.run(['python', "base_station.py", str(x), str(y),str(z)] ,
            capture_output=True, text=True )
        if answer.returncode != 0:
            return Response(answer.stderr, status=500, mimetype='text/plain')
        if answer.stdout:
        # парсим результат работы скрипта
            line = answer.stdout.strip()          
            dX, dY, dZ = map(float, line.split()) 

            coords = c_pb2.Coordinates(x=dX,y=dY,z=dZ)
            binary_data = coords.SerializeToString()
            # return f'X={dX}, Y={dY}, Z={dZ}'
            return Response(binary_data, mimetype='application/x-protobuf')
        
    
    if request.method == 'POST':
        coords = c_pb2.Coordinates(x=float(x), y=float(y), z=float(z))
        return Response(coords.SerializeToString(),
                        mimetype='application/x-protobuf')


@app.route('/satellites', methods=['GET','POST'])
def get_satellites():
    if request.method == 'POST':
        binary_data = request.data
        global lst_salellites
        satellites = s_pb2.SatelliteList()
        satellites.ParseFromString(binary_data)
        lst_salellites = list(satellites.names) 

        return Response(b"OK", status=200, mimetype='text/plain')

    
if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)
