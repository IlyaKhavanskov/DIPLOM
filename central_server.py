from quart import  request ,Quart, Response # Импортируем request 
import subprocess
import coordinates_pb2 as c_pb2 # импорт сообщения - поправки координат
import  satellites_pb2 as s_pb2 # импорт сообщения - списка используемых спутников
from urllib.parse import urljoin
import math
import httpx
import asyncio
import sys
import user_class


users = {}   # ip -> User

# реализация многопользовательского режима
def get_user(ip):
    """Возвращает существующего пользователя или создаёт нового."""
    if ip not in users:
        users[ip] = user_class.User(ip=ip)
    return users[ip]


lst_salellites = [] # список спутников используемых потребителем

lst_bs = [
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

app = Quart(__name__)

@app.route('/')
async def hello_world():
    return 'Hello, World!'


@app.route('/correction', methods=['POST'])
async def correction():
    binary_data = await request.get_data()
    
    # в quart нет request.data есть request.body
    coords = c_pb2.Coordinates()
    coords.ParseFromString(binary_data)

    user = get_user(request.remote_addr)
    user.x, user.y, user.z = coords.x, coords.y, coords.z
                        
    sw = sx = sy = sz = 0.0   
                        
    async with httpx.AsyncClient() as client:
        tasks = []
        for  station in lst_bs:
            tasks.append(client.post(f"http://127.0.0.1:{station['port']}/correct",
                        data = binary_data,
                        headers={
                                "Content-Type": "application/x-protobuf",
                                "Accept": "application/x-protobuf",
                        })
                        
                        )
                        
        # responses = await asyncio.gather(*tasks)
        for task in asyncio.as_completed(tasks) :
            response = await task # получили вектор коррекции
            # парсим вектор коррекции из ответа
            print(response.status_code)
            correction = c_pb2.Coordinates()
            correction.ParseFromString(response.content)
            dx, dy, dz = correction.x, correction.y, correction.z # распарсили вектор коррекции
            # idw коррекция

            W = 1 / max(math.sqrt((user.x - station['x'])**2 +
                                (user.y - station['y'])**2 +
                                (user.z - station['z'])**2), 1e-6)
                                
            sw += W
            sx += W * dx
            sy += W * dy
            sz += W * dz

    user.dx, user.dy, user.dz = sx / sw, sy / sw, sz / sw   # сохраняем поправку в пользователе



    coords = c_pb2.Coordinates(x=user.dx, y=user.dy, z=user.dz)
    binary_data = coords.SerializeToString()
    return Response(binary_data, mimetype='application/x-protobuf')



@app.route('/satellites', methods=['POST'])
async def get_satellites():
    sats = s_pb2.SatelliteList()
    sats.ParseFromString(await request.get_data())

    user = get_user(request.remote_addr)
    user.satellite_lst = list(sats.names)

    return Response(b"OK", status=200, mimetype='text/plain')

    
if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)
