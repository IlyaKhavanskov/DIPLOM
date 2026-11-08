import math
import statistics
from datetime import datetime

import parse_rinex as pr
import parser_sp3_fixed as pf

rinex = pr.parse_rinex('AGA100RUS_R_20263062115_01D_RN.rnx.gz')
sp3 = pf.parser_sp3('COD0OPSRAP_20263060000_01D_05M_ORB.SP3.gz')

sp3_times = sorted(datetime.strptime(epoch, '%Y-%m-%d %H:%M:%S.%f') for epoch in sp3)
differences_x, differences_y, differences_z, distances = [], [], [], []
matched_epochs = set()

for epoch, rinex_sats in rinex.items():
    t = datetime.strptime(epoch, '%Y-%m-%d %H:%M:%S.%f')
    before = [time for time in sp3_times if time <= t]
    after = [time for time in sp3_times if time >= t]
    if not before or not after:
        continue

    t0, t1 = before[-1], after[0]
    sats0 = {sat['R']: sat for sat in sp3[t0.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]]}
    sats1 = {sat['R']: sat for sat in sp3[t1.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]]}
    # Ключи эпох SP3 сохранены с точностью до миллисекунд.
    if t0 == t1:
        weight = 0.0
    else:
        weight = (t - t0).total_seconds() / (t1 - t0).total_seconds()

    for sat in rinex_sats:
        sat_id = sat['R']
        if sat_id not in sats0 or sat_id not in sats1:
            continue
        ref0, ref1 = sats0[sat_id], sats1[sat_id]
        dx = sat['x'] - (ref0['x'] + weight * (ref1['x'] - ref0['x']))
        dy = sat['y'] - (ref0['y'] + weight * (ref1['y'] - ref0['y']))
        dz = sat['z'] - (ref0['z'] + weight * (ref1['z'] - ref0['z']))
        differences_x.append(dx)
        differences_y.append(dy)
        differences_z.append(dz)
        distances.append(math.sqrt(dx**2 + dy**2 + dz**2))
        matched_epochs.add(epoch)

print('Совпавших эпох:', len(matched_epochs))
if distances:
    n = len(distances)
    print('Количество сравнений:', n)
    print('Среднее смещение X:', statistics.mean(differences_x), 'м')
    print('Среднее смещение Y:', statistics.mean(differences_y), 'м')
    print('Среднее смещение Z:', statistics.mean(differences_z), 'м')
    print('RMSE X:', math.sqrt(sum(x*x for x in differences_x) / n), 'м')
    print('RMSE Y:', math.sqrt(sum(y*y for y in differences_y) / n), 'м')
    print('RMSE Z:', math.sqrt(sum(z*z for z in differences_z) / n), 'м')
    print('Общий RMSE 3D:', math.sqrt(sum(d*d for d in distances) / n), 'м')
    print('Средняя 3D ошибка:', statistics.mean(distances), 'м')
    print('Максимальное расхождение:', max(distances), 'м')
else:
    print('Нет общих спутников и эпох. Проверьте дату и спутниковые идентификаторы файлов.')
