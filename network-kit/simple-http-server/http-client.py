from http import client
from tracemalloc import start
import requests as rq
import requests as rq
import time 

from pathlib import Path
from fastapi import FastAPI

app = FastAPI()

@app.get('/')
async def hello_world():
    return {'hello': 'world'}

@app.get('/respone_time')
async def server_respone_time():
    client_send_time = int (time.time() * 1000)
    respone = rq.get('http://10.0.0.2:8000/respone_time')
    server_recive_time = int(respone.json()['time'])
    client_recive_time = int (time.time() * 1000)
    rsp_time =  (server_recive_time - client_send_time) + (client_recive_time - server_recive_time) 
    print(rsp_time)
    return {'time': rsp_time} 