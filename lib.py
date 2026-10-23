import math
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
'''импортирование собственных модулей '''
import parse_ionix as pi
import parsing_SATELLITES_COORDS as prsc

# === Константы ===
# Глобальные переменные
a = 6378137.0
b = 6356752.314
alpha = 1/298.3
PI = math.pi
e = math.sqrt((a**2 - b**2) / a**2)          # FIX: было a2 - b2 (NameError)
c = 299792458
W3 = 7.292115e-5
mu = 3.986004418e14
c20 = -1082.63e-6
R3 = 6378137.0
f = 1602 * 10 ** 6
dT = 0.0                                      # FIX: dT использовался, но не был определён

'''_____________________________________________________________________________________________________________________'''
# Перевод геодезических координат в геоцентрические
def BLH_to_ECEF(h, B, L):
    global a, b, e
    B = math.radians(B)
    L = math.radians(L)
    N = a * (1 - e ** 2 * math.sin(B)**2) ** -0.5
    x = (N + h) * math.cos(B) * math.cos(L)
    y = (N + h) * math.cos(B) * math.sin(L)
    z = (N * (1 - e**2) + h) * math.sin(B)
    return x, y, z

'''_____________________________________________________________________________________________________________________'''
# перевод геоцентрические (подвижные) -> геодезические
def ECEF_to_BLH(x, y, z):
    global a, b, e
    e2 = e**2
    p = math.hypot(x, y)
    L = math.atan2(y, x)
    if p < 1e-9 and abs(z) < 1e-9:
        return 0.0, 0.0, -a
    if p < 1e-9:
        B = PI/2 if z >= 0 else -PI/2
        h = abs(z) - b
        return math.degrees(B), math.degrees(L), h
    B = math.atan2(z, p * (1 - e2))
    for _ in range(20):
        sinB = math.sin(B)
        N = a / math.sqrt(1 - e2 * sinB * sinB)
        h = p / math.cos(B) - N
        denom = 1 - e2 * N / (N + h)
        if abs(denom) < 1e-12:
            break
        B_new = math.atan2(z, p * denom)
        if abs(B_new - B) < 1e-12:
            B = B_new
            break
        B = B_new
    sinB = math.sin(B)
    N = a / math.sqrt(1 - e2 * sinB * sinB)
    h = p / math.cos(B) - N
    return math.degrees(B), math.degrees(L), h

'''_____________________________________________________________________________________________________________________'''
# satellite1 = {
#     "x":  [2.5372872558593750e7],
#     "y":  [-8.776201171875e6],
#     "z":  [2.476775390625e6],
#     "Vx": [0.3416566848754883e3],
#     "Vy": [-0.2145090103149414e3],
#     "Vz": [-3.5758600234985350e3],
#     "ax": [0], "ay": [0], "az": [0],
#     "tb": [58500],
#     "Gn": [7.2759576141834260e-12],
#     "tc": [-3.8743019104003910e-7],
# }

'''_____________________________________________________________________________________________________________________'''
def location(NAP, satellites):
    global dT, c, W3
    sigma_noise = 1.73
    n = len(satellites)
    D_obs = np.zeros(n)
    for i in range(n):
        random_error = np.random.normal(0, sigma_noise)
        geom = math.sqrt((NAP[0]-satellites[i,0])**2 +
                         (NAP[1]-satellites[i,1])**2 +
                         (NAP[2]-satellites[i,2])**2)
        iono = iono_delay(NAP[0], NAP[1], NAP[2],
                          satellites[i,0], satellites[i,1], satellites[i,2])
        
        tropo_delay = troposphere_delay(NAP)
        # FIX: было  c*iono + c*tropo_delay + iono  (iono в метрах, tropo в секундах;
        #      c*iono — лишнее умножение, iono дублировался)
        D_obs[i] = geom + c * dT + iono + c * tropo_delay + random_error

    NAP_guess = np.array([0.0, 0.0, 0.0, 0.0])
    H = np.empty((n, 4))
    R = np.eye(n)
    D_calc = np.zeros(n)
    count = 0
    delta = np.ones(4)
    while np.linalg.norm(delta) > 1e-4 and count < 100:
        count += 1
        for i in range(n):
            dist = math.sqrt((NAP_guess[0]-satellites[i,0])**2 +
                             (NAP_guess[1]-satellites[i,1])**2 +
                             (NAP_guess[2]-satellites[i,2])**2)
            D_calc[i] = dist + NAP_guess[3]
            H[i,0] = -(satellites[i,0] - NAP_guess[0]) / dist
            H[i,1] = -(satellites[i,1] - NAP_guess[1]) / dist
            H[i,2] = -(satellites[i,2] - NAP_guess[2]) / dist
            H[i,3] = 1.0
        delta = np.linalg.pinv(H.T @ np.linalg.pinv(R) @ H) @ H.T @ np.linalg.pinv(R) @ (D_obs - D_calc)
        NAP_guess = NAP_guess + delta
    NAP_guess[3] = NAP_guess[3] / c
    t = np.mean(D_obs) / c
    A = W3 * t
    x0 = NAP_guess[0]
    y0 = NAP_guess[1]
    NAP_guess[0] = x0 * math.cos(A) + y0 * math.sin(A)
    NAP_guess[1] = y0 * math.cos(A) - x0 * math.sin(A)
    return NAP_guess

