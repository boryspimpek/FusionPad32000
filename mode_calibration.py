import machine
import time
import ST7735
import glcdfont

# Definicja czcionki identyczna jak w menu.py
FONT = {
    "Width": 5,
    "Height": 7,
    "Start": 32,
    "End": 122,
    "Data": glcdfont.font
}

def run(tft, ads1, ads2):
    BLACK = ST7735.TFT.BLACK
    WHITE = ST7735.TFT.WHITE
    YELLOW = ST7735.TFT.YELLOW
    GREEN = ST7735.TFT.GREEN
    CYAN = ST7735.TFT.CYAN

    tft.fill(BLACK)
    tft.text((10, 10), "KALIBRACJA", YELLOW, FONT, 1)
    
    channels = ["LX", "LY", "RX", "RY", "P1", "P2"]
    mins = [32767] * 6
    maxs = [0] * 6
    centers = [0] * 6

    def get_raw():
        # Zgodnie z Twoim start.py: LX, LY (ads2), RX, RY (ads1), P1(ads2), P2(ads1)
        return [
            ads2.read(4, 2), ads2.read(4, 1), # LX, LY
            ads1.read(4, 1), ads1.read(4, 2), # RX, RY
            ads2.read(4, 0), ads1.read(4, 0)  # P1, P2
        ]

    # --- KROK 1: ŚRODEK ---
    tft.text((10, 40), "1. Pusc drazki", WHITE, FONT, 1)
    tft.text((10, 55), "Czekaj 5s...", CYAN, FONT, 1)
    
    sums = [0] * 6
    for s in range(50):
        raw = get_raw()
        for i in range(6): sums[i] += raw[i]
        time.sleep(0.1)
    
    for i in range(6): centers[i] = sums[i] // 50

    # --- KROK 2: MIN/MAX ---
    tft.fill(BLACK)
    tft.text((10, 10), "2. Krec drazkami", WHITE, FONT, 1)
    tft.text((10, 25), "przez 10 sek!", YELLOW, FONT, 1)
    
    # Odliczanie czasu w MicroPython (ticks_ms)
    start_ms = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start_ms) < 10000:
        raw = get_raw()
        for i in range(6):
            if raw[i] < mins[i]: mins[i] = raw[i]
            if raw[i] > maxs[i]: maxs[i] = raw[i]
        
        # Podgląd na żywo
        tft.text((10, 50), "LX: {} - {}".format(mins[0], maxs[0]), GREEN, FONT, 1)
        time.sleep(0.05)

    # --- WYNIKI NA EKRANIE ---
    tft.fill(BLACK)
    tft.text((10, 5), "WYNIKI (ZAPISZ!):", GREEN, FONT, 1)
    
    y = 20
    for i in range(6):
        msg = "{}: {} < {} > {}".format(channels[i], mins[i], centers[i], maxs[i])
        tft.text((5, y), msg, WHITE, FONT, 1)
        y += 12
    
    tft.text((10, 110), "Kliknij SW1 aby wyjsc", CYAN, FONT, 1)
    
    # Czekaj na przycisk, żeby wyniki nie zniknęły
    import buttons
    while not buttons.get_data()['sw1']:
        time.sleep(0.1)