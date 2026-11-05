import coordinates_pb2 as c_pb2
import satellites_pb2 as s_pb2
import user_class
import requests as rq
import lib as fn # подгрузка используемыз библиотек
import parsing_SATELLITES_COORDS as pi # парсер координат спутников
import numpy as np
import math

X_ = 3041464.0 # начальное положение потребителя
Y_ = -815026.0
Z_ = 5527999.0

delta_x = 3
delta_y = 3
delta_z = 3

URL = "http://127.0.0.1:5000/correction"



filename ='BRD400DLR_S_20260010000_01D_MN.rnx.gz'

satellites = pi.parse_rinex(filename)

pi.plot_sat_coords( satellites,(X_,Y_,Z_) )

# отбор спутников рядом с точкой на сфере орбиты
H_sat = 19100000 # радиус области отбора вокруг точки на сфере, м
H = fn.R3 + 19100000 # радиус орбиты ГЛОНАСС, м
B, L, h = fn.ECEF_to_BLH(X_, Y_, Z_)
x_sphere, y_sphere, z_sphere = fn.BLH_to_ECEF(H, B, L)

user_satellites = []

for satellite in satellites:
    if (satellite['x']- x_sphere )**2 + \
        (satellite['y']- y_sphere )**2 + \
        (satellite['z']- z_sphere )**2 < ( H_sat + 4000000)**2:

        user_satellites.append(satellite)
        print(satellite['R'])
            
            # r = (satellite['x']- x_sphere )**2 + \
            #     (satellite['y']- y_sphere )**2 + \
            #     (satellite['z']- z_sphere )**2

satellites_coords=[]
for satellite in user_satellites:

        satellites_coords.append([
            float(np.asarray(satellite['x']).ravel()[0]),
            float(np.asarray(satellite['y']).ravel()[0]),
            float(np.asarray(satellite['z']).ravel()[0])
        ])

satellites_coords = np.array(satellites_coords, dtype=float)

#  сообщение серверу о созвездии спутников
sats = s_pb2.SatelliteList(names=[satellite['R'] for satellite in user_satellites])

# создаем сессию
session = rq.Session()
# общий заголовок для сессии
session.headers.update({
    "Content-Type": "application/x-protobuf",
    "Accept": "application/x-protobuf",
})


try:
    rq.session.post("http://127.0.0.1:5000/satellites",
            data=sats.SerializeToString(),
            headers={"Content-Type": "application/x-protobuf"},
            timeout=10)
except Exception:
    print('Ошибка, центральный сервер еще не поднят') 

for i in range(10):
    X_ += delta_x # геодезические координаты
    Y_ += delta_y
    Z_ += delta_z

    #  считаем координаты по спутникам
    x_raw, y_raw, z_raw ,dt = fn.location((X_,Y_,Z_), satellites_coords)

    msg = c_pb2.Coordinates( x_pr=X_,  y_pr=Y_,  z_pr=Z_,x= x_raw,y=y_raw,z=z_raw)

    try:
        response = rq.session.post(
            URL,
            data=msg.SerializeToString(),
            headers={
                "Content-Type": "application/x-protobuf",
                "Accept": "application/x-protobuf",
            },
            timeout=10,
        )

        print("Статус-код:", response.status_code)

        response.raise_for_status()

        result = c_pb2.Coordinates()
        result.ParseFromString(response.content)

        print(f"x={result.x}, y={result.y}, z={result.z}")

    except rq.RequestException as e:
        print("Ошибка HTTP-запроса:", e)
    except Exception as e:
        print("Ошибка обработки ответа:", e)
    finally:
            # закрываем сессию
            session.close()