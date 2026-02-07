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
    GREY  = 0x7BEF # Ciemniejszy szary (zakładając format 565)

    # --- Layout ---
    MENU_X = 25  # Przesunięcie tekstu w prawo
    CURSOR_X = 10 
    START_Y = 45
    SPACING = 22

    tft.fill(BLACK)
    
    # Nagłówek w ramce
    tft.rect((5, 5), (150, 25), CYAN)
    tft.text((35, 13), "CONTROL MODE", CYAN, FONT, 1)
    
    # Linia boczna (dekoracyjna)
    tft.vline((18, START_Y - 5), 70, GREY)

    # Statyczne rysowanie opcji
    for i, opcja in enumerate(opcje):
        y = START_Y + i * SPACING
        tft.text((MENU_X, y), opcja, WHITE, FONT, 1)

    while True:
        pots = joystick.get_potentiometers()
        btns = buttons.get_data()

        # Lepsze mapowanie (odporne na drgania potencjometru)
        val = pots['pot2']
        nowy_wybor = min(int((val * ilosc) / 101), ilosc - 1)

        if nowy_wybor != wybrany:
            # 1. Wyczyść stary kursor I starą pozycję tekstu (opcjonalnie)
            if wybrany != -1:
                old_y = START_Y + wybrany * SPACING
                tft.text((CURSOR_X, old_y), " ", BLACK, FONT, 1) # Usuń kursor
                # Przywróć kolor szary dla niewybranych (opcjonalnie)
                tft.text((MENU_X, old_y), opcje[wybrany], GREY, FONT, 1)

            # 2. Narysuj nowy kursor i wyróżnij tekst
            wybrany = nowy_wybor
            new_y = START_Y + wybrany * SPACING
            
            tft.text((CURSOR_X, new_y), ">", CYAN, FONT, 1) # Kursor w kolorze CYAN
            tft.text((MENU_X, new_y), opcje[wybrany], WHITE, FONT, 1) # Tekst na biało

        if btns['sw1']:
            # Efekt "mignięcia" przy wyborze dla feedbacku
            for _ in range(3):
                tft.text((CURSOR_X, START_Y + wybrany * SPACING), ">", BLACK, FONT, 1)
                time.sleep(0.05)
                tft.text((CURSOR_X, START_Y + wybrany * SPACING), ">", CYAN, FONT, 1)
                time.sleep(0.05)
            
            while buttons.get_data()['sw1']:
                time.sleep(0.01)
            return opcje[wybrany]

        time.sleep(0.05)