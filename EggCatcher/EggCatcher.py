import cv2
import numpy as np
import subprocess
import time
import uiautomator2 as u2
from FrameManager import FrameManager
from ScreenRecord import ScreenStream
from ObjectsDetection import ObjectsDetection
from Vision import Vision

# --- CONFIGURAZIONE GLOBALE ---
DEVICE_ID = "emulator-5576"
DEBUG_MODE = True
ORIGINAL_SCREEN_SIZE = (900, 1600)
TARGET_SCREEN_SIZE = (360, 640)

# Percorsi Template
BG_PATH = 'templates/background.PNG'
IS_GIFT_PATH = 'templates/is_gift.PNG'
PLAYER_PATH = 'templates/player.PNG'
DEFEAT_PATH = 'templates/defeat.PNG'

# Parametri di Gioco
PLAYER_Y_SCREEN = 470   # Altezza visiva del player nello schermo ridimensionato
SAFE_MARGIN = 70        # Distanza di sicurezza laterale
FALL_SPEED = 7       # px/frame (stimato)
PAN_SPEED = 5       # px/frame (stimato)
MOVE_THRESHOLD = 5    # Pixel minimi per inviare un nuovo comando move

# --- INIZIALIZZAZIONE OGGETTI ---
vision_is_gift = Vision(IS_GIFT_PATH)
vision_bg = Vision(BG_PATH)
vision_player = Vision(PLAYER_PATH)
vision_defeat = Vision(DEFEAT_PATH)

u = u2.connect(DEVICE_ID)
frame_manager = FrameManager(ORIGINAL_SCREEN_SIZE, TARGET_SCREEN_SIZE)
stream = ScreenStream(TARGET_SCREEN_SIZE)
object_detection = ObjectsDetection()

# Impostazione ROI (Region of Interest) per ottimizzare la ricerca
vision_is_gift.set_roi(288, 335, 64, 66)
vision_bg.set_roi(59, 11, 40, 42)
vision_player.set_roi(1, 462, 359, 28)
vision_defeat.set_roi(180, 415, 102, 38)


def get_center(obj_rect):
    """Calcola il centro (cx, cy) da [x, y, w, h]"""
    x, y, w, h = obj_rect
    return int(x + w // 2), int(y + h // 2)

def draw_rectangles(frame, rects, color=(0, 255, 0), thickness=2):
    """Disegna rettangoli basati su [x, y, w, h] o punti Vision"""
    if rects is not None:
        for r in rects:
            # Gestione compatibilità tra output Vision (punti) e ObjectDetection (rect)
            if len(r) == 2: # È un punto (x, y) da Vision
                x, y = r
                w, h = 50, 50 # Default size o prendi da vision.needle_img.shape
            else: # È un rect [x, y, w, h]
                x, y, w, h = r
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, thickness)

def is_path_safe(start_x, end_x, dangers, pan_speed=PAN_SPEED, fall_speed=FALL_SPEED):
    """
    Controlla collisioni future basandosi sul triangolo spazio-temporale.
    """
    path_min = min(start_x, end_x)
    path_max = max(start_x, end_x)
    
    PAN_WIDTH = 50
    PLAYER_HEIGHT = 30 

    for d in dangers:
        # Estrai coordinate dal nuovo formato [x, y, w, h]
        d_x, d_y = get_center(d)
        
        # 1. FILTRO SPAZIALE: È sulla traiettoria?
        if not (path_min - PAN_WIDTH < d_x < path_max + PAN_WIDTH):
            continue 

        # 2. CALCOLO TEMPORALE
        dist_to_danger_x = abs(d_x - start_x)
        time_pan = dist_to_danger_x / pan_speed
        
        dist_fall = (PLAYER_Y_SCREEN - PLAYER_HEIGHT) - d_y
        
        if dist_fall < 0: continue # Già passato

        time_danger = dist_fall / fall_speed
        
        # 3. VALUTAZIONE COLLISIONE
        # Se il pericolo cade tra 'adesso' e 'appena dopo il mio passaggio' -> BLOCCO
        if time_danger < (time_pan + 6): # Buffer aumentato a 6 frame
            return d_x # X del pericolo bloccante

    return None

def get_desired_target(player_x, eggs):
    """Trova l'uovo migliore (più in basso)"""
    if not eggs:
        return player_x
    
    # Ordina uova per Y (l'elemento [1] di [x,y,w,h] è la y del top-left)
    # Vogliamo quello più in basso (Y maggiore)
    best_egg = max(eggs, key=lambda e: e[1])
    return get_center(best_egg)[0] # Ritorna la X centrale

