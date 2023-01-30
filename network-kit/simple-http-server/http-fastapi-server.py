from pydantic import BaseModel
import uvicorn

from pathlib import Path
from fastapi import FastAPI
from fastapi import Request, Response
from fastapi import Header
from fastapi.templating import Jinja2Templates

from fastapi import File, UploadFile
from fastapi.responses import FileResponse

from typing import Union

import time, os
import asyncio
import threading

app = FastAPI()
templates = Jinja2Templates(directory="templates")
CHUNK_SIZE = 1024*1024
video_path = Path("Spring_Blender_Open_Movie.webm")

temp_file_queue = asyncio.Queue()

def generate_big_file(filename, size=1024):
    '''
        Create random file with name and
        size in unit MB
    '''
    with open(f'{filename}', 'wb') as f:
        f.seek(1024 * 1024 * size -1)
        f.write(str.encode("0"))

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.htm", context={"request": request})

@app.get('/respone_time')
async def respone_time():
    current_ms = int (time.time() * 1000)
    return {'time': current_ms}


@app.get("/video")
async def video_endpoint(range: str = Header(None)):
    start, end = range.replace("bytes=", "").split("-")
    start = int(start)
    end = int(end) if end else start + CHUNK_SIZE
    with open(video_path, "rb") as video:
        video.seek(start)
        data = video.read(end - start)
        filesize = str(video_path.stat().st_size)
        headers = {
            'Content-Range': f'bytes {str(start)}-{str(end)}/{filesize}',
            'Accept-Ranges': 'bytes'
        }
        return Response(data, status_code=206, headers=headers, media_type="video/mp4")


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    id_filename = str(int(time.time()*10**6))
    file_path = f'temp/{id_filename}'

    try:
        contents = await file.read()
        with open('test', 'wb') as f:
            f.write(file_path)
    except Exception:
        return {"message": "There was an error uploarding the file"}
    finally:
        await file.close()
    
    task = threading.Thread(target=remove_file_after_download, args=(file_path, 1))
    task.daemon = True
    task.start()

    return {"message": f"Successfuly uploaded {file.filename}"}


@app.get('/download')
async def download_file():
    id_filename = str(int(time.time()*10**6))
    file_path = f'temp/{id_filename}'
    generate_big_file(file_path, 100)

    task = threading.Thread(target=remove_file_after_download, args=(file_path,))
    task.daemon = True
    task.start()

    return FileResponse(path=file_path, filename=file_path)

@app.get('/download/{size}')
async def download_file_with_size(size: int):
    id_filename = str(int(time.time()*10**6))
    file_path = f'temp/{id_filename}'
    generate_big_file(file_path, size)
    
    task = threading.Thread(target=remove_file_after_download, args=(file_path,))
    task.daemon = True
    task.start()

    return FileResponse(path=file_path, filename=file_path); 

def remove_file_after_download(filename, timer=60):
    '''
        remove created file for client to download
        when timer end
    '''
    time.sleep(timer)
    os.remove(filename)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)