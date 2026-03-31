"""
editor.py — 우편배달부 맵 에디터 (독립 실행 도구)
실행: python editor.py   ← 게임과 완전히 분리됨

  카메라 조작
    [WASD]        수평 이동
    [스크롤]       줌 인/아웃
    [우클릭 드래그] 카메라 회전

  오브젝트 배치
    [1~6]   카테고리 선택
    [ / ]   같은 카테고리 내 모델 순환
    [R]     회전 (90° 단위)
    [클릭]  배치
    [Del]   커서 근처 삭제
    [Z]     실행취소
    [G]     그리드 토글

  파일
    [S]     저장 → game/editor_data.json
    [L]     불러오기
"""

from ursina import *
from PIL import Image as PILImage
from panda3d.core import (
    FrameBufferProperties, WindowProperties, GraphicsPipe,
    GraphicsOutput, NodePath, PerspectiveLens,
    AmbientLight, DirectionalLight, LColor,
    Texture as P3DTexture,
    LPoint3, LVector3,
)
from panda3d.core import Camera as P3DCamera
import json, os

# ─── 경로 상수 (map.py 와 동일) ────────────────────────────────────────
SUBURBAN   = 'assets/kenney_city-kit-suburban_20/Models/GLB format/'
ROADS      = 'assets/kenney_city-kit-roads/Models/GLB format/'
COMMERCIAL = 'assets/kenney_city-kit-commercial_2.1/Models/GLB format/'
NATURE     = 'assets/kenney_nature-kit/Models/GLTF format/'
CARS       = 'assets/kenney_car-kit/Models/GLB format/'

SAVE_PATH = 'game/editor_data.json'
GRID_SNAP = 1.0

# ─── 스케일 프리셋 (게임과 동일 — JSON 저장값) ────────────────────────
SC = {
    'road':   (2,   2,   2  ),
    'bldg':   (2,   2,   2  ),
    'tree':   (1.5, 1.5, 1.5),
    'treeL':  (2,   2,   2  ),
    'flower': (1,   1,   1  ),
    'car':    (1.5, 1.5, 1.5),
    'misc':   (1.5, 1.5, 1.5),
}

# ─── 에디터 표시 배율 (카메라가 멀어서 작은 모델이 안 보이는 것 보정) ──
SC_DISPLAY_MULT = {
    'road':   1.0,
    'bldg':   1.0,
    'tree':   2.5,
    'treeL':  2.0,
    'flower': 4.0,
    'car':    2.0,
    'misc':   2.0,
}

