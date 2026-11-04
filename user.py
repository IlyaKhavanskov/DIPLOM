import coordinates_pb2 as c_pb2
import satellites_pb2 as s_pb2
import user_class
import requests as rq
import lib as fn # подгрузка используемыз библиотек
import parsing_SATELLITES_COORDS as pi # парсер координат спутников
import numpy as np

X_ = 3041464.0
Y_ = -815026.0
Z_ = 5527999.0

delta_x = 3
delta_y = 3
delta_z = 3

URL = "http://127.0.0.1:5000/correction"

sats = s_pb2.SatelliteList(names=['R23', 'R15', 'R17', 'R26'])

rq.post("http://127.0.0.1:5000/satellites",
        data=sats.SerializeToString(),
        headers={"Content-Type": "application/x-protobuf"},
        timeout=10)


filename ='BRD400DLR_S_20260010000_01D_MN.rnx.gz'

satellites = pi.parse_rinex(filename)

# отбор спутников, которые использует потребитель

user_satellites = ['R23','R15','R17','R26'] # список номеров спутников которые использует потребитель
result_satellite = [] # список словарей спутников для рассчета координат
satellites_coords = []

for satellite in satellites:
    if satellite['R'] in user_satellites:
        result_satellite.append(satellite)

        satellites_coords.append([
            float(np.asarray(satellite['x']).ravel()[0]),
            float(np.asarray(satellite['y']).ravel()[0]),
            float(np.asarray(satellite['z']).ravel()[0])
        ])

satellites_coords = np.array(satellites_coords, dtype=float)

# рассчет координат по спутникам 
# res = fn.location(station, satellites_coords)



for i in range(10):
    X_ += delta_x # геодезические координаты
    Y_ += delta_y
    Z_ += delta_z

    # блок кода который определяет рабочее созвездие спутников



    msg = c_pb2.Coordinates(x=X_, y=Y_, z=Z_)

    try:
        response = rq.post(
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
