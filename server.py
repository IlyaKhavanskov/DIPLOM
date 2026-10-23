from flask import Flask, request , Response # Импортируем request из flask
import requests as rq
import base_station as bs
import subprocess
import coordinates_pb2 as c_pb2

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/correct/<x>/<y>/<z>', methods=['GET','POST'])
def get_xyz(x, y, z):  
    if request.method == 'GET':
        answer = subprocess.run(["python3", "base_station.py", x, y,z] ,
            capture_output=True, text=True )
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
    
if __name__ == '__main__':
    app.run(debug=True)