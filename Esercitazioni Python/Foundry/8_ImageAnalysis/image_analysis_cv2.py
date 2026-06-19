import os
import json
from dotenv import load_dotenv
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential
import cv2
import numpy as np

# --- Costanti per il pannello laterale ---
PANEL_W = 460
BG_COLOR = (25, 25, 25)
FONT = cv2.FONT_HERSHEY_SIMPLEX
LINE_H = 20
SECTION_GAP = 14
MARGIN_X = 14
WRAP_CHARS = 46  # caratteri massimi per riga nel pannello prima di wrappare


def wrap_text(text, max_chars=WRAP_CHARS):
    """Spezza il testo in più righe se troppo lungo per il pannello."""
    words = text.split()
    lines, current = [], ""
    for w in words:
        if len(current) + len(w) + 1 <= max_chars:
            current = (current + " " + w).strip()
        else:
            lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines


def draw_panel_text(canvas, x, y, text, color=(255, 255, 255), scale=0.5, thickness=1):
    """Scrive una riga di testo nel pannello e ritorna la y successiva."""
    cv2.putText(canvas, text, (x, y), FONT, scale, color, thickness, cv2.LINE_AA)
    return y + LINE_H


def draw_section_title(canvas, x, y, title, color):
    cv2.line(canvas, (x, y), (x + PANEL_W - 2 * MARGIN_X, y), color, 1)
    y += 18
    y = draw_panel_text(canvas, x, y, title, color, 0.62, 2)
    return y + 4


def estimate_panel_height(analysis):
    """Calcola quante righe verranno scritte, per dimensionare il canvas in anticipo."""
    lines = 0

    if 'captionResult' in analysis and analysis['captionResult']:
        lines += 1 + len(wrap_text(analysis['captionResult']['text'])) + 1 + 1  # titolo + testo + conf + gap

    if 'tagsResult' in analysis and analysis['tagsResult']:
        lines += 1 + len(analysis['tagsResult']['values']) + 1

    if 'objectsResult' in analysis and analysis['objectsResult']:
        lines += 1 + len(analysis['objectsResult']['values']) + 1

    if 'peopleResult' in analysis and analysis['peopleResult']:
        lines += 1 + len(analysis['peopleResult']['values']) + 1

    if 'readResult' in analysis and analysis['readResult'] and analysis['readResult'].get('blocks'):
        n_lines = sum(len(b.get('lines', [])) for b in analysis['readResult']['blocks'])
        lines += 1 + n_lines + 1

    if 'smartCropsResult' in analysis and analysis['smartCropsResult']:
        lines += 1 + len(analysis['smartCropsResult']['values']) + 1

    if 'denseCaptionsResult' in analysis and analysis['denseCaptionsResult']:
        lines += 1 + len(analysis['denseCaptionsResult']['values']) + 1

    return lines * LINE_H + 80  # margine extra top/bottom


