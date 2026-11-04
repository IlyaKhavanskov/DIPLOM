# log.info(f"{request.remote_addr} | {user.x} | {user.y} |{user.z} | {x_pr} | {y_pr} | {z_pr} | {dx} | {dy} | {dz}")
import user_class as us
import matplotlib.pyplot as plt
import statistics
import numpy as np

error_x = []
error_y = []
error_z = []

raw_geoposition = {
        'x': [],
        'y': [],
        'z': []
}

geodez_geoposition = {
        'x': [],
        'y': [],
        'z': []    
}

error_vector = {
        'dx': [],
        'dy': [],
        'dz': [] 
}

user_ip = set()
user_dict = {}

with open('user_data.log','r', encoding='utf-8' ) as file:
    for line in file:
        
        columns = line.strip().split('|') # список строк

        for colomn in columns:
            print(colomn)
            
        if columns[1] not in user_ip :
            user_ip.add(columns[1])
            user = us.User() # создаем пользователя
            user.ip = columns[1]
            user_dict[columns[1]  
                    #   ip пользователя
                    ] = user # сам пользователь

            setattr(user,
                    'raw_geoposition' , 
                        {
                            'x': [columns[2]],
                            'y': [columns[3]],
                            'z': [columns[4]]
                        }
                    )

            setattr(user,
                        'geodez_geoposition' , 
                            {
                                'x': [columns[5]],
                                'y': [columns[6]],
                                'z': [columns[7]]
                            }
                    )

            setattr(user,
                    'error_vector' , 
                        {
                            'dx': [columns[8]],
                            'dy': [columns[9]],
                            'dz': [columns[10]]
                        }
                    )
            # print(columns[1])
        else:
            # columns[1] - это ip
            user = user_dict[columns[1]]

            user.raw_geoposition['x'].append(columns[2])
            user.raw_geoposition['y'].append(columns[3])
            user.raw_geoposition['z'].append(columns[4])

            user.geodez_geoposition['x'].append(columns[5])
            user.geodez_geoposition['y'].append(columns[6])
            user.geodez_geoposition['z'].append(columns[7])

            user.error_vector['dx'].append(columns[8])
            user.error_vector['dy'].append(columns[9])
            user.error_vector['dz'].append(columns[10])


# print(*user_ip)
first_user = next(iter(user_ip))
print(first_user)

raw_x = np.array(user_dict[first_user].raw_geoposition['x'], dtype=float )
pr_x = np.array(user_dict[first_user].geodez_geoposition['x'], dtype=float )


raw_y = np.array(user.raw_geoposition['y'], dtype=float)
pr_y = np.array(user.geodez_geoposition['y'], dtype=float)
    
raw_z = np.array(user.raw_geoposition['z'], dtype=float)
pr_z = np.array(user.geodez_geoposition['z'], dtype=float)

if len(raw_x) == len(pr_x) and len(raw_x) > 0:
        err_x = np.abs(raw_x - pr_x)
        err_y = np.abs(raw_y - pr_y)
        err_z = np.abs(raw_z - pr_z)

        print(f"\n📉 Средние абсолютные ошибки:")
        print(f"   X: {np.mean(err_x):.4f}")
        print(f"   Y: {np.mean(err_y):.4f}")
        print(f"   Z: {np.mean(err_z):.4f}")
        
        print(f"\n📈 Среднеквадратичные отклонения (RMS):")
        print(f"   X: {np.sqrt(np.mean(err_x**2)):.4f}")
        print(f"   Y: {np.sqrt(np.mean(err_y**2)):.4f}")
        print(f"   Z: {np.sqrt(np.mean(err_z**2)):.4f}")


# # Данные для графика
# categories = ['', 'B', 'C']
# values = [10, 24, 15]

# # Создание и показ столбчатой диаграммы
# plt.bar(categories, values)
# plt.show()

