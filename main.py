from ursina import *
from game.title  import TitleScreen
from game.player import Player
from game.map    import Map
from game.ui     import UI
from game.mail   import get_tutorial_mails

app = Ursina(title='우편배달부', borderless=False, development_mode=False,
             size=(1280, 720))

# 한글 폰트
Text.default_font = 'assets/malgun.ttf'

# ── 카메라 (아이소메트릭 쿼터뷰) ────────────────────────────────────
CAMERA_OFFSET       = Vec3(-8, 13.5, 18)
camera.rotation     = (30, 135, 0)
camera.orthographic = True
camera.fov          = 22

# ── 배경 ──────────────────────────────────────────────────────────────
window.color = color.rgb(180, 210, 255)

ground = Entity(
    model='plane',
    scale=80,
    texture='assets/textures/grass_block.jpeg',
    texture_scale=(40, 40),
    color=color.rgb(180, 220, 150)
)

# ── 게임 상태 ─────────────────────────────────────────────────────────
game_started = False
mails    = None
game_map = None
player   = None
ui       = None


def start_game():
    """타이틀에서 '시작하기' 클릭 시 호출"""
    global game_started, mails, game_map, player, ui
    mails    = get_tutorial_mails()
    game_map = Map()
    player   = Player(mails, interactables=game_map.interactables)
    ui       = UI(mails)
    game_started = True


# ── 타이틀 화면 표시 ──────────────────────────────────────────────────
title_screen = TitleScreen(on_start=start_game)


# ── 업데이트 ──────────────────────────────────────────────────────────
def update():
    if not game_started:
        return

    camera.position = player.position + CAMERA_OFFSET

    ui.update(mails)
    if all(m.delivered for m in mails):
        ui.show_complete(mails, on_restart=restart)


def restart():
    import os, sys
    os.execv(sys.executable, [sys.executable] + sys.argv)


app.run()
