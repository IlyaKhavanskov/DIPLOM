from quart import Quart, jsonify
import asyncio
import sys

# Создаем экземпляр приложения
app = Quart(__name__)

@app.get("/")
async def index():
    # Асинхронный route handler
    return 'приложение работает'


@app.route('/h')
def hello_world():
    return 'Hello, World!'


@app.route('/run-process')
async def run_process():

    x_in = 2850631.2464619204 
    y_in =  2195281.5913748345 
    z_in =  5248946.485037155

    
    process = await asyncio.create_subprocess_exec(
        ['python', 'base_station.py', str(x_in), str(y_in),str(z_in)],  
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout_bytes, stderr_bytes = await process.communicate()

    encoding = sys.stdout.encoding or 'utf-8'

    
    stdout = stdout_bytes.decode(encoding)
    stderr = stderr_bytes.decode(encoding)

    return stdout
    
if __name__ == "__main__":
    
    app.run()


    
