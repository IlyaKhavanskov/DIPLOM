import gzip

def parser_sp3(filename):
    epochs = {}  # [ИСПРАВЛЕНИЕ 1] Словарь создаем ДО цикла!
    PRs = []     
    current_epoch = None  
    
    with gzip.open(filename, 'rt') as f:
        for line in f:
            # * Год Месяц День Час Минута Секунда
            if line.strip() and line.startswith('*'):
                string = line.split()
                current_epoch = f'Год {string[1]} месяц {string[2]} день {string[3]} час {string[4]} минута {string[5]} секунда {string[6]}'
                # print(current_epoch)
                
                # [ИСПРАВЛЕНИЕ 2] Создаем НОВЫЙ пустой список для спутников этой эпохи
                epochs[current_epoch] = []
                
            elif line.strip() and line.startswith('PR'):
                string = line.split()
                
            
                if current_epoch is None:
                    continue
                    
                satellite = {
                    'R': string[0][1:],
                    "x": float(string[1]),   
                    "y": float(string[2]),
                    "z": float(string[3]),
                    "Gn": float(string[4])
                }
                PRs.append(satellite) # Накапливаем в общий список (если он вам еще нужен)
                
                # [ИСПРАВЛЕНИЕ 3] Добавляем спутник в список именно ТЕКУЩЕЙ эпохи
                epochs[current_epoch].append(satellite)       
                
    return epochs # Теперь вернется полноценный словарь {эпоха: [список спутников]}

if __name__ == '__main__':
    filename = 'COD0OPSRAP_20263060000_01D_05M_ORB.SP3.gz'
    result = parser_sp3(filename)
    
    print(f"\nВсего обработано эпох (временных срезов): {len(result)}")
    
    # вывод для проверки:  первая эпоха и первые два спутника
    # if result:
    #     first_epoch_key = list(result.keys())[0]
    #     print(f"\nПример данных для эпохи '{first_epoch_key}':")
    #     for sat in result[first_epoch_key][:2]:
    #         print(sat)


    print(result.keys())
# parse_rinex.py, строка 6 — раскомментировать:
from datetime import datetime

