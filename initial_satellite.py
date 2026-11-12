import compareNew as cm
import parse_rinex as pr
import parser_sp3_fixed as pf

import asyncio
import redis.asyncio as aioredis  
import redis

epochs = '''        2026-11-02 21:45:00.000
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

# satellites_list = cm.count_difference(sp3, rinex,epochs )

# print(satellites_list[0])
# print(sp3['2026-11-02 21:45:00.000'][0])
# sp3['2026-11-02 21:45:00.000'][0] -> один спутник {'R': 'G01', 'x': 13556.964664, 'y': -20478.654256, 'z': -9992.79433, 'Gn': 135.826129}

def find_satellite(sp3, rinex, epochs='2026-11-02 21:45:00.000'):
    glonass = []
    for satellite_sp3 in sp3[epochs]:
        if satellite_sp3['R'].startswith('R'):
            glonass.append(satellite_sp3)
        glonass.sort(key=lambda x: x['Gn'])

    return glonass


async def main():

    rinex = pr.parse_rinex('AGA100RUS_R_20263062115_01D_RN.rnx.gz')
    
    sp3 = pf.parser_sp3('COD0OPSRAP_20263060000_01D_05M_ORB.SP3.gz')
    
    satellites = find_satellite(sp3, rinex, epochs='2026-11-02 21:45:00.000')
    
    print(satellites)
    
    
    async with aioredis.Redis(host='localhost', port=6379, db=0, decode_responses=True) as r:
        # Формируем список корутин (задач) для всех эпох
        tasks = [
            r.hset(satellite['R'],mapping=satellite)
            for satellite in satellites
        ]

        await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())