def main():
    load_dotenv()

    endpoint = os.getenv("AZ_ENDPOINT")
    key = os.getenv("AZ_KEY")

    client = ImageAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))  # type: ignore

    IMAGE_PATH = "Esercitazioni Python/Foundry/8_ImageAnalysis/img.jpg"

    with open(IMAGE_PATH, "rb") as image_file:
        image_bytes = image_file.read()

        analysis = client.analyze(
            image_data=image_bytes,
            visual_features=[
                VisualFeatures.TAGS,
                VisualFeatures.CAPTION,
                VisualFeatures.DENSE_CAPTIONS,
                VisualFeatures.OBJECTS,
                VisualFeatures.PEOPLE,
                VisualFeatures.READ,
                VisualFeatures.SMART_CROPS,
            ],
        )

    print("\n" + "=" * 40)
    print("        RISULTATI DELL'ANALISI")
    print("=" * 40)

    img = cv2.imread(IMAGE_PATH)
    H, W = img.shape[:2]
    overlay = img.copy()

    # --- 2. DENSE CAPTIONS (riquadri grigi sottili) ---
    if 'denseCaptionsResult' in analysis and analysis['denseCaptionsResult']:
        print("\n--- Descrizioni Dettagliate delle Regioni (Dense Captions) ---")
        for i, dc in enumerate(analysis['denseCaptionsResult']['values']):
            box = dc['boundingBox']
            print(f"[{i+1}] '{dc['text']}' ({dc['confidence']*100:.2f}%)")
            cv2.rectangle(img, (box['x'], box['y']), (box['x'] + box['w'], box['y'] + box['h']), (180, 180, 180), 1)
            cv2.putText(img, f"[{i+1}]", (box['x'] + 5, box['y'] + 20), FONT, 0.5, (150, 150, 150), 1)

    # --- 4. OBJECTS (verde) ---
    if 'objectsResult' in analysis and analysis['objectsResult']:
        print("\n--- Oggetti Rilevati (Objects) ---")
        for obj in analysis['objectsResult']['values']:
            nome = obj['tags'][0]['name'] if obj.get('tags') else "Oggetto"
            box = obj['boundingBox']
            print(f"- {nome.capitalize()} ({obj['tags'][0]['confidence']*100:.2f}%)")
            cv2.rectangle(img, (box['x'], box['y']), (box['x'] + box['w'], box['y'] + box['h']), (0, 255, 0), 3)
            cv2.putText(img, nome.upper(), (box['x'] + 5, box['y'] - 10), FONT, 0.7, (0, 255, 0), 2)

    # --- 5. PEOPLE (rosso) ---
    if 'peopleResult' in analysis and analysis['peopleResult']:
        print("\n--- Persone Rilevate (People) ---")
        for i, person in enumerate(analysis['peopleResult']['values']):
            box = person['boundingBox']
            print(f"- Persona {i+1} ({person['confidence']*100:.2f}%)")
            if person['confidence'] > 0.4:
                cv2.rectangle(img, (box['x'], box['y']), (box['x'] + box['w'], box['y'] + box['h']), (0, 0, 255), 3)
                cv2.putText(img, f"PERSONA {i+1}", (box['x'] + 5, box['y'] + 25), FONT, 0.7, (0, 0, 255), 2)

    # --- 6. READ / OCR (overlay giallo) ---
    read_lines_flat = []
    if 'readResult' in analysis and analysis['readResult']:
        print("\n--- Testo Rilevato (OCR / Read) ---")
        read_data = analysis['readResult']
        if read_data.get('blocks'):
            for block in read_data['blocks']:
                for line in block.get('lines', []):
                    print(f"Linea di testo: '{line['text']}'")
                    read_lines_flat.append(line['text'])
                    if 'boundingBox' in line:
                        t_box = line['boundingBox']
                        cv2.rectangle(overlay, (t_box['x'], t_box['y']),
                                      (t_box['x'] + t_box['w'], t_box['y'] + t_box['h']), (0, 255, 255), -1)
                        cv2.putText(img, line['text'], (t_box['x'], t_box['y'] - 5), FONT, 0.5, (0, 165, 255), 1)
        else:
            print("Nessun testo rilevato nell'immagine.")

    img = cv2.addWeighted(overlay, 0.3, img, 0.7, 0)

    # --- 7. SMART CROPS (blu) ---
    if 'smartCropsResult' in analysis and analysis['smartCropsResult']:
        print("\n--- Ritagli Intelligenti Suggeriti (Smart Crops) ---")
        for i, crop in enumerate(analysis['smartCropsResult']['values']):
            box = crop['boundingBox']
            print(f"Suggerimento {i+1} (AR: {crop['aspectRatio']})")
            cv2.rectangle(img, (box['x'], box['y']), (box['x'] + box['w'], box['y'] + box['h']), (255, 0, 0), 4)
            cv2.putText(img, f"CROP ({crop['aspectRatio']})", (box['x'] + 10, box['y'] + box['h'] - 15),
                        FONT, 0.6, (255, 0, 0), 2)

    if 'captionResult' in analysis and analysis['captionResult']:
        caption = analysis['captionResult']
        print(f"\n--- Caption ---\n'{caption['text']}' ({caption['confidence']*100:.2f}%)")

    if 'tagsResult' in analysis and analysis['tagsResult']:
        print("\n--- Tag Rilevati ---")
        for tag in analysis['tagsResult']['values']:
            print(f"- {tag['name'].capitalize()}: {tag['confidence']*100:.2f}%")

    # ================= COSTRUZIONE CANVAS CON PANNELLO =================
    panel_h_needed = estimate_panel_height(analysis)
    canvas_h = max(H, panel_h_needed)
    canvas = np.full((canvas_h, W + PANEL_W, 3), BG_COLOR, dtype=np.uint8)
    canvas[0:H, 0:W] = img

    x0 = W + MARGIN_X
    y = 30
    cv2.putText(canvas, "ANALISI IMMAGINE - DETTAGLI", (x0, y), FONT, 0.62, (255, 255, 255), 2, cv2.LINE_AA)
    y += SECTION_GAP + 10

    # CAPTION
    if 'captionResult' in analysis and analysis['captionResult']:
        caption = analysis['captionResult']
        y = draw_section_title(canvas, x0, y, "CAPTION", (0, 255, 255))
        for line in wrap_text(caption['text']):
            y = draw_panel_text(canvas, x0, y, line, (255, 255, 255))
        y = draw_panel_text(canvas, x0, y, f"confidenza: {caption['confidence']*100:.1f}%", (160, 160, 160))
        y += SECTION_GAP

    # TAGS
    if 'tagsResult' in analysis and analysis['tagsResult']:
        y = draw_section_title(canvas, x0, y, "TAGS", (0, 255, 255))
        for tag in analysis['tagsResult']['values']:
            y = draw_panel_text(canvas, x0, y, f"{tag['name']}: {tag['confidence']*100:.0f}%", (210, 210, 210))
        y += SECTION_GAP

    # OBJECTS
    if 'objectsResult' in analysis and analysis['objectsResult']:
        y = draw_section_title(canvas, x0, y, "OBJECTS", (0, 255, 0))
        for obj in analysis['objectsResult']['values']:
            nome = obj['tags'][0]['name'] if obj.get('tags') else "Oggetto"
            conf = obj['tags'][0]['confidence'] if obj.get('tags') else 0
            y = draw_panel_text(canvas, x0, y, f"{nome}: {conf*100:.0f}%", (150, 255, 150))
        y += SECTION_GAP

    # PEOPLE
    if 'peopleResult' in analysis and analysis['peopleResult']:
        y = draw_section_title(canvas, x0, y, "PEOPLE", (0, 0, 255))
        for i, person in enumerate(analysis['peopleResult']['values']):
            y = draw_panel_text(canvas, x0, y, f"Persona {i+1}: {person['confidence']*100:.0f}%", (150, 150, 255))
        y += SECTION_GAP

    # READ / OCR
    if read_lines_flat:
        y = draw_section_title(canvas, x0, y, "TESTO RILEVATO (OCR)", (0, 165, 255))
        for line_text in read_lines_flat:
            for wrapped in wrap_text(line_text):
                y = draw_panel_text(canvas, x0, y, wrapped, (255, 220, 150))
        y += SECTION_GAP

    # SMART CROPS
    if 'smartCropsResult' in analysis and analysis['smartCropsResult']:
        y = draw_section_title(canvas, x0, y, "SMART CROPS", (255, 0, 0))
        for i, crop in enumerate(analysis['smartCropsResult']['values']):
            y = draw_panel_text(canvas, x0, y, f"Crop {i+1}: AR {crop['aspectRatio']}", (150, 150, 255))
        y += SECTION_GAP

    # DENSE CAPTIONS (riferimento numerico ai box grigi sull'immagine)
    if 'denseCaptionsResult' in analysis and analysis['denseCaptionsResult']:
        y = draw_section_title(canvas, x0, y, "DENSE CAPTIONS", (200, 200, 200))
        for i, dc in enumerate(analysis['denseCaptionsResult']['values']):
            for wrapped in wrap_text(f"[{i+1}] {dc['text']} ({dc['confidence']*100:.0f}%)"):
                y = draw_panel_text(canvas, x0, y, wrapped, (200, 200, 200))
        y += SECTION_GAP

    print("\n" + "=" * 40)

    OUTPUT_PATH = "Esercitazioni Python/Foundry/8_ImageAnalysis/output_analizzato_cv2.jpg"
    cv2.imwrite(OUTPUT_PATH, canvas)
    print(f"\n[OpenCV] Mappa visiva completa salvata in: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()