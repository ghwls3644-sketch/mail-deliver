from ursina import *

STEPS = {
    'letter':  ('빨간 우체통에 가서 편지를 넣으세요',   color.red),
    'parcel':  ('박씨 집 앞에서 소포를 놓으세요',        color.rgb(200, 140, 80)),
    'express': ('이청년에게 직접 등기를 전달하세요',      color.yellow),
}


class UI:
    def __init__(self, mails):
        self.mails = mails

        # ── 배달 목록 (좌상단) ────────────────────────────────────────
        Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgba(0, 0, 0, 160),
            scale=(0.38, 0.28),
            position=(-0.60, 0.36)
        )
        Text('[ 오늘의 배달 ]', parent=camera.ui,
             position=(-0.75, 0.44), scale=1.1, color=color.yellow)
        self.mail_texts = []
        self._build_mail_list()

        # ── 조작 안내 (하단) ─────────────────────────────────────────
        Text('WASD : 이동       E : 상호작용',
             parent=camera.ui, position=(0, -0.46),
             scale=1.0, origin=(0, 0), color=color.rgba(255, 255, 255, 180))

        # ── 튜토리얼 단계 표시 (상단 중앙) ──────────────────────────
        self.step_bg = Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgba(0, 0, 0, 180),
            scale=(0.70, 0.08),
            position=(0, 0.43)
        )
        self.step_text = Text(
            '',
            parent=camera.ui,
            position=(0, 0.43),
            scale=1.1,
            origin=(0, 0),
            color=color.white
        )

        # ── 완료 패널 (처음엔 숨김) ──────────────────────────────────
        self._complete_shown = False

    # ── 내부 ──────────────────────────────────────────────────────────

    def _build_mail_list(self):
        for t in self.mail_texts:
            destroy(t)
        self.mail_texts = []
        for i, mail in enumerate(self.mails):
            col = color.gray if mail.delivered else mail.mail_color
            t = Text(
                mail.label,
                parent=camera.ui,
                position=(-0.75, 0.38 - i * 0.075),
                scale=0.9,
                color=col
            )
            self.mail_texts.append(t)

    # ── 매 프레임 갱신 ────────────────────────────────────────────────

    def update(self, mails):
        # 배달 목록 색 갱신
        for i, mail in enumerate(mails):
            if i < len(self.mail_texts):
                self.mail_texts[i].text  = mail.label
                self.mail_texts[i].color = color.gray if mail.delivered else mail.mail_color

        # 튜토리얼 단계 텍스트 갱신
        pending = [m for m in mails if not m.delivered]
        if pending:
            m = pending[0]
            hint, col = STEPS.get(m.mail_type, ('배달을 완료하세요', color.white))
            delivered_count = sum(1 for x in mails if x.delivered)
            self.step_text.text  = f'[ {delivered_count + 1} / {len(mails)} ]  {hint}'
            self.step_text.color = col
        else:
            self.step_text.text = ''

    # ── 완료 화면 ─────────────────────────────────────────────────────

    def show_complete(self, mails, on_restart):
        if self._complete_shown:
            return
        self._complete_shown = True

        self.step_bg.enabled  = False
        self.step_text.enabled = False

        panel = Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgba(20, 20, 40, 230),
            scale=(0.60, 0.55)
        )
        Text('배달 완료!', parent=camera.ui,
             position=(0, 0.20), scale=2.2, origin=(0, 0), color=color.yellow)
        Text('수고했어요 :)', parent=camera.ui,
             position=(0, 0.10), scale=1.3, origin=(0, 0), color=color.white)

        for i, m in enumerate(mails):
            Text(
                f'✓  [{m.type_name}]  {m.recipient}  —  {m.address_hint}',
                parent=camera.ui,
                position=(0, 0.00 - i * 0.08),
                scale=1.0, origin=(0, 0),
                color=color.rgb(140, 220, 140)
            )

        btn = Button(
            text='다시 하기',
            parent=camera.ui,
            position=(0, -0.20),
            scale=(0.22, 0.07),
            color=color.azure
        )
        btn.on_click = on_restart
