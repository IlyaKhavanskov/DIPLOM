import requests as rq
from urllib.parse import urljoin
import coordinates_pb2

baseurl = 'http://127.0.0.1:5000/'

path = 'correct/1/2/3'
URL = urljoin(baseurl, path)


response = rq.get(URL)

# Проверяем результат
print("Статус-код:", response.status_code)  
# print("Ответ сервера:", response.text)      

coords = coordinates_pb2.Coordinates()
coords.ParseFromString(response.content)

print(f"X={coords.x}, Y={coords.y}, Z={coords.z}")