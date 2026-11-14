import socket

client = socket.socket()
address = ('127.0.0.1', 5000)

client.connect(address)
print("Connected...")

for i in range(3):
    # Отправляем запрос на получение одного значения
    client.send(b'{TEC}')

    # Обязательно указываем размер буфера (1024 байта)
    data = client.recv(1024)
    print(data.decode())

client.close()