'''_____________________________________________________________________________________________________________________'''
def troposphere_delay(NAP):
    x, y, z = NAP[0], NAP[1], NAP[2]
    BLH = ECEF_to_BLH(x, y, z)
    h_m  = BLH[2]
    h_km = h_m / 1000.0
    phi  = math.radians(BLH[0])
    P  = 1013.25 * (1 - 0.0000226 * h_m) ** 5.225
    T  = 291.16  - 0.00650 * h_m
    H  = 50.0    * math.exp(-0.0006396 * h_m)
    ZHD = (0.0022767 * P) / (1 - 0.00266 * math.cos(2*phi) - 0.00028 * h_km)
    Rd  = 287.054
    g_m = 9.784 * (1 - 0.00266 * math.cos(2*phi) - 0.00028 * h_km)
    Tm  = 70.2  + 0.72 * T
    e0  = (H / 100.0) * 6.112 * math.exp(17.67 * (T - 273.15) / (T - 29.65))
    K3  = 3.701e5
    ZWD = 1e-6 * (Rd / g_m) * (K3 / Tm) * (e0 / 3.7)
    T_troposphere = (ZHD + ZWD) / c
    return T_troposphere

'''_____________________________________________________________________________________________________________________'''
def iono_delay(X_nap, Y_nap, Z_nap, X_s, Y_s, Z_s):
    # ЗДЕСЬ УКАЗЫВАЮТСЯ ШИРОТА И ДОЛГОТА ОБЛАСТИ МОДЕЛИРОВАНИЯ 
    filename = 'ROBR007A00.26I.gz'
    lat = 60.5
    lon = -15
    VTEC = pi.parser_ionex(filename, lat, lon)

    h = 450000  # 450 км
    r = (X_s - X_nap, Y_s - Y_nap, Z_s - Z_nap)
    n = (X_nap / math.hypot(X_nap, Y_nap, Z_nap),
         Y_nap / math.hypot(X_nap, Y_nap, Z_nap),
         Z_nap / math.hypot(X_nap, Y_nap, Z_nap))
    r_vertical = np.dot(r, n)
    sin_E = r_vertical / math.hypot(*r)
    E = math.asin(sin_E)

    
    sinE_ = R3 / (R3 + h) * math.cos(E)          
    M_E = 1.0 / sinE_                             

    d_R = 40.3 * VTEC * M_E / (f * f)             
    return d_R

'''_____________________________________________________________________________________________________________________'''
def consumer_movement(X_nap, Y_nap, Z_nap, type_of_movement='line', delta_T=1):
    match type_of_movement:
        case 'line':
            v_x = 2
            V_y = 0
            X_nap = X_nap + v_x * delta_T          # FIX: было v_x * 1
        case 'circular':
            R = 1000
            omega = 0.01
            angle = omega * delta_T
            X_nap = R * math.cos(angle)
            Y_nap = R * math.sin(angle)
        case 'random':
            import random
            X_nap += random.gauss(0, 0.1)
            Y_nap += random.gauss(0, 0.1)
            Z_nap += random.gauss(0, 0.1)
        case 'logistic':
            L, k, t0 = 100, 0.1, 5
            X_nap = L / (1 + math.exp(-k * (delta_T - t0)))
    return X_nap, Y_nap, Z_nap

