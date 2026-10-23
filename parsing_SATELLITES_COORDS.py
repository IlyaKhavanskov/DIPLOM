import gzip
import numpy as np
import math
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # для 3D
from pathlib import Path
import functions as fn
# from datetime import datetime

filename = 'BRD400DLR_S_20261170000_01D_MN.rnx.gz'

BASE_DIR = Path(__file__).resolve().parent

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



'''_____________________________________________________________________________________________________________________'''
# функция для парсинга файла
def parse_rinex(filename):

    satellites = [] # cписок словарей для каждого спутника

    path = BASE_DIR / filename

    with open('data.txt', "w") as f:

        with gzip.open(path, 'rt') as f:


            target_sat = ['R'+str(x) for x in range(0,25)] # номера спутников

            for line in f:
                # print(line)
                if 'END OF HEADER' in line:
                    break
            
            # print("=== ГЛОНАСС ЭФЕМЕРИДЫ ===\n")
            
            for line in f:
                #                                            время опорного интервала
                time_of_ephemerides = '16 45'
                if line.startswith(tuple(target_sat)) and  time_of_ephemerides in line: 
                #if line.startswith(tuple(target_sat)):
                
                    sat = line[0:3]
                    epoch = line[4:26].strip()
                    
                    # Читаем 3 строки параметров
                    x_line = next(f)
                    y_line = next(f)
                    z_line = next(f)
                    
                    x = float(x_line[4:23])
                    y = float(y_line[4:23])
                    z = float(z_line[4:23])
                    
                    vx = float(x_line[23:42])
                    vy = float(y_line[23:42])
                    vz = float(z_line[23:42])
                    
                    # print(f"{sat}  |  {epoch}")
                    # print(f"   X={x:8.1f} km   Y={y:8.1f} km   Z={z:8.1f} km")
                    # print(f"  VX={vx:7.3f}    VY={vy:7.3f}    VZ={vz:7.3f} km/s")
                    # print("-" * 60)

                    satellite = {
                        "x": x * 1000, # м
                        "y": y * 1000,
                        "z": z * 1000,
                        "Vx": vx* 1000, # м/с
                        "Vy": vy* 1000,
                        "Vz": vz* 1000,
                        "ax": [0], "ay": [0], "az": [0],
                        "tb":  time_of_ephemerides,
                        "Gn": [7.2759576141834260e-12],
                        "tc": [-3.8743019104003910e-7],
                        "R" : sat
                    }

                    satellites.append( satellite)


                satellite1 = {
                    "x":  [2.5372872558593750e7],
                    "y":  [-8.776201171875e6],
                    "z":  [2.476775390625e6],
                    "Vx": [0.3416566848754883e3],
                    "Vy": [-0.2145090103149414e3],
                    "Vz": [-3.5758600234985350e3],
                    "ax": [0], "ay": [0], "az": [0],
                    "tb": [58500],
                    "Gn": [7.2759576141834260e-12],
                    "tc": [-3.8743019104003910e-7],
}


    return satellites
# Конец функции парсинга
'''_____________________________________________________________________________________________________________________'''



'''_____________________________________________________________________________________________________________________'''
# построение графика с координатами спутников

def plot_sat_coords( satellites,NAP=(0,0,0) ):
    ''' 
    на вход подается список словарей спутников
    спутники выводятся вместе с Землей
    NAP - координаты потребителя на Земле
    '''
    # как создать маитрицу
    
    coords = np.zeros((3, len(satellites)))

    for i,satellite in enumerate(satellites):
        coords[0,i] = satellite['x'] 
        coords[1,i] = satellite['y'] 
        coords[2,i] = satellite['z'] 

    fig = plt.figure( figsize=(15, 12) )

    ax_3d = fig.add_subplot(projection='3d')   

    ax_3d.scatter(coords[0,:], coords[1,:], coords[2,:], c='red', s=20, marker='o')

    R_earth = 6_378_137.0
    u = np.linspace(0, 2 * np.pi, 60)
    v = np.linspace(0, np.pi, 30)
    xe = R_earth * np.outer(np.cos(u), np.sin(v))
    ye = R_earth * np.outer(np.sin(u), np.sin(v))
    ze = R_earth * np.outer(np.ones_like(u), np.cos(v))
    ax_3d.plot_surface(xe, ye, ze, color='steelblue', alpha=0.6, linewidth=0)

    #  если задана точка потребилеля
    if NAP != (0,0,0):

        ax_3d.scatter(
        NAP[0], NAP[1], NAP[2],
        c='green', s=80, marker='^', label='NAP (потребитель)'
        )

        for i,satellite in enumerate(satellites):

            ax_3d.plot(
                [NAP[0], satellite['x']],
                [NAP[1],satellite['y']],
                [NAP[2], satellite['z']],
                c='orange', linestyle='--', linewidth=1.5, alpha=0.7, label='Линия связи'
            )
            ax_3d.text(coords[0, i], coords[1, i], coords[2, i],
                satellites[i]['R'], fontsize=10, color='darkred')

    plt.show()

satellites_for_NAP = []

if __name__ == "__main__":
    # BRD400DLR_S_20260010000_01D_MN.rnx
    filename ='BRD400DLR_S_20260010000_01D_MN.rnx.gz'

    satellites = parse_rinex(filename)

    NAP = list(fn.BLH_to_ECEF(83, 36.8762, 14.9894))# точка потребителя
    # plot_sat_coords( satellites,NAP=(0,0,0) ):
    plot_sat_coords(satellites, NAP)


    








