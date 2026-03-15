import time
import ST7735 # type: ignore
import buttons
import glcdfont

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
    CYAN  = ST7735.TFT.CYAN
    YELLOW = ST7735.TFT.YELLOW
    GREY  = 0x7BEF

    tft.fill(BLACK)
    tft.text((10, 10), "RAW ADC VALUES", CYAN, FONT, 1)
    tft.hline((5, 22), 150, GREY)
    tft.text((10, 115), "Press SW1 to exit", GREY, FONT, 1)

    # Definicja kanałów do odczytu
    channels = [
        ("LX (ADS2 CH2)", ads2, 2),
        ("LY (ADS2 CH1)", ads2, 1),
        ("RX (ADS1 CH1)", ads1, 1),
        ("RY (ADS1 CH2)", ads1, 2),
        ("POT1 (ADS2 CH0)", ads2, 0),
        ("POT2 (ADS1 CH0)", ads1, 0)
    ]

    while True:
        for i, (name, ads, ch) in enumerate(channels):
            try:
                val = ads.read(rate=4, channel1=ch)
                y = 35 + i * 12

                # Czyścimy tylko obszar z wartością przed wypisaniem nowej
                tft.fillrect((100, y), (50, 8), BLACK)
                tft.text((10, y), name, WHITE, FONT, 1)
                tft.text((110, y), str(val), YELLOW, FONT, 1)
            except Exception as e:
                print(f"ADC Error: {e}")

        # Powrót do menu po naciśnięciu SW1
        btns = buttons.get_data()
        if btns['sw1']:
            while buttons.get_data()['sw1']:
                time.sleep(0.01)
            break

        time.sleep(0.05)
