from ursina import *
from PIL import Image, ImageDraw
import os


# ── 둥근 버튼 이미지 생성 및 저장 ────────────────────────────────
BTN_DIR = 'assets/textures/ui/'


def _make_round_btn(filename, base_rgb, w=512, h=128, radius=50):
    """둥근 사각형 버튼 이미지를 파일로 저장"""
    path = BTN_DIR + filename
    if os.path.exists(path):
        return path

    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 그림자
    shadow_rgb = tuple(max(0, c - 60) for c in base_rgb)
    draw.rounded_rectangle([(2, 8), (w - 2, h - 2)], radius=radius,
                           fill=shadow_rgb + (255,))

    # 메인 바디
    draw.rounded_rectangle([(2, 2), (w - 2, h - 10)], radius=radius,
                           fill=base_rgb + (255,))

    # 상단 하이라이트
    hl_rgb = tuple(min(255, c + 40) for c in base_rgb)
    draw.rounded_rectangle([(6, 4), (w - 6, h // 2 - 2)], radius=radius - 4,
                           fill=hl_rgb + (160,))

    img.save(path)
    return path


def _make_btn_set():
    """모든 버튼 텍스처 생성"""
    os.makedirs(BTN_DIR, exist_ok=True)
    return {
        'blue':     _make_round_btn('btn_blue.png',     (40, 100, 180)),
        'blue_hl':  _make_round_btn('btn_blue_hl.png',  (55, 125, 215)),
        'green':    _make_round_btn('btn_green.png',    (50, 140, 70)),
        'green_hl': _make_round_btn('btn_green_hl.png', (65, 165, 90)),
        'gray':     _make_round_btn('btn_gray.png',     (70, 80, 100)),
        'gray_hl':  _make_round_btn('btn_gray_hl.png',  (90, 100, 120)),
        'red':      _make_round_btn('btn_red.png',      (160, 55, 55)),
        'red_hl':   _make_round_btn('btn_red_hl.png',   (190, 75, 75)),
    }


_btn_tex = None


def _get_tex():
    global _btn_tex
    if _btn_tex is None:
        _btn_tex = _make_btn_set()
    return _btn_tex


def _styled_btn(text, parent, position, scale, style, on_click, elements):
    """둥근 텍스처 버튼"""
    tex = _get_tex()
    tex_normal = tex[style]
    tex_hover = tex[style + '_hl']

    btn = Button(
        text=text,
        parent=parent,
        position=position,
        scale=scale,
        texture=tex_normal,
        color=color.white,
        highlight_color=color.white,
        text_color=color.rgb(255, 255, 255),
    )
    btn.on_click = on_click
    elements.append(btn)

    def _on_mouse_enter():
        btn.texture = tex_hover
    def _on_mouse_exit():
        btn.texture = tex_normal
    btn.on_mouse_enter = _on_mouse_enter
    btn.on_mouse_exit = _on_mouse_exit
    return btn


# ── 공통 색상 ────────────────────────────────────────────────
PANEL_DARK  = color.rgba(20, 25, 45, 245)
TEXT_LIGHT  = color.rgb(230, 230, 240)
TEXT_ACCENT = color.rgb(255, 210, 100)


class TitleScreen:
    """타이틀 화면 — 시작하기 / 설정 / 크레딧"""

    def __init__(self, on_start):
        self._on_start = on_start
        self._elements = []
        self._settings_panel = None
        self._credits_panel = None
        self._build_main()

    # ── 메인 타이틀 ──────────────────────────────────────────

    def _build_main(self):
        # 배경 이미지 (cover 방식)
        img_ratio = 1536 / 1024
        scale_y = max(1.0, window.aspect_ratio / img_ratio)
        scale_x = scale_y * img_ratio
        bg = Entity(
            parent=camera.ui,
            model='quad',
            texture='img/title.png',
            scale=(scale_x, scale_y),
        )
        self._elements.append(bg)

        # 버튼들
        _styled_btn('시작하기', camera.ui, (0, -0.22), (0.30, 0.08),
                     'blue', self._start_game, self._elements)
        _styled_btn('설정', camera.ui, (0, -0.32), (0.30, 0.08),
                     'green', self._show_settings, self._elements)
        _styled_btn('크레딧', camera.ui, (0, -0.42), (0.30, 0.08),
                     'gray', self._show_credits, self._elements)

    # ── 시작 ─────────────────────────────────────────────────

    def _start_game(self):
        self.destroy()
        self._on_start()

    # ── 설정 패널 ────────────────────────────────────────────

    def _show_settings(self):
        if self._settings_panel:
            return
        els = []

        bg = Entity(
            parent=camera.ui, model='quad',
            color=PANEL_DARK,
            scale=(0.65, 0.55),
        )
        els.append(bg)

        els.append(Text(
            '설정', parent=camera.ui,
            position=(0, 0.20), origin=(0, 0),
            scale=2.2, color=TEXT_ACCENT,
        ))

        # BGM 볼륨
        els.append(Text(
            'BGM 볼륨', parent=camera.ui,
            position=(-0.15, 0.10), origin=(0, 0),
            scale=1.1, color=TEXT_LIGHT,
        ))
        els.append(Entity(
            parent=camera.ui, model='quad',
            color=color.rgb(50, 50, 70),
            scale=(0.25, 0.025),
            position=(0.10, 0.10),
        ))

        # 효과음 볼륨
        els.append(Text(
            '효과음 볼륨', parent=camera.ui,
            position=(-0.15, 0.03), origin=(0, 0),
            scale=1.1, color=TEXT_LIGHT,
        ))
        els.append(Entity(
            parent=camera.ui, model='quad',
            color=color.rgb(50, 50, 70),
            scale=(0.25, 0.025),
            position=(0.10, 0.03),
        ))

        # 조작 안내
        els.append(Text(
            '[ 조작 안내 ]', parent=camera.ui,
            position=(0, -0.06), origin=(0, 0),
            scale=1.1, color=TEXT_ACCENT,
        ))
        els.append(Text(
            'WASD : 이동       E : 상호작용',
            parent=camera.ui,
            position=(0, -0.14), origin=(0, 0),
            scale=1.0, color=TEXT_LIGHT,
        ))

        _styled_btn('닫기', camera.ui, (0, -0.22), (0.20, 0.065),
                     'red', self._close_settings, els)

        self._settings_panel = els

    def _close_settings(self):
        if self._settings_panel:
            for e in self._settings_panel:
                destroy(e)
            self._settings_panel = None

    # ── 크레딧 패널 ──────────────────────────────────────────

    def _show_credits(self):
        if self._credits_panel:
            return
        els = []

        bg = Entity(
            parent=camera.ui, model='quad',
            color=PANEL_DARK,
            scale=(0.65, 0.50),
        )
        els.append(bg)

        els.append(Text(
            '크레딧', parent=camera.ui,
            position=(0, 0.18), origin=(0, 0),
            scale=2.2, color=TEXT_ACCENT,
        ))

        credits_text = (
            '개발\n'
            '  ghwls3644\n'
            '\n'
            '3D 에셋 (CC0)\n'
            '  Kenney - City Kit Suburban\n'
            '  Kenney - City Kit Roads\n'
            '  Kenney - City Kit Commercial\n'
            '  Kenney - Nature Kit\n'
            '  Kenney - Car Kit\n'
            '  Kenney - Mini Characters\n'
            '\n'
            '엔진\n'
            '  Ursina Engine (Python)'
        )
        els.append(Text(
            credits_text, parent=camera.ui,
            position=(0, 0.08), origin=(0, 0),
            scale=0.9, color=TEXT_LIGHT,
        ))

        _styled_btn('닫기', camera.ui, (0, -0.20), (0.20, 0.065),
                     'red', self._close_credits, els)

        self._credits_panel = els

    def _close_credits(self):
        if self._credits_panel:
            for e in self._credits_panel:
                destroy(e)
            self._credits_panel = None

    # ── 전체 제거 ────────────────────────────────────────────

    def destroy(self):
        self._close_settings()
        self._close_credits()
        for e in self._elements:
            destroy(e)
        self._elements.clear()
