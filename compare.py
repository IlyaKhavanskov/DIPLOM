import parse_rinex as pr
import parser_sp3_fixed as pf

filename = 'AGA100RUS_R_20263062115_01D_RN.rnx.gz'
rinex = pr.parse_rinex(filename)

filename = 'COD0OPSRAP_20263060000_01D_05M_ORB.SP3.gz'
sp3 = pf.parser_sp3(filename)

coincidence  = [] # совпадения
for key in rinex.keys() :
    if key in sp3.keys():
        coincidence.append(key)
print('количество совпадений = ',len(coincidence))

import math
import statistics

differences_x = []
differences_y = []
differences_z = []
distances = []

for key in coincidence:

    sp3_satellites = {sat['R']: sat for sat in sp3[key]}

    for satellite in rinex[key]:

        sat_id = satellite['R']

        if sat_id in sp3_satellites:

            sat_sp3 = sp3_satellites[sat_id]

            dx = satellite['x'] - sat_sp3['x']
            dy = satellite['y'] - sat_sp3['y']
            dz = satellite['z'] - sat_sp3['z']

            differences_x.append(dx)
            differences_y.append(dy)
            differences_z.append(dz)

            distance = math.sqrt(dx**2 + dy**2 + dz**2)
            distances.append(distance)

if distances:
    n = len(distances)

    rmse_x = math.sqrt(sum(x**2 for x in differences_x) / n)
    rmse_y = math.sqrt(sum(y**2 for y in differences_y) / n)
    rmse_z = math.sqrt(sum(z**2 for z in differences_z) / n)

    rmse_3d = math.sqrt(
        sum(d**2 for d in distances) / n
    )

    print('\nРезультаты сравнения с SP3:')
    print('Количество сравнений:', n)

    print('Среднее смещение X:', statistics.mean(differences_x), 'м')
    print('Среднее смещение Y:', statistics.mean(differences_y), 'м')
    print('Среднее смещение Z:', statistics.mean(differences_z), 'м')

    print('RMSE X:', rmse_x, 'м')
    print('RMSE Y:', rmse_y, 'м')
    print('RMSE Z:', rmse_z, 'м')

    print('Общий RMSE 3D:', rmse_3d, 'м')
    print('Максимальное расхождение:', max(distances), 'м')