def decide(player_x, eggs, dangers):
    """Logica decisionale principale"""
    # 1. Target ideale (Uovo)
    target_x = get_desired_target(player_x, eggs)

    # 2. Controllo Sicurezza (Evita Bombe)
    block_danger_x = is_path_safe(player_x, target_x, dangers)

    if block_danger_x is not None:
        # Se c'è un blocco, fermati prima del blocco
        print(f"[DECISION] Path blocked by danger at {block_danger_x}")
        if block_danger_x > player_x:
            target_x = block_danger_x - SAFE_MARGIN
        else:
            target_x = block_danger_x + SAFE_MARGIN
            
    # Assicurati che target_x sia entro i limiti dello schermo
    target_x = max(20, min(target_x, TARGET_SCREEN_SIZE[0] - 20))
    
    return target_x

def main():
    frame_count = 0
    
    # Stato del bot
    is_touch_active = False
    prev_target_x = None
    
    print("[SYSTEM] Bot started. Waiting for game...")

    while True:
        # --- 1. CATTURA ---
        frame = stream.read()
        if frame is None: continue
        frame_count += 1

        # --- 2. ANALISI STATO (UI) ---
        # Usiamo i template match per capire dove siamo
        bg_points = vision_bg.find_object(frame, threshold=0.85)
        defeat_points = vision_defeat.find_object(frame, threshold=0.95)
        
        is_playing = (bg_points is not None)
        is_game_over = (defeat_points is not None)

        # Disegno debug UI
        if is_game_over: draw_rectangles(frame, defeat_points, (0,0,255))
        
        # --- 3. LOGICA DI GIOCO ---
        if is_playing and not is_game_over:
            
            # A. Trova il Player
            player_matches = vision_player.find_object(frame, threshold=0.55)
            
            if player_matches:
                # Calcola centro player
                px, py = player_matches[0]
                pw, ph = vision_player.needle_img.shape[1], vision_player.needle_img.shape[0]
                player_x = int(px + pw // 2)
                
                # Disegna player
                cv2.rectangle(frame, (px, py), (px+pw, py+ph), (255, 255, 0), 2)
                
                # B. Gestione Touch INIZIALE
                if not is_touch_active:
                    print("[ACTION] Game Start -> Touch Down")
                    real_px = frame_manager.map_x_to_original(player_x)
                    u.touch.down(real_px, 1200) # 1200 è un Y fisso sicuro nell'area touch
                    is_touch_active = True
                    prev_target_x = player_x

                # C. Rileva Uova e Bombe
                eggs, dangers = object_detection.detect_objects(frame)
                
                # Disegno debug oggetti
                draw_rectangles(frame, eggs, (0, 255, 255))   # Giallo per uova
                draw_rectangles(frame, dangers, (0, 0, 255))  # Rosso per pericoli

                # D. Prendi Decisione
                target_x = decide(player_x, eggs, dangers)
                
                # Visualizza intenzione
                cv2.line(frame, (player_x, PLAYER_Y_SCREEN), (int(target_x), PLAYER_Y_SCREEN), (255, 0, 255), 2)
                cv2.circle(frame, (int(target_x), PLAYER_Y_SCREEN), 5, (255, 0, 255), -1)

                # E. Esegui Movimento (Solo se necessario)
                # Muoviamo solo se la distanza è significativa per evitare spam di comandi
                if abs(target_x - prev_target_x) > MOVE_THRESHOLD:
                    
                    real_target_x = frame_manager.map_x_to_original(target_x)
                    
                    # Usa touch.move perché il dito è già giù
                    u.touch.move(real_target_x, 1200)
                    
                    prev_target_x = target_x # Aggiorna l'ultima posizione inviata
            
            else:
                print("[WARNING] Playing but Player lost!")
                # Se perdiamo il player per troppi frame, forse dovremmo resettare il touch?
                # Per ora lasciamo correre, potrebbe essere un glitch visivo di un frame.

        # --- 4. GESTIONE FINE GIOCO / PAUSA ---
        else:
            if is_touch_active:
                print("[ACTION] Game Over/Menu -> Release Touch")
                if prev_target_x:
                    real_last_x = frame_manager.map_x_to_original(prev_target_x)
                    u.touch.up(real_last_x, 1200)
                else:
                    u.touch.up(450, 1200) # Release generico al centro
                is_touch_active = False
                prev_target_x = None

            if is_game_over:
                cv2.putText(frame, "GAME OVER", (50, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 3)
  
            else:
                # Controllo Gift/Home solo se non sto giocando né ho perso
                is_gift_points = vision_is_gift.find_object(frame, threshold=0.9)
                if is_gift_points:
                    print("[STATE] In Home / Gift screen")

            

      
        
        


        # Salva il frame come file PNG o JPG
        #cv2.imwrite(f"debug_shapes\debug{frame_count}.png", frame)
        # --- 5. VISUALIZZAZIONE ---
        cv2.imshow("Egg Catcher Bot AI", frame)
        if cv2.waitKey(1) == ord('q'):
            break

if __name__ == "__main__":
    main()