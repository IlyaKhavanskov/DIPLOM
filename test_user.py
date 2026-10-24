import requests as rq
from urllib.parse import urljoin
import coordinates_pb2 as c_pb2  # импорт сообщения - поправки координат
import  satellites_pb2 as s_pb2 # импорт сообщения - списка используемых спутников


baseurl = 'http://127.0.0.1:5000/'

path = 'correct/1.0/2.0/3.0'
URL = urljoin(baseurl, path)


response = rq.get(URL)

# Проверяем результат
print("Статус-код:", response.status_code)  
# print("Ответ сервера:", response.text)      

coords = c_pb2.Coordinates()
coords.ParseFromString(response.content)

print(f"X={coords.x}, Y={coords.y}, Z={coords.z}")

path = 'satellites'
URL = urljoin(baseurl, path)

#  собрать сообщение
msg = s_pb2.SatelliteList(names=["R1", "R2", "R3"])

# отправить байты с правильным Content-Type
response = rq.post(
    URL,
    data=msg.SerializeToString(),         



    headers={
        "Content-Type": "application/x-protobuf",
        "Accept": "application/x-protobuf",
    },
)

print("Статус-код:", response.status_code)
