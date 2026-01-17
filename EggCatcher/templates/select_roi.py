import cv2
import os

if __name__ == "__main__":
    # Ciclo infinito per processare più immagini una dopo l'altra
    while True:
        print("\n--- NUOVO RITAGLIO ---")
        
        # 1. Input percorso immagine sorgente
        image_path = input("Inserisci il path dell'immagine da ritagliare (es. screen.png) o 'q' per uscire: ").strip()
        
        if image_path.lower() == 'q':
            print("Chiusura programma.")
            break

        # Verifica se il file esiste
        if not os.path.exists(image_path):
            print(f"Errore: Il file '{image_path}' non esiste. Riprova.")
            continue

        # 2. Input nome del file di output
        output_name = input("Inserisci il nome/path del ritaglio da salvare (es. templates/uovo.png): ").strip()
        
        # Crea la cartella se non esiste
        output_dir = os.path.dirname(output_name)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Cartella '{output_dir}' creata.")

        # 3. Carica l'immagine
        img = cv2.imread(image_path)
        
        if img is None:
            print(f"Errore: Impossibile caricare l'immagine {image_path}. Formato non valido?")
            continue

        # 4. Selezione ROI (Interattiva)
        print("\nIstruzioni:")
        print("- TRASCINA il mouse per selezionare l'area.")
        print("- Premi INVIO o SPAZIO per confermare.")
        print("- Premi 'c' per annullare la selezione.")
        print("- Chiudi la finestra o premi ESC per saltare questa immagine.")
        
        # Mostra l'immagine e permette il ritaglio
        roi = cv2.selectROI("Seleziona la ROI", img, fromCenter=False, showCrosshair=True)

        # x, y sono le coordinate in alto a sinistra, w e h dimensioni
        x, y, w, h = roi

        # 5. Verifica ed esecuzione del ritaglio
        if w > 0 and h > 0:
            # Slicing NumPy: [y:y+altezza, x:x+larghezza]
            crop = img[int(y):int(y+h), int(x):int(x+w)]
            
            # Salva il ritaglio
            success = cv2.imwrite(output_name, crop)
            
            if success:
                print(f"\n[OK] Ritaglio salvato: {output_name}")

                  # --- AGGIUNTA: SCRITTURA SU FILE coordinate.txt ---
                with open("coordinate.txt", "a") as f:
                    # Formato: nome_file | x: ..., y: ..., w: ..., h: ...
                    linea = f"{output_name} | x:{x}, y:{y}, w:{w}, h:{h}\n"
                    f.write(linea)
                
                print(f"Coordinate salvate: x={x}, y={y}, w={w}, h={h}")
                
                # Mostra anteprima del ritaglio
                cv2.imshow("Anteprima Ritaglio (Premi un tasto per continuare)", crop)
                cv2.waitKey(0)
            else:
                print(f"[ERRORE] Impossibile scrivere il file in {output_name}")
        else:
            print("Selezione annullata o area nulla.")

        # Pulisce le finestre per la prossima immagine
        cv2.destroyAllWindows()

