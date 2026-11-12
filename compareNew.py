import math
import statistics
from datetime import datetime

import parse_rinex as pr
import parser_sp3_fixed as pf

from collections import defaultdict
import math
# Чтение файлов

rinex = pr.parse_rinex('AGA100RUS_R_20263062115_01D_RN.rnx.gz')
sp3 = pf.parser_sp3('COD0OPSRAP_20263060000_01D_05M_ORB.SP3.gz')

# Нормализация эпох к единому формату

def normalize_epoch_key(epoch):
    """
    Приводит эпоху к строке вида:
    YYYY-MM-DD HH:MM:SS.mmm

    Например:
    '2026-11-02 21:15:00.000'
    """
    if isinstance(epoch, datetime):
        dt = epoch
    else:
        s = str(epoch).strip()
        dt = None

        # Поддерживаем варианты с миллисекундами/микросекундами и без них
        for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S'):
            try:
                dt = datetime.strptime(s, fmt)
                break
            except ValueError:
                pass

        if dt is None:
            raise ValueError(f'Не удалось распознать эпоху: {epoch!r}')

    # Оставляем точность до миллисекунд
    ms = dt.microsecond // 1000
    return f"{dt.strftime('%Y-%m-%d %H:%M:%S')}.{ms:03d}"

# def count_difference(sp3,rinex):

    # Совпавшие эпохи:
    epochs = '''2026-11-02 21:45:00.000
                2026-11-02 19:45:00.000
                2026-11-02 23:15:00.000
                2026-11-02 23:45:00.000
                2026-11-02 16:45:00.000
                2026-11-02 19:15:00.000
                2026-11-02 22:45:00.000
                2026-11-02 18:15:00.000
                2026-11-02 14:45:00.000
                2026-11-02 16:15:00.000
                2026-11-02 20:45:00.000
            '''

    lines_epochs = epochs.strip().split('\n')
# delta - список словарей 
# словарь 
# {
    # 'R':'R1',
    # 'dx':[],
    # 'dy':[],
    # 'dz':[]
# }

    for epoch in lines_epochs:
        epoch = epoch.strip()
        delta = {
        }
        sorted_sp3 = sorted(sp3[epoch], key=lambda x: x['R'])
        sorted_rinex = sorted(rinex[epoch], key=lambda x: x['R'])
        for satellite_sp3 in sp3[epoch]:
            for satellite_rinex in  rinex[epoch]:
                if satellite_rinex['R'] not in delta.keys():
                    R = {
                            'R':satellite_rinex['R'],
                            'dx':(satellite_sp3['x'] - satellite_rinex['x']),
                            'dy':(satellite_sp3['y'] - satellite_rinex['y']),
                            'dz':(satellite_sp3['z'] - satellite_rinex['z'])
                        }
                    delta[satellite_rinex['R']] = R
                else:
                    delta[satellite_rinex['R']]['dx'] += satellite_sp3['x'] - satellite_rinex['x']
                    delta[satellite_rinex['R']]['dy'] += satellite_sp3['y'] - satellite_rinex['y']
                    delta[satellite_rinex['R']]['dz'] += satellite_sp3['z'] - satellite_rinex['z']
    print(delta['R15'])
    return delta






def count_difference(sp3, rinex, epochs = '2026-11-02 21:45:00.000'):
    
    # epochs = '''2026-11-02 21:45:00.000
    #             2026-11-02 19:45:00.000
    #             2026-11-02 23:15:00.000
    #             2026-11-02 23:45:00.000
    #             2026-11-02 16:45:00.000
    #             2026-11-02 19:15:00.000
    #             2026-11-02 22:45:00.000
    #             2026-11-02 18:15:00.000
    #             2026-11-02 14:45:00.000
    #             2026-11-02 16:15:00.000
    #             2026-11-02 20:45:00.000
    #         '''

    delta = defaultdict(lambda: {'dx': 0, 'dy': 0, 'dz': 0, '3d': 0, 'count': 0})

    for epoch in epochs.strip().splitlines():
        epoch = epoch.strip()

        if epoch not in sp3 or epoch not in rinex:
            continue

        for satellite_sp3 in sp3[epoch]:
            for satellite_rinex in rinex[epoch]:
                if satellite_sp3['R'] == satellite_rinex['R']:
                    sat_id = satellite_rinex['R']

                    dx = satellite_sp3['x'] - satellite_rinex['x']
                    dy = satellite_sp3['y'] - satellite_rinex['y']
                    dz = satellite_sp3['z'] - satellite_rinex['z']

                    delta[sat_id]['dx'] += dx
                    delta[sat_id]['dy'] += dy
                    delta[sat_id]['dz'] += dz
                    delta[sat_id]['3d'] += math.sqrt(dx**2 + dy**2 + dz**2)
                    delta[sat_id]['count'] += 1

    for sat_id, values in delta.items():
        count = values['count']
        values['dx'] /= count
        values['dy'] /= count
        values['dz'] /= count
        values['3d'] /= count
        print(sat_id, values)

    return delta