# ─── 팔레트 ────────────────────────────────────────────────────────────
PALETTE = [
    ('도로', [
        ('straight',      ROADS + 'road-straight.glb',      'road'),
        ('crossroad',     ROADS + 'road-crossroad.glb',     'road'),
        ('end',           ROADS + 'road-end.glb',           'road'),
        ('roundabout',    ROADS + 'road-roundabout.glb',    'road'),
        ('bend',          ROADS + 'road-bend.glb',          'road'),
        ('intersection',  ROADS + 'road-intersection.glb',  'road'),
        ('side',          ROADS + 'road-side.glb',          'road'),
        ('crossing',      ROADS + 'road-crossing.glb',      'road'),
    ]),
    ('상업건물', [
        ('building-a', COMMERCIAL + 'building-a.glb', 'bldg'),
        ('building-b', COMMERCIAL + 'building-b.glb', 'bldg'),
        ('building-c', COMMERCIAL + 'building-c.glb', 'bldg'),
        ('building-d', COMMERCIAL + 'building-d.glb', 'bldg'),
    ]),
    ('주거건물', [
        ('type-a', SUBURBAN + 'building-type-a.glb', 'bldg'),
        ('type-b', SUBURBAN + 'building-type-b.glb', 'bldg'),
        ('type-c', SUBURBAN + 'building-type-c.glb', 'bldg'),
        ('type-e', SUBURBAN + 'building-type-e.glb', 'bldg'),
        ('type-f', SUBURBAN + 'building-type-f.glb', 'bldg'),
        ('type-j', SUBURBAN + 'building-type-j.glb', 'bldg'),
    ]),
    ('나무', [
        ('tree-large',    SUBURBAN + 'tree-large.glb',        'bldg'),
        ('tree-small',    SUBURBAN + 'tree-small.glb',        'tree'),
        ('tree_oak',      NATURE   + 'tree_oak.glb',          'tree'),
        ('tree_fat',      NATURE   + 'tree_fat.glb',          'tree'),
        ('tree_tall',     NATURE   + 'tree_tall.glb',         'tree'),
        ('tree_cone',     NATURE   + 'tree_cone.glb',         'treeL'),
        ('tree_default',  NATURE   + 'tree_default.glb',      'treeL'),
        ('tree_detailed', NATURE   + 'tree_detailed.glb',     'tree'),
        ('tree_pine',     NATURE   + 'tree_pineRoundA.glb',   'tree'),
        ('tree_thin',     NATURE   + 'tree_thin.glb',         'tree'),
    ]),
    ('자연/꽃', [
        ('flower_redA',      NATURE + 'flower_redA.glb',      'flower'),
        ('flower_redB',      NATURE + 'flower_redB.glb',      'flower'),
        ('flower_purpleA',   NATURE + 'flower_purpleA.glb',   'flower'),
        ('flower_yellowA',   NATURE + 'flower_yellowA.glb',   'flower'),
        ('plant_bush',       NATURE + 'plant_bush.glb',       'flower'),
        ('plant_bushLarge',  NATURE + 'plant_bushLarge.glb',  'flower'),
        ('plant_bushSmall',  NATURE + 'plant_bushSmall.glb',  'flower'),
        ('rock_smallA',      NATURE + 'rock_smallA.glb',      'flower'),
        ('rock_largeA',      NATURE + 'rock_largeA.glb',      'flower'),
        ('log',              NATURE + 'log.glb',              'flower'),
        ('stump_round',      NATURE + 'stump_round.glb',      'flower'),
        ('lily_large',       NATURE + 'lily_large.glb',       'flower'),
    ]),
    ('차량/소품', [
        ('delivery',   CARS     + 'delivery.glb',      'car' ),
        ('sedan',      CARS     + 'sedan.glb',         'car' ),
        ('taxi',       CARS     + 'taxi.glb',          'car' ),
        ('suv',        CARS     + 'suv.glb',           'car' ),
        ('planter',    SUBURBAN + 'planter.glb',       'misc'),
        ('fence-1x2',  SUBURBAN + 'fence-1x2.glb',    'misc'),
        ('fence-1x3',  SUBURBAN + 'fence-1x3.glb',    'misc'),
        ('fence',      SUBURBAN + 'fence.glb',         'misc'),
        ('light',      ROADS    + 'light-square.glb',  'misc'),
        ('path-short', SUBURBAN + 'path-short.glb',    'misc'),
        ('path-long',  SUBURBAN + 'path-long.glb',     'misc'),
    ]),
]

# ──────────────────────────────────────────────────────────────────────
#  앱 초기화
# ──────────────────────────────────────────────────────────────────────
app = Ursina(title='맵 에디터', borderless=False, size=(1280, 720), development_mode=False)
Text.default_font = 'assets/malgun.ttf'
render.setShaderAuto()   # vertex color 모델(NATURE 에셋 등) 정상 렌더링

# 하늘 배경색 — 어두운 회색 (모델 구분 쉽게)
camera.background_color = color.rgb(45, 45, 50)

