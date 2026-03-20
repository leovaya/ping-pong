from pygame import *
import socket
import json
from threading import Thread

# ---ПУГАМЕ НАЛАШТУВАННЯ ---
WIDTH, HEIGHT = 800, 600
init()
font.init()
mixer.init()
screen = display.set_mode((WIDTH, HEIGHT))
clock = time.Clock()
display.set_caption("Пінг-Понг (Модифікована версія)")


# ---СЕРВЕР ---
def connect_to_server():
    while True:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('localhost', 8080))  # ---- Підключення до сервера
            buffer = ""
            game_state = {}
            my_id = int(client.recv(24).decode())
            return my_id, game_state, buffer, client
        except:
            pass


def receive():
    global buffer, game_state, game_over
    while not game_over:
        try:
            data = client.recv(1024).decode()
            buffer += data
            while "\n" in buffer:
                packet, buffer = buffer.split("\n", 1)
                if packet.strip():
                    game_state = json.loads(packet)
        except:
            game_state["winner"] = -1
            break


# --- ШРИФТИ ---
font_win = font.Font(None, 72)
font_main = font.Font(None, 36)

# --- ЗОБРАЖЕННЯ ----
BG_IMG = image.load("fotos/background.png")
BG_IMG = transform.scale(BG_IMG, (WIDTH, HEIGHT))

BALL_IMG = image.load("fotos/ball.png")
BALL_IMG = transform.scale(BALL_IMG, (20, 20))

PADDLE1_IMG = image.load("fotos/paddle1.png")
PADDLE1_IMG = transform.rotate(PADDLE1_IMG, 90)
PADDLE1_IMG = transform.scale(PADDLE1_IMG, (20, 100))

PADDLE2_IMG = transform.flip(PADDLE1_IMG, True, False)

# --- ЗВУКИ ---
mixer.init()
sound_plat = mixer.Sound("sound/plat.wav")
sound_wall = mixer.Sound("sound/wall.wav")

# back music
try:
    mixer.music.load("sound/timewaster.mp3")
    mixer.music.play(-1)
    mixer.music.set_volume(0.15)
except Exception as e:
    print("Music not found: ", e)

# --- ГРА ---
game_over = False
winner = None
you_winner = None

# -----menu----
is_menu = True
btnPlay = transform.scale_by(image.load("fotos/play.png"), 1.5)
playRect = btnPlay.get_rect(center=(WIDTH // 2, HEIGHT // 2))

while is_menu:
    for e in event.get():
        if e.type == QUIT:
            exit()
        if e.type == MOUSEBUTTONDOWN and e.button == 1:
            if playRect.collidepoint(e.pos):
                is_menu = False

        screen.blit(BG_IMG, (0, 0))
        screen.blit(btnPlay, playRect)
        display.update()
        clock.tick(60)

my_id, game_state, buffer, client = connect_to_server()
Thread(target=receive, daemon=True).start()

while True:
    for e in event.get():
        if e.type == QUIT:
            exit()

    if "countdown" in game_state and game_state["countdown"] > 0:
        screen.fill((0, 0, 0))
        countdown_text = font.Font(None, 72).render(str(game_state["countdown"]), True, (255, 255, 255))
        screen.blit(countdown_text, (WIDTH // 2 - 20, HEIGHT // 2 - 30))
        display.update()
        continue  # Не малюємо гру до завершення відліку

    if "winner" in game_state and game_state["winner"] is not None:
        screen.fill((20, 20, 20))

        if you_winner is None:  # Встановлюємо тільки один раз
            if game_state["winner"] == my_id:
                you_winner = True
            else:
                you_winner = False

        if you_winner:
            text = "Ти переміг!"
        else:
            text = "Пощастить наступним разом!"

        win_text = font_win.render(text, True, (255, 215, 0))
        text_rect = win_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(win_text, text_rect)

        #K для рестарту
        text = font_win.render('К - рестарт', True, (255, 215, 0))
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 120))
        screen.blit(text, text_rect)

        display.update()
        continue  # Блокує гру після перемоги

    if game_state:
        screen.blit(BG_IMG, (0, 0))
        screen.blit(PADDLE1_IMG, (20, game_state['paddles']['0']))
        screen.blit(PADDLE2_IMG, (WIDTH - 40, game_state['paddles']['1']))

        # gold super ball
        if game_state['ball'].get('is_super'):
            draw.circle(screen, (255, 215, 0), (int(game_state['ball']['x']), int(game_state['ball']['y'])), 12)
        else:
            screen.blit(BALL_IMG, (game_state['ball']['x'] - 10, game_state['ball']['y'] - 10))

        score_text = font_main.render(f"{game_state['scores'][0]} : {game_state['scores'][1]}", True, (255, 255, 255))
        screen.blit(score_text, (WIDTH // 2 - 25, 20))

        if game_state['sound_event']:
            if game_state['sound_event'] == 'wall_hit':
                sound_wall.play()
            if game_state['sound_event'] == 'platform_hit':
                sound_plat.play()
            game_state['sound_event'] = None

    else:
        wating_text = font_main.render(f"Очікування гравців...", True, (255, 255, 255))
        screen.blit(wating_text, (WIDTH // 2 - 25, 20))

    display.update()
    clock.tick(60)

    keys = key.get_pressed()
    # smth wrong
    if keys[K_w]:
        client.send(b"UP")
    elif keys[K_s]:
        client.send(b"DOWN")