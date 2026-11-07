
import coordinates_pb2 as c_pb2
import satellites_pb2 as s_pb2
import requests as rq
import lib as fn  # подгрузка используемых библиотек
import parsing_SATELLITES_COORDS as pi  # парсер координат спутников
import numpy as np
from websocket import create_connection

X_ = 3041464.0  # начальное положение потребителя
Y_ = -815026.0
Z_ = 5527999.0

delta_x = 3
delta_y = 3
delta_z = 3

URL_SATS = "http://127.0.0.1:5000/satellites"
WS_URL = "ws://127.0.0.1:5000/ws"

filename = 'BRD400DLR_S_20260010000_01D_MN.rnx.gz'

satellites = pi.parse_rinex(filename)

# отбор спутников рядом с точкой на сфере орбиты
H_sat = 19100000  # радиус области отбора вокруг точки на сфере, м
H = fn.R3 + 19100000  # радиус орбиты ГЛОНАСС, м
B, L, h = fn.ECEF_to_BLH(X_, Y_, Z_)
x_sphere, y_sphere, z_sphere = fn.BLH_to_ECEF(H, B, L)

user_satellites = []
for satellite in satellites:
    if (satellite['x'] - x_sphere) ** 2 + \
       (satellite['y'] - y_sphere) ** 2 + \
       (satellite['z'] - z_sphere) ** 2 < (H_sat + 4000000) ** 2:
        user_satellites.append(satellite)
        print(satellite['R'])

satellites_coords = []
for satellite in user_satellites:
    satellites_coords.append([
        float(np.asarray(satellite['x']).ravel()[0]),
        float(np.asarray(satellite['y']).ravel()[0]),
        float(np.asarray(satellite['z']).ravel()[0]),
    ])
satellites_coords = np.array(satellites_coords, dtype=float)

# сообщение серверу о созвездии спутников
sats = s_pb2.SatelliteList(names=[satellite['R'] for satellite in user_satellites])

#  регистрация пользователя ДО подключения по websocket
try:
    r = rq.post(URL_SATS,
                data=sats.SerializeToString(),
                headers={"Content-Type": "application/x-protobuf"},
                timeout=10)
    r.raise_for_status()
except Exception as e:
    print("Не удалось отправить список спутников:", e)
    raise SystemExit(1)


try: #
    ws = create_connection(WS_URL, timeout=10, source_address=("127.0.0.3", 0))
    print("Статус-код подключения:", ws.getstatus())
except Exception as e:
    print(f"Ошибка подключения: {e}")
    raise SystemExit(1)

try:
    for i in range(10):
        X_ += delta_x  # геодезические координаты
        Y_ += delta_y
        Z_ += delta_z

        # считаем координаты по спутникам
        x_raw, y_raw, z_raw, dt = fn.location((X_, Y_, Z_), satellites_coords)

        msg = c_pb2.Coordinates(x_pr=X_, y_pr=Y_, z_pr=Z_,
                                x=x_raw, y=y_raw, z=z_raw)

        # отправляем именно байты, в бинарном кадре
        ws.send_binary(msg.SerializeToString())

        
        response = ws.recv()
        if not response:
            print("Сервер закрыл соединение, код:")
            break

        
        result = c_pb2.Coordinates()
        result.ParseFromString(response)
        print(f"x={result.x}, y={result.y}, z={result.z}")
except Exception as e:
    print("Ошибка во время обмена:", e)
finally:
    # закрытие соединения: сервер удалит пользователя в finally
    ws.close()