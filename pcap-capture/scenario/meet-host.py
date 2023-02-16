import pyvirtualcam as pvc
import tomli
import numpy as np
# read config file
with open('config.toml') as f:
    config = tomli.load(f)


def main():
    with pvc.Camera(width=640, height=480, fps=20) as cam:
        print(f'Using virtual camera: {cam.device}')
        while True:
            frame = cam.frames_sent
            cam.send(np.zeros((480, 640, 4), np.uint8))
            print(f'Sent frame {frame}')