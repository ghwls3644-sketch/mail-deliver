"""
editor.py — 우편배달부 맵 에디터 (독립 실행 도구)
실행: python editor.py   ← 게임과 완전히 분리됨

  카메라 조작
    [WASD]        수평 이동
    [스크롤]       줌 인/아웃
    [Ctrl+이동]   카메라 회전

  오브젝트 배치
    [1~6]   카테고리 선택
    [ / ]   같은 카테고리 내 모델 순환
    [R]     회전 (90° 단위)
    [클릭]  배치
    [Del]   커서 근처 삭제
    [Z]     실행취소
    [G]     그리드 토글

  파일
    [Ctrl+S]       빠른 저장
    [Ctrl+Shift+S] 다른 이름으로 저장
    [L]            불러오기
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
import json, os, math

# ─── 경로 상수 (map.py 와 동일) ────────────────────────────────────────
SUBURBAN   = 'assets/kenney_city-kit-suburban_20/Models/GLB format/'
ROADS      = 'assets/kenney_city-kit-roads/Models/GLB format/'
COMMERCIAL = 'assets/kenney_city-kit-commercial_2.1/Models/GLB format/'
NATURE     = 'assets/kenney_nature-kit/Models/GLTF format/'
CARS       = 'assets/kenney_car-kit/Models/GLB format/'

MAPS_DIR  = 'game/maps/'
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


class MapEditor(Entity):
    # ─── 카메라 속도 상수 ─────────────────────────────────────────────
    CAM_PAN_SPEED = 25
    CAM_ZOOM_STEP = 5
    CAM_ROT_SPEED = 80

    # ─── 경로 → skey 역조회 (로드 시 PALETTE 전체 순회 방지) ──────────
    _PATH_TO_SKEY = {p: sk for _, models in PALETTE for _, p, sk in models}

    # ─── 단축키 패널 내용 ─────────────────────────────────────────────
    HELP_LINES = [
        ('카메라', None),
        ('W / S',        '앞뒤 이동'),
        ('A / D',        '좌우 이동'),
        ('스크롤',        '줌 인/아웃'),
        ('Ctrl+이동',    '시점 회전'),
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
        ('Ctrl+S',       '빠른 저장'),
        ('Ctrl+Shift+S', '다른 이름으로 저장'),
        ('L',            '맵 불러오기'),
        ('G',            '그리드 토글'),
    ]

    def __init__(self):
        super().__init__()

        # ─── 색 상수 ──────────────────────────────────────────────────
        self.C_BG     = Vec4(0.39, 0.71, 1.0, 0.45)   # 하늘색 반투명 배경
        self.C_BORDER = Vec4(0.20, 0.50, 0.90, 0.85)  # 진한 파랑 테두리
        self.C_TITLE  = Vec4(0.0,  0.0,  0.5,  1.0)   # 진한 파랑 (제목)
        self.C_KEY    = Vec4(0.0,  0.15, 0.6,  1.0)   # 파랑 (단축키)
        self.C_DESC   = Vec4(0.05, 0.05, 0.2,  1.0)   # 거의 검정 (설명)
        self.C_INFO   = Vec4(0.0,  0.0,  0.3,  1.0)   # 진한 남색 (상단 정보)

        # ─── 에디터 상태 ──────────────────────────────────────────────
        self._cat_idx      = 0
        self._model_idx    = 0
        self._rot_y        = 0
        self._placed       = []
        self._current_map  = None   # 현재 작업 중인 맵 이름 (확장자 제외)
        self._dialog_open  = False  # 다이얼로그 열림 여부

        # ─── 저장/불러오기 다이얼로그 참조 ───────────────────────────
        self._save_dialog = None
        self._save_field  = None
        self._load_dialog = None

        # ─── 미리보기 상태 ────────────────────────────────────────────
        self._prev_wrapper = None   # 현재 미리보기 모델을 담는 NodePath
        self._prev_rot_y   = 0.0    # 자동 회전 각도

        # ─── 씬 구성 ──────────────────────────────────────────────────
        self._setup_scene()

        # ─── 미리보기 버퍼 ────────────────────────────────────────────
        self._setup_preview_buffer()

        # ─── UI 구성 ──────────────────────────────────────────────────
        self._setup_ui()

        # ─── 시작 ─────────────────────────────────────────────────────
        self._refresh_ui()
        self._show_status('에디터 준비 완료  |  WASD 이동  스크롤 줌  Ctrl+마우스 회전')

    # ──────────────────────────────────────────────────────────────────
    #  씬 초기화
    # ──────────────────────────────────────────────────────────────────
    def _setup_scene(self):
        checker_path = MapEditor._make_checker_texture()

        self._ground = Entity(
            model='plane', scale=100,
            texture=checker_path,
            texture_scale=(50, 50),
            collider='mesh',
            name='ground',
        )

        # 그리드 (G 키로 토글)
        self._grid_root = Entity()
        for i in range(-20, 21, 2):
            Entity(parent=self._grid_root, model='cube',
                   scale=(40, 0.01, 0.02), position=(0, 0.01, i),
                   color=color.rgba(80, 80, 255, 80), unlit=True)
            Entity(parent=self._grid_root, model='cube',
                   scale=(0.02, 0.01, 40), position=(i, 0.01, 0),
                   color=color.rgba(80, 80, 255, 80), unlit=True)

        # 배치 위치 인디케이터
        self._indicator = Entity(
            model='quad', rotation=(90, 0, 0),
            scale=1.8, color=color.rgba(80, 200, 255, 170),
            unlit=True, enabled=False,
        )

        # 카메라 (직접 제어)
        camera.position = Vec3(0, 40, -15)
        camera.rotation = Vec3(65, 0, 0)   # 65° 아래로 내려다보기

    # ──────────────────────────────────────────────────────────────────
    #  미리보기 오프스크린 버퍼
    # ──────────────────────────────────────────────────────────────────
    def _setup_preview_buffer(self):
        PREV_SIZE = 210

        fbp = FrameBufferProperties()
        fbp.set_rgb_color(True)
        fbp.set_alpha_bits(8)
        fbp.set_depth_bits(1)

        self._prev_buf = base.graphics_engine.make_output(
            base.pipe, 'preview_buf', -100,
            fbp, WindowProperties.size(PREV_SIZE, PREV_SIZE),
            GraphicsPipe.BF_refuse_window,
            base.win.get_gsg(), base.win,
        )
        self._prev_buf.set_clear_color_active(True)
        self._prev_buf.set_clear_color(LColor(0.12, 0.12, 0.15, 1))

        self._prev_tex = P3DTexture('preview_tex')
        self._prev_buf.add_render_texture(self._prev_tex, GraphicsOutput.RTM_bind_or_copy)

        self._ps = NodePath('prev_scene')

        al = AmbientLight('al')
        al.set_color(LColor(0.45, 0.45, 0.45, 1))
        self._ps.set_light(self._ps.attach_new_node(al))

        dl = DirectionalLight('dl')
        dl.set_color(LColor(1.0, 0.92, 0.8, 1))
        dl_np = self._ps.attach_new_node(dl)
        dl_np.set_hpr(40, -45, 0)
        self._ps.set_light(dl_np)

        pc    = P3DCamera('prev_cam')
        pl    = PerspectiveLens()
        pl.set_fov(45)
        pl.set_aspect_ratio(1)
        pc.set_lens(pl)
        pc_np = self._ps.attach_new_node(pc)
        pc_np.set_pos(0, 2, -4)
        pc_np.look_at(LPoint3(0, 0, 0), LVector3(0, 0, 1))
        self._prev_buf.make_display_region().set_camera(pc_np)

    # ──────────────────────────────────────────────────────────────────
    #  UI 구성
    # ──────────────────────────────────────────────────────────────────
    def _setup_ui(self):
        # ── 상단: 현재 선택 모델 정보 ──────────────────────────────────
        self._panel(camera.ui, 0.85, 0.1, -0.11, 0.445)

        self._info_txt = Text(
            parent=camera.ui, text='',
            position=(-0.51, 0.468, -1),
            scale=1.1, color=self.C_INFO, origin=(-0.5, 0.5),
        )

        # ── 우측: 단축키 패널 (H 키로 토글) ────────────────────────────
        PX  = 0.66
        PW  = 0.42
        XL  = PX - PW * 0.5 + 0.01
        XR  = PX

        self._help_panel = Entity(parent=camera.ui)

        self._panel(self._help_panel, PW, 0.74, PX, 0.02)

        # 제목
        Text(parent=self._help_panel,
             text='단축키      [H] 숨기기',
             position=(XL, 0.375, -1),
             scale=1.05, color=self.C_TITLE, origin=(-0.5, 0.5))

        # 구분선
        Entity(parent=self._help_panel, model='quad',
               scale=(PW - 0.02, 0.002), position=(PX, 0.348, -1),
               color=color.rgba(255, 255, 255, 60), unlit=True)

        LINE_H  = 0.033
        START_Y = 0.33

        for i, (key, desc) in enumerate(MapEditor.HELP_LINES):
            y = START_Y - i * LINE_H
            if desc is None:
                if key:
                    Text(parent=self._help_panel, text=key,
                         position=(XL, y, -1),
                         scale=1.0, color=self.C_TITLE, origin=(-0.5, 0.5))
            else:
                Text(parent=self._help_panel, text=key,
                     position=(XL, y, -1),
                     scale=0.95, color=self.C_KEY, origin=(-0.5, 0.5))
                Text(parent=self._help_panel, text=desc,
                     position=(XR, y, -1),
                     scale=0.95, color=self.C_DESC, origin=(-0.5, 0.5))

        # ── 좌하단: 미리보기 패널 ──────────────────────────────────────
        self._panel(camera.ui, 0.25, 0.32, -0.745, -0.32)

        Text(parent=camera.ui, text='미리보기',
             position=(-0.86, -0.165, -1),
             scale=1.0, color=self.C_TITLE, origin=(-0.5, 0.5))

        self._prev_display = Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.23, 0.23),
            position=(-0.745, -0.335, -1),
        )
        self._prev_display.model.setTexture(self._prev_tex, 1)

        # ── 하단 중앙: 상태 메시지 ──────────────────────────────────────
        self._status_txt = Text(
            parent=camera.ui, text='',
            position=(0, -0.46),
            scale=1.3, color=color.lime, origin=(0, -0.5),
        )

    # ──────────────────────────────────────────────────────────────────
    #  헬퍼 — 패널 생성
    # ──────────────────────────────────────────────────────────────────
    def _panel(self, parent, w, h, cx, cy, thickness=0.003):
        """하늘색 반투명 배경 + 테두리 생성"""
        Entity(parent=parent, model='quad',
               scale=(w, h), position=(cx, cy, 1),
               color=self.C_BG, unlit=True)
        for sw, sh, px, py in [
            (w, thickness, cx,     cy+h/2),
            (w, thickness, cx,     cy-h/2),
            (thickness, h, cx-w/2, cy    ),
            (thickness, h, cx+w/2, cy    ),
        ]:
            Entity(parent=parent, model='quad',
                   scale=(sw, sh), position=(px, py, -0.5),
                   color=self.C_BORDER, unlit=True)

    # ──────────────────────────────────────────────────────────────────
    #  헬퍼 — NATURE 키트 PBR 재질 변환
    # ──────────────────────────────────────────────────────────────────
    @staticmethod
    def _fix_nature_materials(root):
        """NATURE kit PBR → fixed-function 변환.
        1) 모든 하위 노드에 setShaderOff() 적용 (루트만으론 부족)
        2) baseColorFactor → diffuse/ambient 복사 (fixed-function이 쓰는 값)
        """
        from panda3d.core import Material, MaterialAttrib
        root.setShaderOff()                          # 루트에도 적용
        for np in root.findAllMatches('**'):
            np.setShaderOff()                        # 각 지오메트리 노드에도 적용
            attrib = np.getAttrib(MaterialAttrib.getClassType())
            if attrib:
                old = attrib.getMaterial()
                base = old.getBaseColor()            # GLTF baseColorFactor
                mat = Material()
                mat.setDiffuse(LColor(base[0], base[1], base[2], base[3]))
                mat.setAmbient(LColor(base[0]*0.5, base[1]*0.5, base[2]*0.5, 1))
                mat.setSpecular(LColor(0, 0, 0, 1))
                mat.setShininess(0)
                np.setMaterial(mat, 1)

    # ──────────────────────────────────────────────────────────────────
    #  헬퍼 — 체커 텍스처 생성
    # ──────────────────────────────────────────────────────────────────
    @staticmethod
    def _make_checker_texture(size=128, cell=32,
                              c1=(210, 210, 215), c2=(175, 175, 180)):
        path = 'assets/textures/_editor_checker.png'
        if os.path.exists(path):          # 이미 있으면 재생성 불필요
            return path
        img = PILImage.new('RGB', (size, size))
        for y in range(size):
            for x in range(size):
                img.putpixel((x, y), c1 if (x // cell + y // cell) % 2 == 0 else c2)
        img.save(path)
        return path

    # ──────────────────────────────────────────────────────────────────
    #  팔레트 접근
    # ──────────────────────────────────────────────────────────────────
    def _cur_models(self):
        return PALETTE[self._cat_idx][1]

    def _cur_item(self):
        models = self._cur_models()
        return models[self._model_idx % len(models)]

    # ──────────────────────────────────────────────────────────────────
    #  미리보기 업데이트
    # ──────────────────────────────────────────────────────────────────
    def _update_preview(self):
        """현재 선택된 모델을 미리보기 씬에 로드"""
        if self._prev_wrapper:
            self._prev_wrapper.remove_node()
            self._prev_wrapper = None
        _, path, _ = self._cur_item()
        try:
            np = loader.load_model(path)
            wrapper = self._ps.attach_new_node('wrapper')
            np.reparent_to(wrapper)
            b = np.get_tight_bounds()
            if b:
                mn, mx = b
                center = (mn + mx) * 0.5
                size   = max((mx - mn).length(), 0.001)
                np.set_pos(-center.x, -center.y, -center.z)
                wrapper.set_scale(3.0 / size)
            self._prev_wrapper = wrapper
        except Exception as e:
            print(f'[preview] 로드 실패: {e}')

    # ──────────────────────────────────────────────────────────────────
    #  상태 메시지
    # ──────────────────────────────────────────────────────────────────
    def _show_status(self, msg, col=color.lime):
        self._status_txt.text  = msg
        self._status_txt.color = col
        invoke(lambda: setattr(self._status_txt, 'text', ''), delay=2.5)

    # ──────────────────────────────────────────────────────────────────
    #  UI 새로고침
    # ──────────────────────────────────────────────────────────────────
    def _refresh_info(self):
        """상단 텍스트만 갱신 — 선택 모델이 바뀌지 않을 때 사용"""
        cat_name, models = PALETTE[self._cat_idx]
        idx       = self._model_idx % len(models)
        m_name    = models[idx][0]
        map_label = self._current_map if self._current_map else '(저장 안 됨)'
        self._info_txt.text = (
            f'맵: {map_label}   카테고리: {cat_name}  ({self._cat_idx + 1}/{len(PALETTE)})\n'
            f'모델: {m_name}  [{idx + 1}/{len(models)}]   '
            f'회전: {self._rot_y}°   배치 수: {len(self._placed)}'
        )

    def _refresh_ui(self):
        """텍스트 + 미리보기 갱신 — 선택 모델이 바뀔 때 사용"""
        self._refresh_info()
        self._update_preview()

    # ──────────────────────────────────────────────────────────────────
    #  배치 / 삭제
    # ──────────────────────────────────────────────────────────────────
    def _place(self):
        if not mouse.world_point:
            return
        name, path, skey = self._cur_item()
        sc      = SC[skey]                          # 저장용 (게임과 동일)
        mult    = SC_DISPLAY_MULT[skey]
        sc_disp = tuple(v * mult for v in sc)       # 에디터 표시용 (크게)
        px  = round(mouse.world_point.x / GRID_SNAP) * GRID_SNAP
        pz  = round(mouse.world_point.z / GRID_SNAP) * GRID_SNAP
        if 'kenney_nature-kit' in path:
            # Entity를 빈 컨테이너로만 사용, 모델은 raw로 붙여 색상 보존
            ent = Entity(position=(px, 0, pz), rotation_y=self._rot_y)
            raw = loader.load_model(path)
            raw.set_scale(*sc_disp)
            MapEditor._fix_nature_materials(raw)     # shader 끄기 + 재질 변환
            raw.reparent_to(ent)
        else:
            ent = Entity(model=path, position=(px, 0, pz),
                         scale=sc_disp, rotation_y=self._rot_y)
            ent.setColorOff()
        self._placed.append((ent, {
            'name': name, 'model': path,
            'pos':  [px, 0, pz],
            'scale': list(sc),      # JSON엔 원래 스케일 저장
            'rot_y': self._rot_y,
        }))
        self._refresh_info()   # 모델 선택이 바뀌지 않으므로 미리보기 재로드 불필요

    def _delete_nearest(self):
        if not self._placed or not mouse.world_point:
            return
        mp = Vec3(mouse.world_point.x, 0, mouse.world_point.z)
        # Vec3 거리를 한 번만 계산해 (target, dist) 쌍으로 탐색
        target, dist = min(
            ((item, (Vec3(*item[1]['pos']) - mp).length()) for item in self._placed),
            key=lambda x: x[1],
        )
        if dist < 3.0:
            self._placed.remove(target)
            destroy(target[0])
            self._refresh_info()
            self._show_status('삭제됨', color.orange)

    def _undo(self):
        if self._placed:
            ent, _ = self._placed.pop()
            destroy(ent)
            self._refresh_info()
            self._show_status('실행 취소', color.yellow)

    # ──────────────────────────────────────────────────────────────────
    #  저장 / 불러오기
    # ──────────────────────────────────────────────────────────────────
    def _do_save(self, name):
        """실제 파일 저장"""
        os.makedirs(MAPS_DIR, exist_ok=True)
        path = MAPS_DIR + name + '.json'
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({'objects': [d for _, d in self._placed]}, f,
                      ensure_ascii=False, indent=2)
        self._current_map = name
        self._refresh_info()
        self._show_status(f'저장 완료  {len(self._placed)}개  [{name}]')

    def _do_load(self, name):
        """실제 파일 불러오기"""
        path = MAPS_DIR + name + '.json'
        if not os.path.exists(path):
            self._show_status('파일을 찾을 수 없습니다', color.orange)
            return
        for ent, _ in self._placed:
            destroy(ent)
        self._placed.clear()
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        for obj in data.get('objects', []):
            skey    = MapEditor._PATH_TO_SKEY.get(obj['model'], 'misc')
            mult    = SC_DISPLAY_MULT.get(skey, 1.0)
            sc_disp = [v * mult for v in obj['scale']]
            if 'kenney_nature-kit' in obj['model']:
                ent = Entity(position=obj['pos'], rotation_y=obj['rot_y'])
                raw = loader.load_model(obj['model'])
                raw.set_scale(*sc_disp)
                MapEditor._fix_nature_materials(raw)
                raw.reparent_to(ent)
            else:
                ent = Entity(model=obj['model'], position=obj['pos'],
                             scale=sc_disp, rotation_y=obj['rot_y'])
                ent.setColorOff()
            self._placed.append((ent, obj))
        self._current_map = name
        self._refresh_info()
        self._show_status(f'불러오기 완료  {len(self._placed)}개  [{name}]')

    # ── 저장 다이얼로그 ────────────────────────────────────────────────
    def _open_save_dialog(self):
        if self._dialog_open:
            return
        self._dialog_open = True
        self._save_dialog = Entity(parent=camera.ui)
        # 반투명 오버레이
        Entity(parent=self._save_dialog, model='quad', scale=(2, 2),
               color=color.rgba(0, 0, 0, 140), z=2)
        self._panel(self._save_dialog, 0.52, 0.22, 0, 0)
        Text(parent=self._save_dialog, text='맵 이름 입력',
             position=(-0.24, 0.09, -3), scale=1.1, color=self.C_TITLE, origin=(-0.5, 0.5))
        Text(parent=self._save_dialog, text='Enter: 저장      Esc: 취소',
             position=(-0.24, -0.08, -3), scale=0.9, color=self.C_DESC, origin=(-0.5, 0.5))
        self._save_field = InputField(
            default_value=self._current_map or '',
            parent=self._save_dialog,
            position=(0, 0.01), scale=(0.44, 0.052), z=-3,
        )
        self._save_field.active = True

    def _close_save_dialog(self):
        if self._save_dialog:
            destroy(self._save_dialog)
            self._save_dialog = None
            self._save_field  = None
        self._dialog_open = False

    def _confirm_save(self):
        name = (self._save_field.text if self._save_field else '').strip()
        self._close_save_dialog()
        if not name:
            self._show_status('이름을 입력하세요', color.orange)
            return
        self._do_save(name)

    # ── 불러오기 다이얼로그 ────────────────────────────────────────────
    def _open_load_dialog(self):
        if self._dialog_open:
            return
        os.makedirs(MAPS_DIR, exist_ok=True)
        files = sorted(f[:-5] for f in os.listdir(MAPS_DIR) if f.endswith('.json'))
        if not files:
            self._show_status('저장된 맵이 없습니다', color.orange)
            return
        self._dialog_open = True
        self._load_dialog = Entity(parent=camera.ui)
        Entity(parent=self._load_dialog, model='quad', scale=(2, 2),
               color=color.rgba(0, 0, 0, 140), z=2)
        rows = min(len(files), 8)
        ph   = rows * 0.058 + 0.1
        self._panel(self._load_dialog, 0.52, ph, 0, 0)
        Text(parent=self._load_dialog,
             text='불러올 맵 선택      Esc: 취소',
             position=(-0.24, ph / 2 - 0.035, -3),
             scale=1.05, color=self.C_TITLE, origin=(-0.5, 0.5))
        for i, name in enumerate(files[:8]):
            y = ph / 2 - 0.075 - i * 0.058
            btn = Button(
                parent=self._load_dialog,
                text=name,
                position=(0, y, -3),
                scale=(0.46, 0.048),
                color=color.rgba(200, 220, 255, 210),
                highlight_color=color.rgba(150, 190, 255, 230),
                pressed_color=color.rgba(100, 150, 255, 255),
                text_color=self.C_TITLE,
            )
            btn.on_click = Func(self._select_map, name)

    def _select_map(self, name):
        self._close_load_dialog()
        self._do_load(name)

    def _close_load_dialog(self):
        if self._load_dialog:
            destroy(self._load_dialog)
            self._load_dialog = None
        self._dialog_open = False

    # ──────────────────────────────────────────────────────────────────
    #  입력 처리 (Ursina 자동 호출)
    # ──────────────────────────────────────────────────────────────────
    def input(self, key):
        # ── 다이얼로그 열림 중 ──
        if self._dialog_open:
            if key == 'escape':
                self._close_save_dialog()
                self._close_load_dialog()
            elif key == 'enter' and self._save_dialog:
                self._confirm_save()
            return

        # 카테고리 선택
        if key in '123456':
            idx = int(key) - 1
            if idx < len(PALETTE):
                self._cat_idx   = idx
                self._model_idx = 0
                self._refresh_ui()

        # 모델 순환
        elif key == ']':
            self._model_idx += 1
            self._refresh_ui()
        elif key == '[':
            self._model_idx -= 1
            self._refresh_ui()

        # 회전
        elif key == 'r':
            self._rot_y = (self._rot_y + 90) % 360
            self._refresh_ui()

        # 배치
        elif key == 'left mouse down':
            if not held_keys['control']:  # Ctrl 중엔 배치 무시
                if mouse.hovered_entity and mouse.hovered_entity.name == 'ground':
                    self._place()

        # 삭제
        elif key in ('delete', 'x'):
            self._delete_nearest()

        # 실행취소
        elif key == 'z':
            self._undo()

        # 그리드 토글
        elif key == 'g':
            self._grid_root.enabled = not self._grid_root.enabled

        # 단축키 패널 토글
        elif key == 'h':
            self._help_panel.enabled = not self._help_panel.enabled

        # 줌 (스크롤)
        elif key == 'scroll up':
            camera.position -= Vec3(0, MapEditor.CAM_ZOOM_STEP, -MapEditor.CAM_ZOOM_STEP * 0.5)
        elif key == 'scroll down':
            camera.position += Vec3(0, MapEditor.CAM_ZOOM_STEP, -MapEditor.CAM_ZOOM_STEP * 0.5)

        # 저장 / 불러오기
        elif key == 's' and held_keys['control']:
            if held_keys['shift']:
                self._open_save_dialog()          # Ctrl+Shift+S: 다른 이름으로 저장
            elif self._current_map:
                self._do_save(self._current_map)  # Ctrl+S: 빠른 저장
            else:
                self._open_save_dialog()          # Ctrl+S: 이름 없으면 다이얼로그
        elif key == 'l':
            self._open_load_dialog()

    # ──────────────────────────────────────────────────────────────────
    #  매 프레임 (Ursina 자동 호출)
    # ──────────────────────────────────────────────────────────────────
    def update(self):
        dt = time.dt
        if self._dialog_open:
            return

        # ── WASD 카메라 이동 (카메라 회전 방향 무시, 월드 XZ 기준) ──
        if not held_keys['control']:
            if held_keys['w']:
                camera.position += Vec3(0, 0,  MapEditor.CAM_PAN_SPEED * dt)
            if held_keys['s']:
                camera.position += Vec3(0, 0, -MapEditor.CAM_PAN_SPEED * dt)
            if held_keys['a']:
                camera.position += Vec3(-MapEditor.CAM_PAN_SPEED * dt, 0, 0)
            if held_keys['d']:
                camera.position += Vec3( MapEditor.CAM_PAN_SPEED * dt, 0, 0)

        # ── Ctrl + 마우스 이동 — 카메라 자유 회전 ──
        if held_keys['control']:
            camera.rotation_y += mouse.velocity[0] * MapEditor.CAM_ROT_SPEED
            camera.rotation_x -= mouse.velocity[1] * MapEditor.CAM_ROT_SPEED
            camera.rotation_x  = clamp(camera.rotation_x, 10, 89)

        # ── 미리보기 모델 천천히 회전 ──
        if self._prev_wrapper:
            self._prev_rot_y += 40 * time.dt
            self._prev_wrapper.set_h(self._prev_rot_y)

        # ── 인디케이터 업데이트 ──
        on_ground = (mouse.hovered_entity is not None
                     and mouse.hovered_entity.name == 'ground'
                     and mouse.world_point is not None)
        if on_ground:
            px = round(mouse.world_point.x / GRID_SNAP) * GRID_SNAP
            pz = round(mouse.world_point.z / GRID_SNAP) * GRID_SNAP
            self._indicator.position = (px, 0.02, pz)
        self._indicator.enabled = on_ground


# ─── 앱 진입점 ──────────────────────────────────────────────────────────
app = Ursina(title='맵 에디터', borderless=False, size=(1280, 720), development_mode=False)
Text.default_font = 'assets/malgun.ttf'
camera.background_color = color.rgb(45, 45, 50)
render.setShaderAuto()

editor = MapEditor()
app.run()