# ─── 체커보드 텍스처 생성 ─────────────────────────────────────────────
def _make_checker_texture(size=128, cell=32,
                          c1=(210, 210, 215), c2=(175, 175, 180)):
    """PIL로 체커보드 이미지를 만들어 임시 파일로 저장 후 경로 반환"""
    img = PILImage.new('RGB', (size, size))
    for y in range(size):
        for x in range(size):
            if (x // cell + y // cell) % 2 == 0:
                img.putpixel((x, y), c1)
            else:
                img.putpixel((x, y), c2)
    path = 'assets/textures/_editor_checker.png'
    img.save(path)
    return path

_checker_path = _make_checker_texture()

# ─── 씬 ───────────────────────────────────────────────────────────────
ground = Entity(
    model='plane', scale=100,
    texture=_checker_path,
    texture_scale=(50, 50),   # 타일 촘촘하게
    collider='mesh',
    name='ground',
)

# 그리드 (G 키로 토글)
_grid_root = Entity()
for _i in range(-20, 21, 2):
    Entity(parent=_grid_root, model='cube',
           scale=(40, 0.01, 0.02), position=(0, 0.01, _i),
           color=color.rgba(80, 80, 255, 80), unlit=True)
    Entity(parent=_grid_root, model='cube',
           scale=(0.02, 0.01, 40), position=(_i, 0.01, 0),
           color=color.rgba(80, 80, 255, 80), unlit=True)

# 배치 위치 인디케이터
_indicator = Entity(
    model='quad', rotation=(90, 0, 0),
    scale=1.8, color=color.rgba(80, 200, 255, 170),
    unlit=True, enabled=False,
)

# ─── 카메라 (직접 제어) ───────────────────────────────────────────────
camera.position = Vec3(0, 40, -15)
camera.rotation = Vec3(65, 0, 0)   # 65° 아래로 내려다보기

_CAM_PAN_SPEED  = 25
_CAM_ZOOM_STEP  = 5
_CAM_ROT_SPEED  = 80

# ──────────────────────────────────────────────────────────────────────
#  미리보기 오프스크린 버퍼
# ──────────────────────────────────────────────────────────────────────
_PREV_SIZE = 210

_fbp = FrameBufferProperties()
_fbp.set_rgb_color(True)
_fbp.set_alpha_bits(8)
_fbp.set_depth_bits(1)

_prev_buf = base.graphics_engine.make_output(
    base.pipe, 'preview_buf', -100,
    _fbp, WindowProperties.size(_PREV_SIZE, _PREV_SIZE),
    GraphicsPipe.BF_refuse_window,
    base.win.get_gsg(), base.win,
)
_prev_buf.set_clear_color_active(True)
_prev_buf.set_clear_color(LColor(0.12, 0.12, 0.15, 1))

_prev_tex = P3DTexture('preview_tex')
_prev_buf.add_render_texture(_prev_tex, GraphicsOutput.RTM_bind_or_copy)

# 미리보기 전용 씬 (메인 렌더와 완전 분리)
_ps = NodePath('prev_scene')

_al = AmbientLight('al')
_al.set_color(LColor(0.45, 0.45, 0.45, 1))
_ps.set_light(_ps.attach_new_node(_al))

_dl = DirectionalLight('dl')
_dl.set_color(LColor(1.0, 0.92, 0.8, 1))
_dl_np = _ps.attach_new_node(_dl)
_dl_np.set_hpr(40, -45, 0)
_ps.set_light(_dl_np)

# 미리보기 카메라
_pc     = P3DCamera('prev_cam')
_pl     = PerspectiveLens()
_pl.set_fov(45)
_pl.set_aspect_ratio(1)
_pc.set_lens(_pl)
_pc_np  = _ps.attach_new_node(_pc)
_pc_np.set_pos(0, 2, -4)
_pc_np.look_at(LPoint3(0, 0, 0), LVector3(0, 0, 1))
_prev_buf.make_display_region().set_camera(_pc_np)

_prev_wrapper = None   # 현재 미리보기 모델을 담는 NodePath
_prev_rot_y   = 0.0    # 자동 회전 각도


def _update_preview():
    """현재 선택된 모델을 미리보기 씬에 로드"""
    global _prev_wrapper
    if _prev_wrapper:
        _prev_wrapper.remove_node()
        _prev_wrapper = None
    _, path, _ = _cur_item()
    try:
        np = loader.load_model(path)
        wrapper = _ps.attach_new_node('wrapper')
        np.reparent_to(wrapper)
        # 바운딩 박스 기준 자동 스케일 & 중앙 정렬
        b = np.get_tight_bounds()
        if b:
            mn, mx = b
            center = (mn + mx) * 0.5
            size   = max((mx - mn).length(), 0.001)
            np.set_pos(-center.x, -center.y, -center.z)
            wrapper.set_scale(3.0 / size)
        _prev_wrapper = wrapper
    except Exception as e:
        print(f'[preview] 로드 실패: {e}')

# ──────────────────────────────────────────────────────────────────────
#  에디터 상태
# ──────────────────────────────────────────────────────────────────────
_cat_idx   = 0
_model_idx = 0
_rot_y     = 0
_placed    = []


def _cur_models():
    return PALETTE[_cat_idx][1]


def _cur_item():
    models = _cur_models()
    return models[_model_idx % len(models)]


# ──────────────────────────────────────────────────────────────────────
#  UI
# ──────────────────────────────────────────────────────────────────────

# ── 공통 색 상수 ──────────────────────────────────────────────────────
# ── 공통 색 상수 (Ursina: 0~1 범위) ──────────────────────────────────
_C_BG     = Vec4(0.39, 0.71, 1.0, 0.45)   # 하늘색 반투명 배경
_C_BORDER = Vec4(0.20, 0.50, 0.90, 0.85)  # 진한 파랑 테두리
_C_TITLE  = Vec4(0.0,  0.0,  0.5,  1.0)   # 진한 파랑 (제목)
_C_KEY    = Vec4(0.0,  0.15, 0.6,  1.0)   # 파랑 (단축키)
_C_DESC   = Vec4(0.05, 0.05, 0.2,  1.0)   # 거의 검정 (설명)
_C_INFO   = Vec4(0.0,  0.0,  0.3,  1.0)   # 진한 남색 (상단 정보)

def _panel(parent, w, h, cx, cy, thickness=0.003):
    """하늘색 반투명 배경 + 테두리 생성"""
    Entity(parent=parent, model='quad',
           scale=(w, h), position=(cx, cy, 1),
           color=_C_BG, unlit=True)
    for sw, sh, px, py in [
        (w, thickness, cx,     cy+h/2),
        (w, thickness, cx,     cy-h/2),
        (thickness, h, cx-w/2, cy    ),
        (thickness, h, cx+w/2, cy    ),
    ]:
        Entity(parent=parent, model='quad',
               scale=(sw, sh), position=(px, py, -0.5),
               color=_C_BORDER, unlit=True)

# ── 상단: 현재 선택 모델 정보 ──────────────────────────────────────────
_panel(camera.ui, 0.85, 0.1, -0.11, 0.445)

_info_txt = Text(
    parent=camera.ui, text='',
    position=(-0.51, 0.468, -1),
    scale=1.1, color=_C_INFO, origin=(-0.5, 0.5),
)

# ── 우측: 단축키 패널 (H 키로 토글) ──────────────────────────────────
_PX   = 0.66
_PW   = 0.42
_XL   = _PX - _PW * 0.5 + 0.01
_XR   = _PX

_help_panel = Entity(parent=camera.ui)

_panel(_help_panel, _PW, 0.74, _PX, 0.02)

# 제목
Text(parent=_help_panel,
     text='단축키      [H] 숨기기',
     position=(_XL, 0.375, -1),
     scale=1.05, color=_C_TITLE, origin=(-0.5, 0.5))

# 구분선
Entity(parent=_help_panel, model='quad',
       scale=(_PW - 0.02, 0.002), position=(_PX, 0.348, -1),
       color=color.rgba(255, 255, 255, 60), unlit=True)

_HELP_LINES = [
    ('카메라', None),
    ('W / S',        '앞뒤 이동'),
    ('A / D',        '좌우 이동'),
    ('스크롤',        '줌 인/아웃'),
    ('우클릭+드래그', '시점 회전'),
    ('', None),
    ('오브젝트', None),
    ('1 ~ 6',        '카테고리 선택'),
    ('[ / ]',        '모델 순환'),
    ('R',            '90° 회전'),
    ('좌클릭',        '오브젝트 배치'),
    ('Del / X',      '가까운 것 삭제'),
    ('Z',            '배치 취소'),
    ('', None),
    ('파일', None),
    ('S',            '저장'),
    ('L',            '불러오기'),
    ('G',            '그리드 토글'),
]

_LINE_H  = 0.033
_START_Y = 0.33

for i, (key, desc) in enumerate(_HELP_LINES):
    y = _START_Y - i * _LINE_H
    if desc is None:
        if key:
            Text(parent=_help_panel, text=key,
                 position=(_XL, y, -1),
                 scale=1.0, color=_C_TITLE, origin=(-0.5, 0.5))
    else:
        Text(parent=_help_panel, text=key,
             position=(_XL, y, -1),
             scale=0.95, color=_C_KEY, origin=(-0.5, 0.5))
        Text(parent=_help_panel, text=desc,
             position=(_XR, y, -1),
             scale=0.95, color=_C_DESC, origin=(-0.5, 0.5))

# ── 좌하단: 미리보기 패널 ─────────────────────────────────────────────
_panel(camera.ui, 0.25, 0.32, -0.745, -0.32)

Text(parent=camera.ui, text='미리보기',
     position=(-0.86, -0.165, -1),
     scale=1.0, color=_C_TITLE, origin=(-0.5, 0.5))

_prev_display = Entity(
    parent=camera.ui,
    model='quad',
    scale=(0.23, 0.23),
    position=(-0.745, -0.335, -1),
)
# Ursina 텍스처 래퍼를 우회해 panda3d 텍스처 직접 적용
_prev_display.model.setTexture(_prev_tex, 1)

# ── 하단 중앙: 상태 메시지 ─────────────────────────────────────────────
_status_txt = Text(
    parent=camera.ui, text='',
    position=(0, -0.46),
    scale=1.3, color=color.lime, origin=(0, -0.5),
)


def _show_status(msg, col=color.lime):
    _status_txt.text  = msg
    _status_txt.color = col
    invoke(lambda: setattr(_status_txt, 'text', ''), delay=2.5)


def _refresh_ui():
    cat_name, models = PALETTE[_cat_idx]
    idx    = _model_idx % len(models)
    m_name = models[idx][0]
    _info_txt.text = (
        f'카테고리: {cat_name}  ({_cat_idx + 1}/{len(PALETTE)})\n'
        f'모델: {m_name}  [{idx + 1}/{len(models)}]   '
        f'회전: {_rot_y}°   배치 수: {len(_placed)}'
    )
    _update_preview()


# ──────────────────────────────────────────────────────────────────────
#  배치 / 삭제
# ──────────────────────────────────────────────────────────────────────
def _place():
    if not mouse.world_point:
        return
    name, path, skey = _cur_item()
    sc      = SC[skey]                          # 저장용 (게임과 동일)
    mult    = SC_DISPLAY_MULT[skey]
    sc_disp = tuple(v * mult for v in sc)       # 에디터 표시용 (크게)
    px  = round(mouse.world_point.x / GRID_SNAP) * GRID_SNAP
    pz  = round(mouse.world_point.z / GRID_SNAP) * GRID_SNAP
    ent = Entity(model=path, position=(px, 0, pz),
                 scale=sc_disp, rotation_y=_rot_y)
    ent.model.setColorOff()   # Ursina 기본 색 덮어쓰기 해제 → vertex color 표시
    _placed.append((ent, {
        'name': name, 'model': path,
        'pos':  [px, 0, pz],
        'scale': list(sc),      # JSON엔 원래 스케일 저장
        'rot_y': _rot_y,
    }))
    _refresh_ui()


def _delete_nearest():
    if not _placed or not mouse.world_point:
        return
    mp     = Vec3(mouse.world_point.x, 0, mouse.world_point.z)
    target = min(_placed, key=lambda x: (Vec3(*x[1]['pos']) - mp).length())
    if (Vec3(*target[1]['pos']) - mp).length() < 3.0:
        _placed.remove(target)
        destroy(target[0])
        _refresh_ui()
        _show_status('삭제됨', color.orange)


def _undo():
    if _placed:
        ent, _ = _placed.pop()
        destroy(ent)
        _refresh_ui()
        _show_status('실행 취소', color.yellow)


# ──────────────────────────────────────────────────────────────────────
#  저장 / 불러오기
# ──────────────────────────────────────────────────────────────────────
def _save():
    os.makedirs('game', exist_ok=True)
    with open(SAVE_PATH, 'w', encoding='utf-8') as f:
        json.dump({'objects': [d for _, d in _placed]}, f,
                  ensure_ascii=False, indent=2)
    _show_status(f'저장 완료  {len(_placed)}개 → {SAVE_PATH}')


def _load():
    if not os.path.exists(SAVE_PATH):
        _show_status('저장 파일이 없습니다', color.orange)
        return
    for ent, _ in _placed:
        destroy(ent)
    _placed.clear()
    with open(SAVE_PATH, encoding='utf-8') as f:
        data = json.load(f)
    for obj in data.get('objects', []):
        # 팔레트에서 skey 찾기 → 표시용 배율 적용
        skey = 'misc'
        for _, models in PALETTE:
            for n, p, sk in models:
                if p == obj['model']:
                    skey = sk
                    break
        mult    = SC_DISPLAY_MULT.get(skey, 1.0)
        sc_disp = [v * mult for v in obj['scale']]
        ent = Entity(model=obj['model'], position=obj['pos'],
                     scale=sc_disp, rotation_y=obj['rot_y'])
        ent.model.setColorOff()
        _placed.append((ent, obj))
    _refresh_ui()
    _show_status(f'불러오기 완료  {len(_placed)}개')


# ──────────────────────────────────────────────────────────────────────
#  입력 처리
# ──────────────────────────────────────────────────────────────────────
def input(key):
    global _cat_idx, _model_idx, _rot_y

    # 카테고리 선택
    if key in '123456':
        idx = int(key) - 1
        if idx < len(PALETTE):
            _cat_idx   = idx
            _model_idx = 0
            _refresh_ui()

    # 모델 순환
    elif key == ']':
        _model_idx += 1
        _refresh_ui()
    elif key == '[':
        _model_idx -= 1
        _refresh_ui()

    # 회전
    elif key == 'r':
        _rot_y = (_rot_y + 90) % 360
        _refresh_ui()

    # 배치
    elif key == 'left mouse down':
        if not held_keys['right mouse']:   # 우클릭 회전 중엔 배치 무시
            if mouse.hovered_entity and mouse.hovered_entity.name == 'ground':
                _place()

    # 삭제
    elif key in ('delete', 'x'):
        _delete_nearest()

    # 실행취소
    elif key == 'z':
        _undo()

    # 그리드 토글
    elif key == 'g':
        _grid_root.enabled = not _grid_root.enabled

    # 단축키 패널 토글
    elif key == 'h':
        _help_panel.enabled = not _help_panel.enabled

    # 줌 (스크롤)
    elif key == 'scroll up':
        camera.position -= Vec3(0, _CAM_ZOOM_STEP, -_CAM_ZOOM_STEP * 0.5)
    elif key == 'scroll down':
        camera.position += Vec3(0, _CAM_ZOOM_STEP, -_CAM_ZOOM_STEP * 0.5)

    # 저장 / 불러오기
    elif key == 's':
        _save()
    elif key == 'l':
        _load()


# ──────────────────────────────────────────────────────────────────────
#  매 프레임
# ──────────────────────────────────────────────────────────────────────
def update():
    dt = time.dt

    # ── WASD 카메라 이동 (카메라 회전 방향 무시, 월드 XZ 기준) ──
    if held_keys['w']:
        camera.position += Vec3(0, 0,  _CAM_PAN_SPEED * dt)
    if held_keys['s']:
        camera.position += Vec3(0, 0, -_CAM_PAN_SPEED * dt)
    if held_keys['a']:
        camera.position += Vec3(-_CAM_PAN_SPEED * dt, 0, 0)
    if held_keys['d']:
        camera.position += Vec3( _CAM_PAN_SPEED * dt, 0, 0)

    # ── 우클릭 드래그 — 카메라 회전 ──
    if held_keys['right mouse']:
        camera.rotation_y += mouse.velocity[0] * _CAM_ROT_SPEED
        camera.rotation_x -= mouse.velocity[1] * _CAM_ROT_SPEED
        camera.rotation_x  = clamp(camera.rotation_x, 10, 89)

    # ── 미리보기 모델 천천히 회전 ──
    global _prev_rot_y
    if _prev_wrapper:
        _prev_rot_y += 40 * dt
        _prev_wrapper.set_h(_prev_rot_y)

    # ── 인디케이터 업데이트 ──
    on_ground = (mouse.hovered_entity is not None
                 and mouse.hovered_entity.name == 'ground'
                 and mouse.world_point is not None)
    if on_ground:
        px = round(mouse.world_point.x / GRID_SNAP) * GRID_SNAP
        pz = round(mouse.world_point.z / GRID_SNAP) * GRID_SNAP
        _indicator.position = (px, 0.02, pz)
    _indicator.enabled = on_ground


# ─── 시작 ─────────────────────────────────────────────────────────────
_refresh_ui()
_show_status('에디터 준비 완료  |  WASD 이동  스크롤 줌  우클릭드래그 회전')
app.run()
