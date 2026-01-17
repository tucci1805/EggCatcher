import subprocess
import numpy as np
import cv2
import threading
import queue
import time


TIME_LIMIT = 179

class ScreenStream:
    def __init__(self, screen_size):

        self.width, self.height = screen_size

        self.frame_queue = queue.Queue(maxsize=1) # Teniamo solo 1 frame per evitare accumuli

        self.stopped = False
        
        self.start()
        
    def launch_ffmpeg(self):
        return subprocess.Popen(
                [
                    'ffmpeg',
                    '-probesize', '32',
                    '-analyzeduration', '0',
                    '-flags', 'low_delay',
                    #'-use_wallclock_as_timestamps', '1',
                    #'-vsync', 'drop',
                    '-f', 'h264',                 # Forza formato input
                    '-i', 'pipe:0',               # Legge dallo stdin (adb)
                    #'-vf', f'scale={WIDTH_DST}:{HEIGHT_DST}',
                    '-f', 'rawvideo',
                    '-pix_fmt', 'bgr24',
                    '-vcodec', 'rawvideo', 
                    '-'  
                ],stdin=self.adb_process.stdout,stdout=subprocess.PIPE,bufsize=10**7)

    def launch_adb(self):
        adb_command = (
                        f"while true; do "
                        f"screenrecord --size {self.width}x{self.height} --bit-rate 6M  --time-limit {TIME_LIMIT} --output-format=h264 -;"
                        f"done"
                    )
        return subprocess.Popen(
        [
            'adb', 'exec-out', adb_command
        ],
        stdout=subprocess.PIPE,
        bufsize=10**7
    )
        
        
    def start(self):

        self.adb_process = self.launch_adb()
        self.ffmpeg_process = self.launch_ffmpeg()
        
        self.start_time = time.time()
        
        threading.Thread(target=self.update, daemon=True).start()
        return self

    
    def update(self):
        frame_size = self.width * self.height * 3
        
        while not self.stopped:
            elapsed = time.time() - self.start_time
            try:
                # Legge i dati dallo stdout
                raw_frame = self.ffmpeg_process.stdout.read(frame_size)

                # Converte e aggiorna la coda
                frame = np.frombuffer(raw_frame, dtype='uint8').reshape((self.height, self.width, 3)).copy()
                
                if not self.frame_queue.empty():
                    try: self.frame_queue.get_nowait()
                    except queue.Empty: pass
                self.frame_queue.put(frame)

            except Exception as e:
                print(f"Errore: {e}")
                time.sleep(0.01)

    def read(self):
        return self.frame_queue.get() if not self.frame_queue.empty() else None

