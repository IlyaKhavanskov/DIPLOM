from flask import Flask, request  # Импортируем request из flask
import requests as rq
import base_station as bs
import subprocess


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

            return f'X={dX}, Y={dY}, Z={dZ}'
        
    if request.method == 'POST':
            return f'X={x}, Y={y}, Z={z}'

if __name__ == '__main__':
    app.run(debug=True)