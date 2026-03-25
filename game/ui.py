from ursina import *

class UI:
    def __init__(self, mails, game, npcs=None):
        self.mails = mails
        self.game  = game
        self.npcs  = npcs or []   # NPC 친밀도 패널용

        # ── 배달 목록 패널 (좌상단) ──────────────────────────
        self.list_bg = Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgba(0, 0, 0, 160),
            scale=(0.38, 0.35),
            position=(-0.62, 0.32)
        )
        self.list_title = Text(
            '📬 오늘의 배달 목록',
            parent=camera.ui,
            position=(-0.77, 0.42),
            scale=1.1,
            color=color.yellow
        )
        self.mail_texts = []
        self._build_mail_list()

        # ── 시계 (우상단) ────────────────────────────────────
        self.clock_text = Text(
            '오전 9:00',
            parent=camera.ui,
            position=(0.55, 0.45),
            scale=1.3,
            color=color.white
        )

        # ── 조작 안내 (하단) ─────────────────────────────────
        # 참조 저장 — _on_next_day에서 실수로 삭제되지 않도록
        self.hint_text = Text(
            'WASD: 이동   E: 상호작용',
            parent=camera.ui,
            position=(0, -0.47),
            scale=1.0,
            color=color.rgba(255, 255, 255, 180)
        )

        # ── 주민 친밀도 패널 (우하단) ────────────────────────
        self.relation_bg = Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgba(0, 0, 0, 150),
            scale=(0.28, 0.30),
            position=(0.62, -0.22)
        )
        self.relation_title = Text(
            '👥 주민 관계',
            parent=camera.ui,
            position=(0.49, -0.09),
            scale=1.0,
            color=color.yellow
        )
        self.relation_texts = []
        self._build_relation_list()

        # ── 일기 화면 (저녁 귀환 시) ─────────────────────────
        self.diary_panel = None

    # ── 배달 목록 갱신 ──────────────────────────────────────
    def _build_mail_list(self):
        for t in self.mail_texts:
            destroy(t)
        self.mail_texts = []

        for i, mail in enumerate(self.mails):
            col = mail.mail_color if not mail.delivered else color.gray
            t = Text(
                mail.label,
                parent=camera.ui,
                position=(-0.77, 0.36 - i * 0.07),
                scale=0.9,
                color=col
            )
            self.mail_texts.append(t)

    # ── 친밀도 목록 갱신 ─────────────────────────────────────
    def _build_relation_list(self):
        for t in self.relation_texts:
            destroy(t)
        self.relation_texts = []

        for i, npc in enumerate(self.npcs):
            stars = '★' * npc.relation + '☆' * (2 - npc.relation)
            col   = [color.gray, color.yellow, color.lime][npc.relation]
            t = Text(
                f'{npc.name}  {stars}',
                parent=camera.ui,
                position=(0.49, -0.15 - i * 0.06),
                scale=0.85,
                color=col
            )
            self.relation_texts.append(t)

    def refresh(self, mails):
        self.mails = mails
        self._build_mail_list()

    # ── 시계 업데이트 ────────────────────────────────────────
    def update_clock(self, t):
        # t: 0.0 = 오전 9시, 1.0 = 오후 6시 (9시간)
        total_minutes = int(t * 9 * 60)
        hour   = 9 + total_minutes // 60
        minute = total_minutes % 60
        period = '오전' if hour < 12 else '오후'
        display_hour = hour if hour <= 12 else hour - 12
        self.clock_text.text = f'{period} {display_hour}:{minute:02d}'

        # 배달 완료 여부 반영 (색상 갱신)
        for i, mail in enumerate(self.mails):
            if i < len(self.mail_texts):
                self.mail_texts[i].text  = mail.label
                self.mail_texts[i].color = color.gray if mail.delivered else mail.mail_color

        # 친밀도 패널 갱신 (매 프레임 — 가벼운 텍스트 업데이트)
        for i, npc in enumerate(self.npcs):
            if i < len(self.relation_texts):
                stars = '★' * npc.relation + '☆' * (2 - npc.relation)
                col   = [color.gray, color.yellow, color.lime][npc.relation]
                self.relation_texts[i].text  = f'{npc.name}  {stars}'
                self.relation_texts[i].color = col

    # ── 일기 화면 ────────────────────────────────────────────
    def show_diary(self, day_count, mails):
        done  = sum(1 for m in mails if m.delivered)
        total = len(mails)

        # 우편물 수에 따라 패널 높이 조절 (최대 5개까지 표시)
        visible = min(len(mails), 5)
        panel_h = 0.72 + visible * 0.02

        self.diary_panel = Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgba(20, 20, 40, 220),
            scale=(0.72, panel_h)
        )

        # 제목
        Text(
            f'📖 {day_count}일차 일기',
            parent=camera.ui,
            position=(0, 0.30),
            scale=1.8,
            color=color.yellow,
            origin=(0, 0)
        )

        # 배달 요약
        Text(
            f'오늘 배달: {done} / {total}',
            parent=camera.ui,
            position=(0, 0.21),
            scale=1.2,
            color=color.white,
            origin=(0, 0)
        )

        # 우편물 항목 목록 (최대 5개, 초과 시 "외 N건" 표시)
        display_mails = mails[:5]
        for i, m in enumerate(display_mails):
            check = '✓' if m.delivered else '□'
            col   = color.rgb(140, 220, 140) if m.delivered else color.rgb(160, 160, 160)
            Text(
                f'{check}  {m.recipient}   {m.type_name}',
                parent=camera.ui,
                position=(0, 0.13 - i * 0.075),
                scale=1.05,
                color=col,
                origin=(0, 0)
            )
        if len(mails) > 5:
            Text(
                f'... 외 {len(mails) - 5}건',
                parent=camera.ui,
                position=(0, 0.13 - 5 * 0.075),
                scale=0.95,
                color=color.gray,
                origin=(0, 0)
            )

        # 오늘의 일기 한 줄 — 수신인 이름 포함
        comment_y = 0.13 - visible * 0.075 - 0.07
        diary_line = self._diary_comment(mails)
        Text(
            diary_line,
            parent=camera.ui,
            position=(0, comment_y),
            scale=1.0,
            color=color.rgb(200, 200, 255),
            origin=(0, 0)
        )

        btn = Button(
            text='다음 날 →',
            parent=camera.ui,
            position=(0, comment_y - 0.12),
            scale=(0.2, 0.07),
            color=color.azure
        )
        btn.on_click = self._on_next_day

    def _on_next_day(self):
        # 일기 화면 정리 — 영구 UI 요소는 보존
        keep = {
            self.list_bg, self.list_title,
            self.clock_text, self.hint_text,
            self.relation_bg, self.relation_title,
        }
        keep.update(self.mail_texts)
        keep.update(self.relation_texts)
        for e in list(camera.ui.children):
            if isinstance(e, (Entity, Text, Button)) and e not in keep:
                destroy(e)
        self.diary_panel = None
        self.game.next_day()

    def _diary_comment(self, mails):
        delivered   = [m for m in mails if m.delivered]
        undelivered = [m for m in mails if not m.delivered]

        if not mails:
            return '오늘은 배달할 우편물이 없었다.'

        # 전부 완료
        if not undelivered:
            if len(delivered) == 1:
                return f'{delivered[0].recipient}께 전하고 나니 마음이 가벼웠다.'
            names = ', '.join(m.recipient for m in delivered)
            return f'{names}.\n오늘 받은 분들이 기뻐했으면 좋겠다.'

        # 하나도 못 함
        if not delivered:
            names = ', '.join(m.recipient for m in undelivered)
            return f'{names}께 못 전했다.\n내일은 꼭 먼저 챙겨야지.'

        # 일부 완료
        done_names = ', '.join(m.recipient for m in delivered)
        skip_names = ', '.join(m.recipient for m in undelivered)
        return f'{done_names}께는 전했다.\n{skip_names}은(는) 내일 꼭 챙겨야지.'
