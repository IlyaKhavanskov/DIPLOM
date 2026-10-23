import gzip


def parser_ionex(filename, target_lat: float, target_lon: float) -> float:
    er_lat = 0.4
    exponent = -1  # По умолчанию для большинства IONEX

    with gzip.open(filename, 'rt') as f:
        for line in f:
            if 'LAT/LON1/LON2/DLON/H' in line:
                parts = line.strip().split()

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


if __name__ == '__main__':
    filename = 'ROBR007A00.26I.gz'
    target_lat = 39.5
    target_lon = 1
    parser_ionex(filename, target_lat, target_lon) 