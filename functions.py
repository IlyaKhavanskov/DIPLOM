import math
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import copy

# импортирование собственных модулей
# import parse_ionix as pi
import parsing_SATELLITES_COORDS as pi
import parsing_SATELLITES_COORDS as prsc

# === Константы ===
a = 6378137.0
b = 6356752.314
alpha = 1/298.3
PI = math.pi
e = math.sqrt((a**2 - b**2) / a**2)
c = 299792458
W3 = 7.292115e-5
mu = 3.986004418e14
c20 = -1082.63e-6
R3 = 6378137.0
f = 1602 * 10 ** 6
dT = 0.0


def BLH_to_ECEF(h, B, L):
    global a, b, e
    B = math.radians(B)
    L = math.radians(L)
    e2 = e**2
    sinB = math.sin(B)
    N = a / math.sqrt(1 - e2 * sinB * sinB)
    x = (N + h) * math.cos(B) * math.cos(L)
    y = (N + h) * math.cos(B) * math.sin(L)
    z = (N * (1 - e2) + h) * sinB
    return x, y, z


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


def location(NAP, satellites, vtec_tecu=10.0, change_flag=False):
    global dT, c, W3
    sigma_noise = 0.173
    n = len(satellites)
    D_obs = np.zeros(n)
    for i in range(n):
        random_error = np.random.normal(0, sigma_noise)
        geom = math.sqrt((NAP[0]-satellites[i,0])**2 +
                         (NAP[1]-satellites[i,1])**2 +
                         (NAP[2]-satellites[i,2])**2)
        if change_flag:
            # Ровер: используем переданный (возможно, устаревший) VTEC
            iono = iono_delay(NAP[0], NAP[1], NAP[2],
                              satellites[i,0], satellites[i,1], satellites[i,2],
                              vtec_tecu)
        else:
            # Базовая станция: читаем свежий VTEC из файла (эпоха t0)
            base_vtec = pi.parser_ionex('ROBR007A00.26I.gz', 60.5, -15)
            iono = iono_delay(NAP[0], NAP[1], NAP[2],
                              satellites[i,0], satellites[i,1], satellites[i,2],
                              base_vtec)
        tropo_delay = troposphere_delay(NAP)
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


def troposphere_delay(NAP):
    x, y, z = NAP[0], NAP[1], NAP[2]
    BLH = ECEF_to_BLH(x, y, z)
    h_m  = BLH[2]
    h_km = h_m / 1000.0
    phi  = math.radians(BLH[0])
    P  = 1013.25 * (1 - 0.0000226 * h_m) ** 5.225
    T  = 291.16  - 0.00650 * h_m
    H  = 50.0    * math.exp(-0.0006396 * h_m)
    ZHD = (0.0022767 * P) / (1 - 0.00266 * math.cos(2 * phi) - 0.00028 * h_km)
    Rd  = 287.054
    g_m = 9.784 * (1 - 0.00266 * math.cos(2 * phi) - 0.00028 * h_km)
    Tm  = 70.2  + 0.72 * T
    e0  = (H / 100.0) * 6.112 * math.exp(17.67 * (T - 273.15) / (T - 29.65))
    K3  = 3.701e5
    ZWD = 1e-6 * (Rd / g_m) * (K3 / Tm) * (e0 / 3.7)
    T_troposphere = (ZHD + ZWD) / c
    return T_troposphere


def iono_delay(X_nap, Y_nap, Z_nap, X_s, Y_s, Z_s, vtec_tecu=10.0):
    h = 450000.0  # 450 км
    r = np.array([X_s - X_nap, Y_s - Y_nap, Z_s - Z_nap])
    r_norm = np.linalg.norm(r)
    if r_norm < 1e-9:
        return 0.0
    n = np.array([X_nap, Y_nap, Z_nap])
    n_norm = np.linalg.norm(n)
    if n_norm < 1e-9:
        return 0.0
    n = n / n_norm
    
    sin_E = np.dot(r, n) / r_norm
    sin_E = max(-1.0, min(1.0, sin_E))
    E = math.asin(sin_E)
    
    sinE_ = R3 / (R3 + h) * math.cos(E)
    sinE_ = max(1e-6, sinE_)
    M_E = 1.0 / sinE_
    
    # ВАЖНО: VTEC в TECU переводим в эл/м^2 (*1e16)
    TEC = vtec_tecu * 1e16
    d_R = 40.3 * TEC * M_E / (f * f)
    return d_R


