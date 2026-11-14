import gzip
import io
import unlzw3 

def parser_ionex(filename, target_lat: float, target_lon: float) -> float:
    er_lat = 1.3
    exponent = -1  # По умолчанию для большинства IONEX
    
    with (gzip.open(filename, 'rt') if isinstance(filename, str) else filename) as f:
        for line in f:
            print(line)
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
                                    return value

                                i += 1

    return float('nan')

def get_TEC(filename):
    
    target_lat = 39.5
    target_lon = 1
    if filename.endswith('.gz'):
        tec = parser_ionex(filename, target_lat, target_lon) 
        return tec
    elif filename.endswith('.Z'):
        with open(filename, 'rb') as f:
            data = unlzw3.unlzw(f.read()).decode('ascii')
        filename = io.StringIO(data)
        tec = parser_ionex(filename, target_lat, target_lon)
        return tec



if __name__ == '__main__':
    
    # filename = 'ROBR007A00.26I.gz'
    filename = 'upcg3140.26i.Z'
    get_TEC(filename)