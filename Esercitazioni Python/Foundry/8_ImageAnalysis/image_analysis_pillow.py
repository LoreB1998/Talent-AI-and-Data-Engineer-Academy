import os
from dotenv import load_dotenv
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential
from PIL import Image, ImageDraw, ImageFont

# ============================== COSTANTI ==============================
PANEL_W = 460
BG_COLOR = (18, 18, 20)          # sfondo pannello, quasi nero
CARD_COLOR = (30, 30, 34)        # sfondo "card" sezione
CARD_RADIUS = 10
MARGIN_X = 18
PADDING = 14
LINE_H = 23
SECTION_GAP = 14
WRAP_CHARS = 44

PALETTE = {
    "caption": (90, 200, 230),
    "tags": (90, 200, 230),
    "objects": (110, 220, 110),
    "people": (240, 90, 90),
    "ocr": (240, 180, 70),
    "crops": (110, 140, 240),
    "dense": (170, 170, 175),
    "text": (225, 225, 228),
    "muted": (140, 140, 145),
}


def _load_font(candidates, size):
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


_REGULAR = ["/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/Library/Fonts/Arial.ttf"]
_BOLD = ["/System/Library/Fonts/Supplemental/Arial Bold.ttf",
         "/System/Library/Fonts/Helvetica.ttc",
         "/Library/Fonts/Arial Bold.ttf"]

FONT_REGULAR = _load_font(_REGULAR, 15)
FONT_BOLD = _load_font(_BOLD, 16)
FONT_SMALL = _load_font(_REGULAR, 12)
FONT_TITLE = _load_font(_BOLD, 19)
FONT_OVERLAY = _load_font(_BOLD, 19)
FONT_OVERLAY_SMALL = _load_font(_REGULAR, 14)


def wrap_text(text, max_chars=WRAP_CHARS):
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


# ----------------------- helper grafici -----------------------

def draw_confidence_badge(draw, x, y, confidence, color):
    """Pillola colorata con la percentuale, stile 'badge' moderno."""
    label = f"{confidence * 100:.0f}%"
    bbox = draw.textbbox((0, 0), label, font=FONT_SMALL)
    w = bbox[2] - bbox[0] + 14
    h = bbox[3] - bbox[1] + 8
    draw.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=color)
    draw.text((x + 7, y + 3), label, fill=(15, 15, 15), font=FONT_SMALL)
    return w


def draw_box_label(draw, x, y, text, color, font=FONT_OVERLAY):
    """Etichetta con sfondo pieno sopra il bounding box (più leggibile di testo nudo)."""
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad = 5
    draw.rounded_rectangle([x, y, x + w + 2 * pad, y + h + 2 * pad], radius=5, fill=color)
    draw.text((x + pad, y + pad - bbox[1]), text, fill=(15, 15, 15), font=font)


