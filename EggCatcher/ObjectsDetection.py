import numpy as np

import cv2 as cv
import time
import os

class ObjectsDetection:

    

    @staticmethod
    def detect_objects(frame):

        egg_lower = (12, 36, 160)
        egg_upper = (16, 108, 255)

        dark_egg_lower = (12, 136, 206)
        dark_egg_upper = (16, 165, 226)

        tomato_lower = (0, 160, 120)
        tomato_upper = (6, 255, 255)

        carrot_lower = (7, 238, 210)
        carrot_upper = (24, 255, 255)

        dangers = []
        eggs = []

        time_start = time.time()

        hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
        hsv[0:100, :] = 0
        ####### FATTO #######
        ##   altri test: maschera del movimento abbinata a maschera colore, operazioni morfologiche solo su maschera finale.



        #------ EGG MASKING ------#
        egg_mask = cv.inRange(hsv, egg_lower, egg_upper)
        dark_egg_mask = cv.inRange(hsv, dark_egg_lower, dark_egg_upper)

        dark_egg_mask = cv.morphologyEx(dark_egg_mask,  cv.MORPH_OPEN,  np.ones((7,7), np.uint8), iterations=2)
        dark_egg_mask = cv.dilate(dark_egg_mask, np.ones((7,7), np.uint8) , iterations=2)

        eggs_mask = cv.bitwise_or(dark_egg_mask, egg_mask)

        kernel = np.ones((7, 7), np.uint8)

        eggs_mask = cv.morphologyEx(eggs_mask,  cv.MORPH_OPEN,  kernel, iterations=2)
        eggs_mask = cv.dilate(eggs_mask, np.ones((7,7), np.uint8) , iterations=1)

        
        #------ DANGERS MASKING ------#
        tomato_mask = cv.inRange(hsv, tomato_lower, tomato_upper)
        carrot_mask = cv.inRange(hsv, carrot_lower, carrot_upper)

        dangers_mask = cv.bitwise_or(tomato_mask, carrot_mask)

        kernel = np.ones((5, 5), np.uint8)
        
        dangers_mask = cv.morphologyEx(dangers_mask,  cv.MORPH_OPEN,  kernel, iterations=2)
        dangers_mask = cv.dilate(dangers_mask, np.ones((5,5), np.uint8) , iterations=1)



        final_mask = cv.bitwise_or(dangers_mask, eggs_mask)
            
        eggs_countours = cv.findContours(eggs_mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        dangers_countours = cv.findContours(dangers_mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)


        for cnt in eggs_countours[0]:
            x, y, w, h = cv.boundingRect(cnt)

            center = (int(x + w/2), int(y + h/2))

            cv.drawContours(frame, [cnt], -1, (0, 255, 0), 2)
            cv.circle(frame, center, 5, (0,0,255), -1)
            cv.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

            area = cv.contourArea(cnt)
            print(f"Egg area: {area}")

            if area < 800:
                continue
            eggs.append([x,y,w,h])

        for cnt in dangers_countours[0]:
            x, y, w, h = cv.boundingRect(cnt)
            center = (int(x + w/2), int(y + h/2))

            cv.drawContours(frame, [cnt], -1, (0, 255, 0), 2)
            cv.circle(frame, center, 5, (0,0,255), -1)
            cv.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

            dangers.append([x,y,w,h])

        #cv.imshow("Mask", final_mask)
        #cv.waitKey(1)


        cv.imshow("DebugFrame", frame)
        cv.waitKey(1)

        elapsed = time.time() - time_start

        print(f"Elapsed time: {elapsed*1000:.2f} ms")
        return eggs, dangers
