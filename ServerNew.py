import sys
import asyncio
from quart import Quart, request, Response
import coordinates_pb2 as c_pb2
import satellites_pb2 as s_pb2

app = Quart(__name__)
lst_satellites = []

@app.route('/correct', methods=['POST'])
async def get_xyz():
    coords = c_pb2.Coordinates()
    coords.ParseFromString(await request.get_data())

    proc = await asyncio.create_subprocess_exec(
        sys.executable, 'base_station.py',
        str(coords.x), str(coords.y), str(coords.z),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate()

    if proc.returncode != 0:
        return Response(err, status=500, mimetype='text/plain')

    line = out.decode().strip()
    if not line:
        return Response("Base station returned no correction",
                        status=500, mimetype='text/plain')

    dX, dY, dZ = map(float, line.split())
    delta = c_pb2.Coordinates(x=dX, y=dY, z=dZ)
    return Response(delta.SerializeToString(),
                    mimetype='application/x-protobuf')

@app.route('/satellites', methods=['POST'])
async def get_satellites():
    global lst_satellites
    sats = s_pb2.SatelliteList()
    sats.ParseFromString(await request.get_data())
    lst_satellites = list(sats.names)
    return Response(b"OK", status=200, mimetype='text/plain')

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5001
    app.run(host="127.0.0.1", port=port, debug=True)