class Panel:
    """Gestisce il disegno del pannello laterale a 'card'.

    Per evitare che lo sfondo della card coprisse il testo già scritto,
    le righe vengono prima raccolte in una lista (senza disegnare nulla),
    poi si calcola l'altezza totale, si disegna lo sfondo, e infine
    il testo viene scritto sopra.
    """

    def __init__(self, draw, x0, panel_w):
        self.draw = draw
        self.x0 = x0
        self.panel_w = panel_w
        self._lines = []   # lista di dict: {type, text, fill, font, confidence, color}
        self._title = None
        self._title_color = None

    def card_start(self, title, color):
        self._title = title
        self._title_color = color
        self._lines = []

    def line(self, text, fill=PALETTE["text"], font=FONT_REGULAR):
        self._lines.append({"kind": "text", "text": text, "fill": fill, "font": font})

    def line_with_badge(self, label, confidence, color):
        self._lines.append({"kind": "badge", "text": label, "confidence": confidence, "color": color})

    def card_end(self, y):
        """Calcola l'altezza necessaria, disegna lo sfondo, poi scrive titolo e righe."""
        content_h = len(self._lines) * LINE_H
        title_h = 26
        y0 = y
        y1 = y + PADDING + title_h + content_h + PADDING - 6

        x_inner = self.x0 - PADDING
        card_w = self.panel_w - 2 * MARGIN_X + 2 * PADDING
        self.draw.rounded_rectangle([x_inner, y0, x_inner + card_w, y1],
                                     radius=CARD_RADIUS, fill=CARD_COLOR)

        # Titolo
        ty = y0 + PADDING
        self.draw.text((self.x0, ty), self._title, fill=self._title_color, font=FONT_BOLD)
        cy = ty + title_h

        # Contenuto
        for item in self._lines:
            if item["kind"] == "text":
                self.draw.text((self.x0, cy), item["text"], fill=item["fill"], font=item["font"])
            elif item["kind"] == "badge":
                self.draw.text((self.x0, cy + 2), item["text"], fill=PALETTE["text"], font=FONT_REGULAR)
                bbox = self.draw.textbbox((0, 0), "100%", font=FONT_SMALL)
                badge_w = bbox[2] - bbox[0] + 14
                badge_x = self.x0 + self.panel_w - 2 * MARGIN_X - badge_w
                draw_confidence_badge(self.draw, badge_x, cy - 1, item["confidence"], item["color"])
            cy += LINE_H

        return y1 + SECTION_GAP


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

    pil_img = Image.open(IMAGE_PATH).convert("RGB")
    W, H = pil_img.size
    draw = ImageDraw.Draw(pil_img, "RGBA")

    # --- DENSE CAPTIONS ---
    if analysis.get('denseCaptionsResult'):
        print("\n--- Dense Captions ---")
        for i, dc in enumerate(analysis['denseCaptionsResult']['values']):
            b = dc['boundingBox']
            print(f"[{i+1}] '{dc['text']}' ({dc['confidence']*100:.2f}%)")
            draw.rectangle([b['x'], b['y'], b['x'] + b['w'], b['y'] + b['h']],
                            outline=PALETTE["dense"], width=1)
            draw_box_label(draw, b['x'] + 3, b['y'] + 3, f"{i+1}", PALETTE["dense"], FONT_OVERLAY_SMALL)

    # --- OBJECTS ---
    if analysis.get('objectsResult'):
        print("\n--- Objects ---")
        for obj in analysis['objectsResult']['values']:
            nome = obj['tags'][0]['name'] if obj.get('tags') else "Oggetto"
            conf = obj['tags'][0]['confidence'] if obj.get('tags') else 0
            b = obj['boundingBox']
            print(f"- {nome.capitalize()} ({conf*100:.2f}%)")
            draw.rounded_rectangle([b['x'], b['y'], b['x'] + b['w'], b['y'] + b['h']],
                                    radius=4, outline=PALETTE["objects"], width=3)
            draw_box_label(draw, b['x'], max(0, b['y'] - 30), f"{nome.upper()} {conf*100:.0f}%", PALETTE["objects"])

    # --- PEOPLE ---
    if analysis.get('peopleResult'):
        print("\n--- People ---")
        for i, person in enumerate(analysis['peopleResult']['values']):
            b = person['boundingBox']
            print(f"- Persona {i+1} ({person['confidence']*100:.2f}%)")
            if person['confidence'] > 0.4:
                draw.rounded_rectangle([b['x'], b['y'], b['x'] + b['w'], b['y'] + b['h']],
                                        radius=4, outline=PALETTE["people"], width=3)
                draw_box_label(draw, b['x'], b['y'] + 4, f"PERSONA {i+1}", PALETTE["people"])

    # --- READ / OCR ---
    read_lines_flat = []
    if analysis.get('readResult'):
        print("\n--- OCR ---")
        read_data = analysis['readResult']
        if read_data.get('blocks'):
            overlay_layer = Image.new("RGBA", pil_img.size, (0, 0, 0, 0)) # type: ignore
            overlay_draw = ImageDraw.Draw(overlay_layer)
            for block in read_data['blocks']:
                for line in block.get('lines', []):
                    print(f"Linea: '{line['text']}'")
                    read_lines_flat.append(line['text'])
                    if 'boundingBox' in line:
                        t = line['boundingBox']
                        overlay_draw.rectangle(
                            [t['x'], t['y'], t['x'] + t['w'], t['y'] + t['h']],
                            fill=(*PALETTE["ocr"], 80)
                        )
            pil_img = Image.alpha_composite(pil_img.convert("RGBA"), overlay_layer).convert("RGB")
            draw = ImageDraw.Draw(pil_img, "RGBA")
        else:
            print("Nessun testo rilevato.")

    # --- SMART CROPS ---
    if analysis.get('smartCropsResult'):
        print("\n--- Smart Crops ---")
        for i, crop in enumerate(analysis['smartCropsResult']['values']):
            b = crop['boundingBox']
            print(f"Crop {i+1} (AR {crop['aspectRatio']})")
            draw.rounded_rectangle([b['x'], b['y'], b['x'] + b['w'], b['y'] + b['h']],
                                    radius=6, outline=PALETTE["crops"], width=4)
            draw_box_label(draw, b['x'] + 6, b['y'] + b['h'] - 34, f"CROP {crop['aspectRatio']}", PALETTE["crops"])

    if analysis.get('captionResult'):
        c = analysis['captionResult']
        print(f"\n--- Caption ---\n'{c['text']}' ({c['confidence']*100:.2f}%)")

    if analysis.get('tagsResult'):
        print("\n--- Tags ---")
        for tag in analysis['tagsResult']['values']:
            print(f"- {tag['name'].capitalize()}: {tag['confidence']*100:.2f}%")

    print("\n" + "=" * 40)

    # ====================== CANVAS FINALE CON PANNELLO ======================
    # Step 1: stima approssimativa righe per dimensionare il canvas
    approx_lines = 4
    if analysis.get('captionResult'):
        approx_lines += 3 + len(wrap_text(analysis['captionResult']['text']))
    if analysis.get('tagsResult'):
        approx_lines += 3 + len(analysis['tagsResult']['values'])
    if analysis.get('objectsResult'):
        approx_lines += 3 + len(analysis['objectsResult']['values'])
    if analysis.get('peopleResult'):
        approx_lines += 3 + len(analysis['peopleResult']['values'])
    if read_lines_flat:
        wrapped_ocr = sum(len(wrap_text(t)) for t in read_lines_flat)
        approx_lines += 3 + wrapped_ocr
    if analysis.get('smartCropsResult'):
        approx_lines += 3 + len(analysis['smartCropsResult']['values'])
    if analysis.get('denseCaptionsResult'):
        dc_lines = sum(len(wrap_text(f"[{i+1}] {dc['text']}")) for i, dc in
                        enumerate(analysis['denseCaptionsResult']['values']))
        approx_lines += 3 + dc_lines

    canvas_h = max(H, approx_lines * LINE_H + 140)
    canvas = Image.new("RGB", (W + PANEL_W, canvas_h), BG_COLOR) # type: ignore
    canvas.paste(pil_img, (0, 0))
    cdraw = ImageDraw.Draw(canvas)

    x0 = W + MARGIN_X
    y = 36
    cdraw.text((x0, y), "ANALISI IMMAGINE", fill=PALETTE["text"], font=FONT_TITLE)
    y += 34
    panel = Panel(cdraw, x0, PANEL_W)

    if analysis.get('captionResult'):
        caption = analysis['captionResult']
        panel.card_start("CAPTION", PALETTE["caption"])
        for line in wrap_text(caption['text']):
            panel.line(line)
        panel.line(f"confidenza {caption['confidence']*100:.0f}%", PALETTE["muted"], FONT_SMALL)
        y = panel.card_end(y)

    if analysis.get('tagsResult'):
        panel.card_start("TAGS", PALETTE["tags"])
        for tag in analysis['tagsResult']['values']:
            panel.line_with_badge(tag['name'].capitalize(), tag['confidence'], PALETTE["tags"])
        y = panel.card_end(y)

    if analysis.get('objectsResult'):
        panel.card_start("OBJECTS", PALETTE["objects"])
        for obj in analysis['objectsResult']['values']:
            nome = obj['tags'][0]['name'] if obj.get('tags') else "Oggetto"
            conf = obj['tags'][0]['confidence'] if obj.get('tags') else 0
            panel.line_with_badge(nome.capitalize(), conf, PALETTE["objects"])
        y = panel.card_end(y)

    if analysis.get('peopleResult'):
        panel.card_start("PEOPLE", PALETTE["people"])
        for i, person in enumerate(analysis['peopleResult']['values']):
            panel.line_with_badge(f"Persona {i+1}", person['confidence'], PALETTE["people"])
        y = panel.card_end(y)

    if read_lines_flat:
        panel.card_start("TESTO RILEVATO (OCR)", PALETTE["ocr"])
        for line_text in read_lines_flat:
            for wrapped in wrap_text(line_text):
                panel.line(wrapped)
        y = panel.card_end(y)

    if analysis.get('smartCropsResult'):
        panel.card_start("SMART CROPS", PALETTE["crops"])
        for i, crop in enumerate(analysis['smartCropsResult']['values']):
            panel.line(f"Crop {i+1}: AR {crop['aspectRatio']}")
        y = panel.card_end(y)

    if analysis.get('denseCaptionsResult'):
        panel.card_start("DENSE CAPTIONS", PALETTE["dense"])
        for i, dc in enumerate(analysis['denseCaptionsResult']['values']):
            for wrapped in wrap_text(f"[{i+1}] {dc['text']} ({dc['confidence']*100:.0f}%)"):
                panel.line(wrapped, PALETTE["muted"], FONT_SMALL)
        y = panel.card_end(y)

    OUTPUT_PATH = "Esercitazioni Python/Foundry/8_ImageAnalysis/output_analizzato_pillow.png"
    canvas.save(OUTPUT_PATH, format="PNG", compress_level=3)
    print(f"\n[Pillow] Mappa visiva completa salvata in: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()