import gzip
import io
import unlzw3 



def parser_ionex(filename, target_lat: float, target_lon: float) -> float:
    er_lat = 1.3
    exponent = -1  # По умолчанию для большинства IONEX
    TECs = {
        # словарь  эпоха - TEC
    }
    with (gzip.open(filename, 'rt') if isinstance(filename, str) else filename) as f:
        for line in f:
            # print(line)
            #  2026    11    10     0     0     0                        EPOCH OF CURRENT MAP
            if 'EPOCH OF FIRST MAP' in line :
                string  = line.strip().split()
                # 2026    11    10     0     0     0                        EPOCH OF FIRST MAP 
                first_epoch = f' год {string[0]} месяц {string[1]} \
                    число {string[2]} час {string[3]} минута {string[4]} секунда {string[5]}'
                first_epoch = " ".join(first_epoch.split())
                # print('первая эпоха ',first_epoch)

            if 'EPOCH OF last MAP' in line :
                string  = line.strip().split()
                # 2026    11    10    23    59    24                        EPOCH OF LAST MAP 
                last_epoch = f' год {string[0]} месяц {string[1]} \
                    число {string[2]} час {string[3]} минута {string[4]} секунда {string[5]}'
                last_epoch = " ".join(last_epoch.split())
                # print('последяя эпоха ',last_epoch)

            if 'EPOCH OF CURRENT MAP' in line :
            #   2026    11    10     0     0     0                        EPOCH OF CURRENT MAP
                string  = line.strip().split()
                current_epoch = f' год {string[0]} месяц {string[1]} \
                                число {string[2]} час {string[3]} минута {string[4]} секунда {string[5]}'
                current_epoch = " ".join(current_epoch.split())
                TECs[current_epoch] = None


            if 'LAT/LON1/LON2/DLON/H' in line:
                # parts = line.strip().split()
                # parts = [line[i:i+10] for i in range(0, 50, 10)]
                parts = line[:60].replace('-', ' -').split()
                # print(repr(parts[:4]))
                if abs(float(parts[0]) - target_lat) < er_lat:
                    lat = float(parts[0])
                    lon1 = float(parts[1])
                    lon2 = float(parts[2])
                    dlon = float(parts[3])

                    if lon1 <= target_lon <= lon2:
                        idx = int(round((target_lon - lon1) / dlon))

                        i = 0

                        # читаем следующие строки, там идут значения
                        for data_line in f:
                            if (
                                'LAT/LON1/LON2/DLON/H' in data_line
                                or 'END OF TEC MAP' in data_line
                                or 'START OF TEC MAP' in data_line
                            ):
                                break

                            for element in data_line.strip().split():
                                if i == idx:
                                    value = float(element) * (10 ** exponent)
                                    # print(value)
                                    TECs[current_epoch] = value

                                i += 1

    return TECs

def get_TEC(filename, target_lat, target_lon):
    
    if filename.endswith('.gz'):
        tec = parser_ionex(filename, target_lat, target_lon) 

        tec_values = list( tec.values() )
        time_step = 1 # минута
        current_time = 0
        hour = 60
        start_val = tec_values[0]
        end_val  = tec_values[1]

        for current_time in range(0,hour,time_step):
            progress = current_time / hour
            current_val = start_val + (end_val - start_val) * progress
            yield current_val

    elif filename.endswith('.Z'):
        with open(filename, 'rb') as f:
            data = unlzw3.unlzw(f.read()).decode('ascii')
        filename = io.StringIO(data)

        tec = parser_ionex(filename, target_lat, target_lon)
        tec_values = list( tec.values() )
        time_step = 1 # минута
        current_time = 0
        hour = 60
        start_val = tec_values[0]
        end_val  = tec_values[1]
        
        for current_time in range(0,hour,time_step):
            progress = current_time / hour
            current_val = start_val + (end_val - start_val) * progress
            yield current_val

if __name__ == '__main__':
    filename = 'COD0OPSP0D_20263180000_01D_01H_GIM.INX.gz'
    # filename = 'ROBR007A00.26I.gz'
    target_lat = 52.5
    target_lon = -13
    # filename = 'upcg3140.26i.Z'
    TEC = get_TEC(filename, target_lat, target_lon)
    # for key, value in TEC.items():
    #     print(f'время {key} значение {value}')

    for i in range(3):
        print(next(TEC))
# создаем бд
    #     r = redis.Redis(
    # host='localhost',
    # port=6379,
    # db=0,
    # decode_responses=True
    #     )


    # while True:
    #     try:
    #         TEC = get_TEC(filename, target_lat, target_lon)

    #         for key, value in TEC.items():
    #             if value is not None:
    #                 r.hset('TEC', key, value)

    #         print('Данные TEC записаны в Redis')

    #     except Exception as e:
    #         print('Ошибка:', e)

    #     time.sleep(60)




