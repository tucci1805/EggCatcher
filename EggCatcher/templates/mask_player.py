import cv2
import numpy as np

def nothing(x):
    pass

# Carica l'immagine o crea un'immagine di test
img = cv2.imread('debug92.png') # Sostituisci con il percorso della tua immagine
if img is None:
    img = np.zeros((400, 600, 3), np.uint8)
    cv2.putText(img, "Immagine non trovata!", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

# Selezione manuale della ROI
roi_coords = cv2.selectROI("Seleziona ROI", img, fromCenter=False, showCrosshair=True)
x, y, w, h = roi_coords
roi = img[y:y+h, x:x+w]
cv2.destroyWindow("Seleziona ROI")

# Creazione finestra per i controlli e slider per i limiti HSV
cv2.namedWindow("Trackbars")
cv2.resizeWindow("Trackbars", 640, 300)
cv2.createTrackbar("H Min", "Trackbars", 0, 179, nothing)
cv2.createTrackbar("H Max", "Trackbars", 179, 179, nothing)
cv2.createTrackbar("S Min", "Trackbars", 0, 255, nothing)
cv2.createTrackbar("S Max", "Trackbars", 255, 255, nothing)
cv2.createTrackbar("V Min", "Trackbars", 0, 255, nothing)
cv2.createTrackbar("V Max", "Trackbars", 255, 255, nothing)

print("Premi 'q' per uscire.")

while True:
    # Converti la ROI in HSV e leggi i valori dagli slider
    hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    h_min = cv2.getTrackbarPos("H Min", "Trackbars")
    h_max = cv2.getTrackbarPos("H Max", "Trackbars")
    s_min = cv2.getTrackbarPos("S Min", "Trackbars")
    s_max = cv2.getTrackbarPos("S Max", "Trackbars")
    v_min = cv2.getTrackbarPos("V Min", "Trackbars")
    v_max = cv2.getTrackbarPos("V Max", "Trackbars")
    lower = np.array([h_min, s_min, v_min])
    upper = np.array([h_max, s_max, v_max])

    # Crea la maschera e applicala
    mask = cv2.inRange(hsv_roi, lower, upper)
    result = cv2.bitwise_and(roi, roi, mask=mask)

    # Mostra i risultati
    cv2.imshow("ROI Originale", roi)
    cv2.imshow("Maschera", mask)
    cv2.imshow("Risultato Filtro", result)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