def consumer_movement(X_nap, Y_nap, Z_nap, type_of_movement='line', delta_T=1):
    if type_of_movement == 'line':
        v_x = 2
        X_nap = X_nap + v_x * delta_T
    elif type_of_movement == 'circular':
        R = 1000
        omega = 0.01
        angle = omega * delta_T
        X_nap = R * math.cos(angle)
        Y_nap = R * math.sin(angle)
    elif type_of_movement == 'random':
        import random
        X_nap += random.gauss(0, 0.1)
        Y_nap += random.gauss(0, 0.1)
        Z_nap += random.gauss(0, 0.1)
    return X_nap, Y_nap, Z_nap


def satellite_position(satellite, h_step=60.0, t_offset=0):
    tb = satellite['tb']
    if isinstance(tb, (list, np.ndarray)):
        tb = tb[0]
    if isinstance(tb, str):
        tb_sec = int(tb.split()[0]) * 3600 + int(tb.split()[1]) * 60
    else:
        tb_sec = int(tb)
    t_sat_prev = tb_sec + float(t_offset)
    t_sat_prev = t_sat_prev - 0.071
    tc = satellite["tc"][0] if isinstance(satellite["tc"], (list, np.ndarray)) else satellite["tc"]
    Gn = satellite["Gn"][0] if isinstance(satellite["Gn"], (list, np.ndarray)) else satellite["Gn"]
    t_glonass = t_sat_prev + tc - Gn * (t_sat_prev - tb_sec)

    x0 = satellite['x'];  y0 = satellite['y'];  z0 = satellite['z']
    vx0 = satellite['Vx']; vy0 = satellite['Vy']; vz0 = satellite['Vz']

    if isinstance(x0, (list, np.ndarray)): x0 = x0[0]
    if isinstance(y0, (list, np.ndarray)): y0 = y0[0]
    if isinstance(z0, (list, np.ndarray)): z0 = z0[0]
    if isinstance(vx0, (list, np.ndarray)): vx0 = vx0[0]
    if isinstance(vy0, (list, np.ndarray)): vy0 = vy0[0]
    if isinstance(vz0, (list, np.ndarray)): vz0 = vz0[0]

    ax_ext = satellite['ax'][0] if isinstance(satellite['ax'], (list, np.ndarray)) else satellite['ax']
    ay_ext = satellite['ay'][0] if isinstance(satellite['ay'], (list, np.ndarray)) else satellite['ay']
    az_ext = satellite['az'][0] if isinstance(satellite['az'], (list, np.ndarray)) else satellite['az']

    if max(abs(vx0), abs(vy0), abs(vz0)) < 100:
        vx0 *= 1000.0; vy0 *= 1000.0; vz0 *= 1000.0
    if 0 < max(abs(ax_ext), abs(ay_ext), abs(az_ext)) < 1:
        ax_ext *= 1000.0; ay_ext *= 1000.0; az_ext *= 1000.0

    s = np.array([x0, y0, z0, vx0, vy0, vz0], dtype=float)
    t = tb_sec
    dt_total = t_glonass - tb_sec
    step_sign = 1.0 if dt_total >= 0 else -1.0
    h_step = abs(float(h_step))

    def f(state):
        x, y, z, vx, vy, vz = state
        r = math.sqrt(x**2 + y**2 + z**2)
        coeff = -1.5 * c20 * mu * (R3**2) / (r**5)
        ax_grav = -mu * x / (r**3) + coeff * x * (1 - 5 * (z**2) / (r**2))
        ay_grav = -mu * y / (r**3) + coeff * y * (1 - 5 * (z**2) / (r**2))
        az_grav = -mu * z / (r**3) + coeff * z * (3 - 5 * (z**2) / (r**2))
        return np.array([vx, vy, vz, ax_grav + ax_ext, ay_grav + ay_ext, az_grav + az_ext])

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
    return s


if __name__ == "__main__":
    pass