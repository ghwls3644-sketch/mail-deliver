from ursina import *
from game.player import Player
from game.map import Map
from game.ui import UI
from game.mail import get_daily_mails

app = Ursina(title='우편배달부', borderless=False)

# 한글 폰트 설정 — Ursina 기본 폰트는 한글 미지원
Text.default_font = 'assets/malgun.ttf'

# 쿼터뷰 카메라
camera.position = (10, 14, -10)
camera.rotation = (35, -45, 0)
camera.orthographic = True
camera.fov = 12

window.color = color.rgb(180, 210, 255)  # 하늘색 배경

# 바닥
ground = Entity(
    model='plane',
    scale=40,
    texture='assets/textures/grass_block.jpeg',
    texture_scale=(20, 20),
    color=color.rgb(180, 220, 150)
)

# 하루 루프 상태
class GameState:
    DAY   = 'day'
    NIGHT = 'night'

game = GameState()
game.state     = GameState.DAY
game.day_count = 1
game.time      = 0.0    # 0.0 = 오전 9시, 1.0 = 오후 6시 (하루 끝)
game.speed     = 0.01   # 시간 흐름 속도 (숫자 키울수록 빠름)

mails      = get_daily_mails()
game_map   = Map()
player     = Player(mails)
ui         = UI(mails, game, game_map.npcs)

def update():
    if game.state == GameState.DAY:
        game.time += time.dt * game.speed
        ui.update_clock(game.time)

        if game.time >= 1.0:
            end_day()

def end_day():
    game.state = GameState.NIGHT
    ui.show_diary(game.day_count, mails)

def next_day():
    game.state     = GameState.DAY
    game.day_count += 1
    game.time      = 0.0

    # 못 다 한 배달은 다음 날로 이월
    leftover = [m for m in mails if not m.delivered]
    new_mails = get_daily_mails(day=game.day_count)
    mails.clear()
    mails.extend(leftover + new_mails)

    ui.refresh(mails)
    player.mails = mails

# 일기 화면에서 '다음 날' 버튼이 호출
game.next_day = next_day

app.run()
