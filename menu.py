import joystick
import buttons
import time
import ST7735 # type: ignore
import glcdfont

FONT = {
    "Width": 5,
    "Height": 7,
    "Start": 32,
    "End": 122,
    "Data": glcdfont.font
}

def show(tft):
    opcje = ["PC Gamepad", "RC Transmitter", "Robot Controller"]
    ilosc = len(opcje)
    wybrany = -1

    BLACK = ST7735.TFT.BLACK
    WHITE = ST7735.TFT.WHITE
    CYAN  = ST7735.TFT.CYAN

    HEADER_Y = 10
    LINE_Y   = 25
    MENU_Y   = 40

    # --- Stałe elementy ---
    tft.fill(BLACK)
    tft.text((30, HEADER_Y), "SYSTEM V1.0", CYAN, FONT, 1)
    tft.hline((0, LINE_Y), 160, WHITE)

    # Rysuj menu bazowe (bez zaznaczenia)
    for i, opcja in enumerate(opcje):
        y = MENU_Y + i * 20
        tft.text((20, y), opcja, WHITE, FONT, 1)

    while True:
        pots = joystick.get_potentiometers()
        btns = buttons.get_data()

        nowy_wybor = min(int((pots['pot2'] * ilosc) / 101), ilosc - 1)

        if nowy_wybor != wybrany:
            # Usuń stary tick
            if wybrany != -1:
                old_y = MENU_Y + wybrany * 20
                tft.text((8, old_y), " ", WHITE, FONT, 1)

            # Narysuj nowy tick
            wybrany = nowy_wybor
            new_y = MENU_Y + wybrany * 20
            tft.text((8, new_y), ">", WHITE, FONT, 1)

        # Potwierdzenie
        if btns['sw1']:
            while buttons.get_data()['sw1']:
                time.sleep(0.01)
            return opcje[wybrany]

        time.sleep(0.05)
