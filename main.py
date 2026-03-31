from ursina import *
from game.player import Player
from game.map    import Map
from game.ui     import UI
from game.mail   import get_tutorial_mails

app = Ursina(title='우편배달부', borderless=False, development_mode=False,
             size=(1280, 720))

# 한글 폰트
Text.default_font = 'assets/malgun.ttf'

# ── 카메라 (아이소메트릭 쿼터뷰) ────────────────────────────────────
#   orthographic = True  : 원근 왜곡 없이 등축 투영 → 아이소메트릭 스타일
#   rotation y = -45     : 대각선 방향으로 꺾어야 건물 두 면이 동시에 보임
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

# ── 게임 오브젝트 초기화 ─────────────────────────────────────────────
mails    = get_tutorial_mails()
game_map = Map()
player   = Player(mails, interactables=game_map.interactables)
ui       = UI(mails)


# ── 업데이트 ──────────────────────────────────────────────────────────
def update():
    # 카메라가 플레이어를 따라다님
    camera.position = player.position + CAMERA_OFFSET

    ui.update(mails)
    if all(m.delivered for m in mails):
        ui.show_complete(mails, on_restart=restart)


def restart():
    import os, sys
    os.execv(sys.executable, [sys.executable] + sys.argv)


app.run()
