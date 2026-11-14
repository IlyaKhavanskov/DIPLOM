import socket
import parse_ionix as p_ion
import redis

host = '127.0.0.1'
port = 5000

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# делаем tcp сокет
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Важно: host и port передаются в двойных скобках (как кортеж)
server.bind((host, port))
server.listen()

print("Server starts")

con, addr = server.accept()  # принимаем клиента
print("connection: ", con)
print("client address: ", addr)

# Инициализируем  генератор
filename = 'COD0OPSP0D_20263180000_01D_01H_GIM.INX.gz'
target_lat = 52.5 # широта
target_lon = -13  # долгота
TEC = p_ion.get_TEC(filename, target_lat, target_lon)

# Бесконечный цикл общения с подключенным клиентом
while True:
    # Ждем команду от клиента 
    client_msg = con.recv(1024).decode().strip()
    if not client_msg or client_msg == 'stop':
        print("Клиент отключился")
        break

    try:
        # Получаем ОДНО следующее значение из вашего генератора
        val = next(TEC)
        message = str(val)
        con.send(message.encode())

# пишем в redis 
        try:
            r.delete('TEC')
        except Exception as e:
            print(e)
        r.set('TEC', val)

    except StopIteration:
        con.send("Данные закончились".encode())
        break

con.close()
server.close()
