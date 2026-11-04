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
import logging

# общий лог сервера (Quart, Hypercorn, ошибки)
logging.basicConfig(
    filename="central_server.log",
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    force=True,
)

# приглушаем  библиотеки
# logging.getLogger("httpx").setLevel(logging.WARNING)

# чистый лог данных пользователя
log = logging.getLogger("server")
log.setLevel(logging.INFO)
log.propagate = False # не дублировать в central_server.log

handler = logging.FileHandler("user_data.log", encoding="utf-8")
handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
log.addHandler(handler)

users = {}   # ip -> User

# реализация многопользовательского режима
def get_user(ip):
    """Возвращает существующего пользователя или создаёт нового."""
    if ip not in users:
        users[ip] = user_class.User(ip=ip)
    return users[ip]

def find_user(ip):
    """Возвращает пользователя по ip или None, если он ещё не зарегистрирован."""
    return users.get(ip)
# пользователь создается при передаче списка номеров спутников
# в ручке correction проверяется его наличие


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

# X_user = None
# Y_user = None
# Z_user = None

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

    user = find_user(request.remote_addr)
    if user is None:
        return Response("User not registered. Send /satellites first.",
                        status=403, mimetype='text/plain')
    # сырые координаты вычисленные по спутникам
    user.x, user.y, user.z = coords.x, coords.y, coords.z
    # геодезически точные координаты
    x_pr, y_pr, z_pr = coords.x_pr, coords.y_pr, coords.z_pr
                        
    sw = sx = sy = sz = 0.0   
                        
    async with httpx.AsyncClient(timeout=10) as client:
        tasks = []
        for station in lst_bs:
            tasks.append(
                client.post(
                    f"http://127.0.0.1:{station['port']}/correct",
                    content=binary_data,
                    headers={
                        "Content-Type": "application/x-protobuf",
                        "Accept": "application/x-protobuf",
                    },
                )
            )

        responses = await asyncio.gather(*tasks)   # ждём один раз, получаем список ответов

    for station, response in zip(lst_bs, responses):
        response.raise_for_status()
        print(response.status_code)
        correction = c_pb2.Coordinates()
        correction.ParseFromString(response.content)
        dx, dy, dz = correction.x, correction.y, correction.z

        W = 1 / max(math.sqrt((user.x - station['x'])**2 +
                            (user.y - station['y'])**2 +
                            (user.z - station['z'])**2), 1e-6)
        sw += W
        sx += W * dx
        sy += W * dy
        sz += W * dz

    user.dx, user.dy, user.dz = sx / sw, sy / sw, sz / sw   # сохраняем поправку в пользователе

    log.info(f"{request.remote_addr} | {user.x} | {user.y} |\
            {user.z} | {x_pr} | {y_pr} | {z_pr} | {dx} | {dy} | {dz}")


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
    app.run(host="127.0.0.1", port=5000, debug=True,  use_reloader=False)