'''_____________________________________________________________________________________________________________________'''
def satellite_position(satellite, h_step=60.0, t_offset=0):
    """Расчёт положения спутника ГЛОНАСС по эфемеридам.

    Как в UIRS_functions.py, интегрирование выполняется в СИ:
    координаты — м, скорости — м/с, ускорения — м/с^2.
    t_offset задаётся в секундах относительно одного опорного момента.
    """

    tb = satellite['tb']
    if isinstance(tb, (list, np.ndarray)):          
        tb = tb[0]                                  
    if isinstance(tb, str):                        
        tb_sec = int(tb.split()[0]) * 3600 + int(tb.split()[1]) * 60
    else:                                           
        tb_sec = int(tb)                            

    t_sat_prev = tb_sec + float(t_offset)

    t_sat_prev = t_sat_prev - 0.071

    tc = satellite["tc"][0]
    Gn = satellite["Gn"][0]
    t_glonass = t_sat_prev + tc - Gn * (t_sat_prev - tb_sec)

    x0 = satellite['x'];  y0 = satellite['y'];  z0 = satellite['z']
    vx0 = satellite['Vx']; vy0 = satellite['Vy']; vz0 = satellite['Vz']

    
    if isinstance(x0, (list, np.ndarray)): x0 = x0[0]   # FIX
    if isinstance(y0, (list, np.ndarray)): y0 = y0[0]   # FIX
    if isinstance(z0, (list, np.ndarray)): z0 = z0[0]   # FIX
    if isinstance(vx0, (list, np.ndarray)): vx0 = vx0[0] # FIX
    if isinstance(vy0, (list, np.ndarray)): vy0 = vy0[0] # FIX
    if isinstance(vz0, (list, np.ndarray)): vz0 = vz0[0] # FIX

    ax_ext = satellite['ax'][0] if isinstance(satellite['ax'], (list, np.ndarray)) else satellite['ax']  # FIX
    ay_ext = satellite['ay'][0] if isinstance(satellite['ay'], (list, np.ndarray)) else satellite['ay']  # FIX
    az_ext = satellite['az'][0] if isinstance(satellite['az'], (list, np.ndarray)) else satellite['az']  # FIX


    if max(abs(vx0), abs(vy0), abs(vz0)) < 100:
        vx0 *= 1000.0
        vy0 *= 1000.0
        vz0 *= 1000.0

    if 0 < max(abs(ax_ext), abs(ay_ext), abs(az_ext)) < 1:
        ax_ext *= 1000.0
        ay_ext *= 1000.0
        az_ext *= 1000.0

    s = np.array([x0, y0, z0, vx0, vy0, vz0], dtype=float)

    t = tb_sec
    dt_total = t_glonass - tb_sec
    step_sign = 1.0 if dt_total >= 0 else -1.0
    h_step = abs(float(h_step))

    def f(state):
        x, y, z, vx, vy, vz = state
        r = math.sqrt(x**2 + y**2 + z**2)

        # Формулы из UIRS_functions.py: центральное поле + C20 в СИ.
        coeff = -1.5 * c20 * mu * (R3**2) / (r**5)
        ax_grav = -mu * x / (r**3) + coeff * x * (1 - 5 * (z**2) / (r**2))
        ay_grav = -mu * y / (r**3) + coeff * y * (1 - 5 * (z**2) / (r**2))
        az_grav = -mu * z / (r**3) + coeff * z * (3 - 5 * (z**2) / (r**2))

        ax = ax_grav + ax_ext
        ay = ay_grav + ay_ext
        az = az_grav + az_ext
        return np.array([vx, vy, vz, ax, ay, az])

    def rk4(arg, step):
        k1 = step * f(arg)
        k2 = step * f(arg + 0.5 * k1)
        k3 = step * f(arg + 0.5 * k2)
        k4 = step * f(arg + k3)
        return arg + (k1 + 2*k2 + 2*k3 + k4) / 6

    remaining = abs(dt_total)
    while remaining > 1e-9:
        h = step_sign * min(h_step, remaining)
        s = rk4(s, h)
        t += h
        remaining -= abs(h)
    return s[0:3]

def check_satrellite_trajectory(satellite_coords):
    fig = plt.figure(figsize=(15, 12))
    ax_3d = fig.add_subplot(projection='3d')
    ax_3d.plot(satellite_coords[0], satellite_coords[1], satellite_coords[2],
               color='red', linewidth=1.5, label='Траектория спутника')
    ax_3d.scatter(satellite_coords[0], satellite_coords[1], satellite_coords[2],
                  color='red', s=12)

    R_earth = 6_378_137.0
    u = np.linspace(0, 2 * np.pi, 60)
    v = np.linspace(0, np.pi, 30)
    xe = R_earth * np.outer(np.cos(u), np.sin(v))
    ye = R_earth * np.outer(np.sin(u), np.sin(v))
    ze = R_earth * np.outer(np.ones_like(u), np.cos(v))
    ax_3d.plot_surface(xe, ye, ze, color='steelblue', alpha=0.25, linewidth=0)

    max_range = np.max(np.abs(satellite_coords)) * 1.05
    ax_3d.set_xlim(-max_range, max_range)
    ax_3d.set_ylim(-max_range, max_range)
    ax_3d.set_zlim(-max_range, max_range)
    ax_3d.set_xlabel('X, м')
    ax_3d.set_ylabel('Y, м')
    ax_3d.set_zlabel('Z, м')
    ax_3d.legend()
    plt.show()

'''_____________________________________________________________________________________________________________________'''
if __name__ == "__main__":                          
    filename = 'BRD400DLR_S_20260010000_01D_MN.rnx.gz'
    satellites = prsc.parse_rinex(filename)          # получение списка словарей спутников из rinex файла
    satellite_coords = np.zeros((3, 196))
    satellite = satellites[0]                        # один опорный момент

    for i in range(satellite_coords.shape[1]):
        new_coords = satellite_position(satellite, t_offset=i * 300)  # каждые 5 минут
        satellite_coords[0][i] = new_coords[0]
        satellite_coords[1][i] = new_coords[1]
        satellite_coords[2][i] = new_coords[2]

    check_satrellite_trajectory(satellite_coords)
