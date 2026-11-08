import gzip
import numpy as np
import math
import lib as fn
import gzip
# from datetime import datetime

# https://dns.comss.one/dns-query


# === Константы ===
# Глобальные переменные
a = 6378137.0 # большая полуось
b = 6356752.314 # малая полуось
alpha = 1/298.3
PI = math.pi
e = math.sqrt((a**2 - b**2) / a**2)  # эксцентриситет
c = 299792458  # скорость света в вакууме
W3 = 7.292115e-5 # угловая скорость вращения Земли в радианах в секунду
mu = 3.986004418e14 # гравитационный параметр Земли в м^3/с^2
c20 = -1082.63e-6 # коэффициент сферической гармоники 20-го порядка
R3 = 6378137.0 # средний радиус Земли в метрах
f =1602 * 10 ** 6 # Центральная (средняя) частота: ~1602 МГц

        
# R17 — Идентификатор спутника      - 0
# 2026 11 03 18 45 00 — Эпоха эфемерид   - 1
#  Смещение часов спутника [c] - 2
# Относительный сдвиг частоты часов - 3
#   Время передачи сообщения - 4
# Координата X
# скорость по Vx
# ускоренике AX

# Индикатор здоровья спутника 0/1

# Координата Y
# скорость по Vy
# ускоренике AY

# Частотный номер канала (Литера частоты)

# Координата Z
# скорость по Vz
# ускоренике AZ

# Возраст оперативной информации

'''_____________________________________________________________________________________________________________________'''
# функция для парсинга файла
def parse_epoch(filename):
    with gzip.open(filename, 'rt', encoding='utf-8') as f:
        # Пропускаем заголовок RINEX, чтобы код не споткнулся в начале
        for line in f:
            if "END OF HEADER" in line:
                break
                
        epochs = []
        for line in f:
            if not line.strip():
                continue
            elif line.strip().startswith('R'):
                # Добавили пропуск 3 строк данных, чтобы не читать их как новые эпохи
                str_epoch = line.replace('D', 'E').split()
                epoch = f'год {str_epoch[1]} месяц {str_epoch[2]} день {str_epoch[3]} час {str_epoch[4]} минута {str_epoch[5]} секунда {str_epoch[6]}'
                f.readline(); f.readline(); f.readline() 
                
                if epoch not in epochs:
                    epochs.append(epoch)
    return epochs
                
def parse_rinex(filename,epochs = None):
    satellites = [] # список словарей для каждого спутника

    with gzip.open(filename, 'rt', encoding='utf-8') as f:
        epochs_dict = {}

        for line in f:
            # Пропускаем пустые строки
            if not line.strip():
                continue
            
            # Если строка начинается с 'R' (ГЛОНАСС)
            if line.strip().startswith('R'):
                # Первая строка содержит метаданные, её можно оставить через split, 
                # так как там обычно есть пробелы, но для надежности заменим D на E
                str1 = line.replace('D', 'E').split()
                
                # Читаем следующие 3 строки с орбитальными данными
                # .ljust(60) гарантирует, что строка будет не меньше 60 символов (чтобы не упасть по индексам)
                line2 = f.readline().replace('D', 'E').ljust(80)
                line3 = f.readline().replace('D', 'E').ljust(80)
                line4 = f.readline().replace('D', 'E').ljust(80)
                
                # Парсим с отступом в 4 символа в начале строки
                # Строка 2: X, Vx, ax, health
                x_val      = line2[ 4:23].strip()
                vx_val     = line2[23:42].strip()
                ax_val     = line2[42:61].strip()
                health_val = line2[61:80].strip()
                
                # Строка 3: Y, Vy, ay, freq_num
                y_val      = line3[ 4:23].strip()
                vy_val     = line3[23:42].strip()
                ay_val     = line3[42:61].strip()
                freq_val   = line3[61:80].strip()
                
                # Строка 4: Z, Vz, az, age
                z_val      = line4[ 4:23].strip()
                vz_val     = line4[23:42].strip()
                az_val     = line4[42:61].strip()
                age_val    = line4[61:80].strip()
                # Формируем дату и время эпохи
                # Время занимает фиксированные колонки; split() может склеить секунды со смещением часов.
                epoch = f'{int(line[4:8]):04d}-{int(line[9:11]):02d}-{int(line[12:14]):02d} {int(line[15:17]):02d}:{int(line[18:20]):02d}:{float(line[21:23]):06.3f}'
                # Безопасно конвертируем в float/int с дефолтными значениями (0), если поле пустое
                satellite = {
                    'R': str1[0],
                    'epoch': epoch,
                    
                    "x": float(x_val) if x_val else 0.0, 
                    "y": float(y_val) if y_val else 0.0, 
                    "z": float(z_val) if z_val else 0.0,
                    
                    "Vx": float(vx_val) if vx_val else 0.0, 
                    "Vy": float(vy_val) if vy_val else 0.0, 
                    "Vz": float(vz_val) if vz_val else 0.0,
                    
                    "ax": float(ax_val) if ax_val else 0.0, 
                    "ay": float(ay_val) if ay_val else 0.0, 
                    "az": float(az_val) if az_val else 0.0,
                    
                    "health": int(float(health_val)) if health_val else 0,
                    "freq_num": int(float(freq_val)) if freq_val else 0,
                    "age": float(age_val) if age_val else 0.0
                }

                if epoch not in epochs_dict:
                    epochs_dict[epoch] = [satellite]
                else:
                    epochs_dict[epoch].append(satellite)

    return  epochs_dict


# Конец функции парсинга
if __name__ == '__main__':
    filename = 'AGA100RUS_R_20263062115_01D_RN.rnx.gz'
    # EKTG00RUS_R_20263081845_01D_RN.rnx.gz
    result = parse_rinex(filename)
    # parse_epoch(filename)
    # print( len(result.keys() ) )
    print( result.keys()  )