if __name__ == '__main__':

    # Создаём словарь SP3 с нормализованными ключами
    sp3_norm = {
        normalize_epoch_key(epoch): satellites
        for epoch, satellites in sp3.items()
    }

    # Множество нормализованных эпох из RINEX
    rinex_norm_keys = {
        normalize_epoch_key(epoch)
        for epoch in rinex.keys()
    }

    # Точно совпадающие эпохи по времени
    common_epoch_keys = rinex_norm_keys.intersection(sp3_norm.keys())

    print('Общих эпох (точное совпадение времени):', len(common_epoch_keys))

    # Списки для накопления статистики

    differences_x = []
    differences_y = []
    differences_z = []
    distances = []
    matched_epochs = set()


    # Основной цикл по эпохам из RINEX
    for epoch, rinex_sats in rinex.items():
        norm_epoch = normalize_epoch_key(epoch)

        # Берём данные только если эпоха точно есть в SP3
        if norm_epoch not in sp3_norm:
            continue

        sp3_sats_list = sp3_norm[norm_epoch]

        # Для быстрого доступа к спутникам по идентификатору
        sp3_sats = {
            sat['R']: sat
            for sat in sp3_sats_list
        }

        epoch_has_comparison = False

        for sat in rinex_sats:
            sat_id = sat['R']

            # Если такого спутника в этой эпохе SP3 нет, пропускаем
            if sat_id not in sp3_sats:
                continue

            ref = sp3_sats[sat_id]

            dx = sat['x'] - ref['x']
            dy = sat['y'] - ref['y']
            dz = sat['z'] - ref['z']

            differences_x.append(dx)
            differences_y.append(dy)
            differences_z.append(dz)

            distance_3d = math.sqrt(dx * dx + dy * dy + dz * dz)
            distances.append(distance_3d)

            epoch_has_comparison = True

        if epoch_has_comparison:
            matched_epochs.add(norm_epoch)



    # Вывод результатов
    print('Эпох, где есть хотя бы одно сравнение:', len(matched_epochs))

    if distances:
        n = len(distances)

        print('Количество сравнений:', n)

        print('Среднее смещение X:', statistics.mean(differences_x), 'м')
        print('Среднее смещение Y:', statistics.mean(differences_y), 'м')
        print('Среднее смещение Z:', statistics.mean(differences_z), 'м')

        print('RMSE X:', math.sqrt(sum(x * x for x in differences_x) / n), 'м')
        print('RMSE Y:', math.sqrt(sum(y * y for y in differences_y) / n), 'м')
        print('RMSE Z:', math.sqrt(sum(z * z for z in differences_z) / n), 'м')

        print('Общий RMSE 3D:', math.sqrt(sum(d * d for d in distances) / n), 'м')
        print('Средняя 3D ошибка:', statistics.mean(distances), 'м')
        print('Максимальное расхождение:', max(distances), 'м')

        print(30*'-')
        print('Совпавшие эпохи:',end='\n')
        for epoch in matched_epochs:
            print(epoch)
        print()

        print(rinex['2026-11-02 23:15:00.000'])
        
        epochs = '''2026-11-02 21:45:00.000
                    2026-11-02 19:45:00.000
                    2026-11-02 23:15:00.000
                    2026-11-02 23:45:00.000
                    2026-11-02 16:45:00.000
                    2026-11-02 19:15:00.000
                    2026-11-02 22:45:00.000
                    2026-11-02 18:15:00.000
                    2026-11-02 14:45:00.000
                    2026-11-02 16:15:00.000
                    2026-11-02 20:45:00.000
                '''
        
        count_difference(sp3,rinex,epochs)
        

    else:
        print('Нет сравнений для точно совпадающих эпох.')
        print('Проверьте:')
        print('1) совпадают ли даты и время в файлах;')
        print('2) шаг эпох в RINEX и SP3;')
        print('3) формат идентификаторов спутников;')
        print('4) есть ли общие спутники в одинаковых эпохах.')


