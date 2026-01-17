import cv2
import numpy as np
import time

class Vision:

    needle_img = None

    x_roi, y_roi, w_roi, h_roi = None, None, None, None

    is_roi_default = True

    def __init__(self, needle_img_path = None):
        if(needle_img_path):
            self.needle_img = cv2.imread(needle_img_path, cv2.IMREAD_COLOR)

    def set_roi(self, x_roi, y_roi, w_roi, h_roi):
        self.x_roi, self.y_roi, self.w_roi, self.h_roi = x_roi, y_roi, w_roi, h_roi
        self.is_roi_default = False

    def find_object(self, heystack_img, threshold=0.8):
        start_time = time.perf_counter()

        # 1. Applicazione ROI
        if not self.is_roi_default:
            heystack_img = heystack_img[self.y_roi:self.y_roi + self.h_roi, 
                                        self.x_roi:self.x_roi + self.w_roi]

        # 2. Match Template
        result = cv2.matchTemplate(heystack_img, self.needle_img, cv2.TM_CCOEFF_NORMED)
    
        # 3. Trova il valore massimo e la sua posizione
        # minMaxLoc restituisce: (valore_min, valore_max, pos_min, pos_max)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
    
        points = []
    
        # 4. Verifica se il match migliore supera la soglia
        if max_val >= threshold:
            best_x, best_y = max_loc
        
            # Converte coordinate ROI-relative in coordinate originali
            if not self.is_roi_default:
                best_x += self.x_roi
                best_y += self.y_roi
            
            points = [(int(best_x), int(best_y))]

        elapsed = (time.perf_counter() - start_time) * 1000
        #print(f"[SPEED] for find object {elapsed:.2f} ms") 

        if len(points) > 0:
            return points
        else:
            return None
