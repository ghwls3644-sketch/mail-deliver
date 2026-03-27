from ursina import *

# 관계 단계 표시
RELATION_STAGES = ['낯선 사람', '아는 사이', '친구']
RELATION_COLORS  = [color.gray, color.yellow, color.lime]

# 단계별 순환 대화 목록
_DIALOGUES = {
    0: [
        '...',
        '안녕하세요.',
        '오늘도 수고하세요.',
    ],
    1: [
        '오늘 날씨 좋죠?',
        '매일 보니 반갑네요!',
        '배달 많이 힘들지 않으세요?',
    ],
    2: [
        '어서 와요, 기다리고 있었어요!',
        '이 동네 살기 좋죠? 잘 오신 것 같아요.',
        '오늘도 고마워요. 덕분에 기분이 좋아요.',
    ],
}


class NPC(Entity):
    """
    주민 NPC
    ─ E키로 말 걸기 (단계별 대화)
    ─ 등기 우편물이 있으면 직접 전달 처리
    ─ 관계 단계: 낯선 사람 → 아는 사이 → 친구
    """

    def __init__(self, npc_id, name, building_id, pos, col=color.cyan):
        super().__init__(
            model='cube',
            color=col,
            scale=(0.45, 0.9, 0.45),
            position=pos,
            collider='box'
        )
        self.npc_id      = npc_id
        self.name        = name
        self.building_id = building_id  # mail.target_id와 연결
        self.relation    = 0            # 0: 낯선 사람 / 1: 아는 사이 / 2: 친구
        self._talk_count = 0            # 일반 대화 횟수 (누적)
        self._dial_idx   = 0            # 대화 순환 인덱스
        self.interactable   = True
        self.interact_label = f'{name}에게 말 걸기'

        # 머리 — 플레이어(주황)와 구분되는 색상
        Entity(
            parent=self,
            model='sphere',
            color=col,
            scale=0.65,
            y=0.75
        )

        # 이름표 + 친밀도 별 표시
        self._name_tag = Text(
            self._tag_text(),
            parent=self,
            y=1.4,
            scale=4,
            billboard=True,
            color=RELATION_COLORS[self.relation]
        )

    # ── 내부 헬퍼 ──────────────────────────────────────────────────────────

    def _tag_text(self):
        stars = '★' * self.relation + '☆' * (2 - self.relation)
        return f'{self.name} {stars}'

    def _refresh_tag(self):
        self._name_tag.text  = self._tag_text()
        self._name_tag.color = RELATION_COLORS[self.relation]

    def _try_raise_relation(self):
        """관계 단계를 한 단계 올리고 태그 갱신"""
        if self.relation < 2:
            self.relation    += 1
            self._talk_count  = 0
            self._refresh_tag()
            return True
        return False

    def _show_message(self, text):
        msg = Text(
            text,
            origin=(0, 0),
            position=(0, 0.15),
            color=color.black,
            background=True,
            scale=1.4
        )
        destroy(msg, delay=2.5)

    # ── E 키 상호작용 ───────────────────────────────────────────────────────

    def interact(self, player):
        # ① 등기 우편물 확인 — 있으면 직접 전달 처리
        express = [
            m for m in player.mails
            if m.target_id == self.building_id
            and m.mail_type == 'express'
            and not m.delivered
        ]
        if express:
            express[0].delivered = True
            raised = self._try_raise_relation()
            stage  = RELATION_STAGES[self.relation]
            notice = f'\n(관계: {stage})' if raised else ''
            self._show_message(
                f'[등기] {self.name}님, 서명 부탁드려요!{notice}'
            )
            return

        # ② 일반 대화 — 3회 나누면 '아는 사이'로 승격
        lines = _DIALOGUES[self.relation]
        line  = lines[self._dial_idx % len(lines)]
        self._dial_idx += 1

        if self.relation == 0:
            self._talk_count += 1
            if self._talk_count >= 3:
                self._try_raise_relation()
                self._show_message(
                    f'{self.name}: "{line}"\n'
                    f'(조금 친해진 것 같아요: {RELATION_STAGES[self.relation]})'
                )
                return

        self._show_message(f'{self.name}: "{line}"')
