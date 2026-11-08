import gzip

def parser_sp3(filename):
    epochs = {}  
    PRs = []     
    current_epoch = None  
    
    with gzip.open(filename, 'rt') as f:
        for line in f:
            # * Год Месяц День Час Минута Секунда
            if line.strip() and line.startswith('*'):
                string = line.split()
                current_epoch = f'{int(string[1]):04d}-{int(string[2]):02d}-{int(string[3]):02d} {int(string[4]):02d}:{int(string[5]):02d}:{float(string[6]):06.3f}'
                

                epochs[current_epoch] = []
                
            elif line.strip() and line.startswith('P'):
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
                PRs.append(satellite) # 

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


    print(f'Всего обработано эпох: {len(result)}')
# parse_rinex.py, строка 6 — раскомментировать:
from datetime import datetime

