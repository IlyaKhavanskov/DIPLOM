import lib as fn # подгрузка используемыз библиотек
import parsing_SATELLITES_COORDS as pi # парсер координат спутников
import numpy as np
import sys

# BRD400DLR_S_20260010000_01D_MN.rnx
filename ='BRD400DLR_S_20260010000_01D_MN.rnx.gz'

def calc_correction(X_user=None, Y_user=None, Z_user=None):
    # геодезические координаты базовой станции
    X_geodez = 3041464.0
    Y_geodez = -815026.0
    Z_geodez = 5527999.04

    # если координаты пользователя не переданы — используем координаты базовой станции
    if X_user is None:
        X_user = X_geodez
        Y_user = Y_geodez
        Z_user = Z_geodez

    station = (X_geodez, Y_geodez, Z_geodez)

    satellites = pi.parse_rinex(filename)  # поиск созвездия доступных спутников

    # отбор спутников, которые использует потребитель
    user_satellites = ['R23', 'R15', 'R17', 'R26']  # список номеров спутников
    result_satellite = []
    satellites_coords = []

    for satellite in satellites:
        if satellite['R'] in user_satellites:
            result_satellite.append(satellite)
            satellites_coords.append([
                float(np.asarray(satellite['x']).ravel()[0]),
                float(np.asarray(satellite['y']).ravel()[0]),
                float(np.asarray(satellite['z']).ravel()[0])
            ])

    if len(satellites_coords) == 0:
        raise ValueError("Не найдены спутники из списка user_satellites в RINEX-файле")

    satellites_coords = np.array(satellites_coords, dtype=float)

    # расчёт координат по спутникам
    res = fn.location(station, satellites_coords)

    # вычисление вектора ошибки
    delta_X = res[0] - X_geodez
    delta_Y = res[1] - Y_geodez
    delta_Z = res[2] - Z_geodez

    return delta_X, delta_Y, delta_Z


if __name__ == '__main__':
    try:
        X_user = float(sys.argv[1])
        Y_user = float(sys.argv[2])
        Z_user = float(sys.argv[3])
    except (IndexError, ValueError):
        X_user = Y_user = Z_user = None

    dX, dY, dZ = calc_correction(X_user, Y_user, Z_user)
    print(f"{dX:.6f} {dY:.6f} {dZ:.6f}")