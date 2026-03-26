from ursina import *
from game.npc import NPC

class Building(Entity):
    """배달 가능한 건물 기본 클래스"""

    def __init__(self, building_id, label, pos, col=color.white, scale=(1.5, 2, 1.5), tex=None):
        super().__init__(
            model='cube',
            position=pos,
            color=col,
            scale=scale,
            collider='box',
            texture=tex,
            texture_scale=(2, 2),
        )
        self.building_id     = building_id
        self.label           = label
        self.interactable    = True
        self.interact_label  = label

        # 건물 이름표 (항상 카메라를 향함)
        self.name_tag = Text(
            label,
            parent=self,
            y=1.2,
            scale=4,
            billboard=True,
            color=color.black
        )

    def interact(self, player):
        """E키 상호작용 — 해당 건물로 배달 가능한 우편물 처리"""
        matched = [m for m in player.mails
                   if m.target_id == self.building_id and not m.delivered]

        if not matched:
            self._show_message('배달할 우편물이 없어요')
            return

        mail = matched[0]

        # 등기는 NPC에게 직접 전달 — 건물에서는 처리 불가
        if mail.mail_type == 'express':
            self._show_message(f'등기는 {mail.recipient}에게 직접 전달하세요!')
            return

        mail.delivered = True
        self._show_message(f'{mail.type_name} 배달 완료!')

        # 배달 완료 이펙트
        self.color = color.lime
        invoke(lambda: setattr(self, 'color', color.white), delay=0.5)

    def _show_message(self, text):
        msg = Text(
            text,
            origin=(0, 0),
            position=(0, 0.15),
            color=color.white,
            background=True,
            scale=1.5
        )
        destroy(msg, delay=2)


class Mailbox(Entity):
    """우체통 — 편지(letter) 전용"""

    def __init__(self, building_id, pos, box_color=color.red):
        super().__init__(
            model='cube',
            position=pos,
            color=box_color,
            scale=(0.3, 0.5, 0.3),
            collider='box'
        )
        self.building_id    = building_id
        self.interactable   = True
        self.interact_label = '우체통에 편지 넣기'

    def interact(self, player):
        matched = [m for m in player.mails
                   if m.target_id == self.building_id
                   and m.mail_type == 'letter'
                   and not m.delivered]

        if not matched:
            self._show_message('넣을 편지가 없어요')
            return

        matched[0].delivered = True
        self._show_message('편지 투입 완료!')
        self.color = color.lime
        invoke(lambda: setattr(self, 'color', color.red), delay=0.5)

    def _show_message(self, text):
        msg = Text(text, origin=(0,0), position=(0, 0.15),
                   color=color.white, background=True, scale=1.5)
        destroy(msg, delay=2)


class Map:
    """구역 A — 마을 광장 초기 배치"""

    def __init__(self):
        self.buildings = []
        self.npcs      = []   # UI 친밀도 패널에서 참조
        self._build_zone_a()

    def _build_zone_a(self):
        BRICK = 'brick'
        HOUSE = 'assets/textures/dirt_block.jpeg'

        layout = [
            # (building_id,       label,           위치,        색상,                   크기,           텍스처)
            ('post_office',    '[우체국]',      (0,  0,  0), color.rgb(255,230,100), (2,   2.5, 2),   BRICK),
            ('bakery',         '[빵집]',        (4,  0,  0), color.rgb(255,200,130), (1.8, 2,   1.8), BRICK),
            ('flower_shop',    '[꽃집]',        (-4, 0,  0), color.rgb(255,190,200), (1.5, 2,   1.5), BRICK),
            ('house_flower_side', '꽃집 옆 집', (-4, 0,  3), color.rgb(230,230,220), (1.5, 2,   1.5), HOUSE),
            ('house_bakery_opp',  '빵집 맞은편',(4,  0,  3), color.rgb(220,210,180), (1.5, 2,   1.5), HOUSE),
            ('house_post_opp',   '우체국 맞은편',(0,  0,  3), color.rgb(210,225,200), (1.5, 2,  1.5), HOUSE),
        ]

        for bid, label, pos, col, sc, tex in layout:
            b = Building(bid, label, pos, col, sc, tex)
            self.buildings.append(b)

        # 우체통 — 집 건물 앞(z -1.5)에 배치해 건물과 좌표 겹침 방지
        mailboxes = [
            ('house_blue',        (-8, 0, 1.5), color.cyan),    # 파란 우체통 집 우체통
            ('house_flower_side', (-4, 0, 1.5), color.magenta), # 꽃집 옆 집 우체통
            ('house_bakery_opp',  (4,  0, 1.5), color.orange),  # 빵집 맞은편 집 우체통
            ('house_park_side',   (8,  0, 1.5), color.green),   # 공원 옆 집 우체통
        ]
        for bid, pos, col in mailboxes:
            self.buildings.append(Mailbox(bid, pos, col))

        # 골목 파란 우체통 집 — 건물은 z=3, 우체통은 z=1.5 (중복 좌표 해소)
        b = Building('house_blue', '파란 우체통 집', (-8, 0, 3),
                     color.rgb(200, 220, 255), (1.5, 2, 1.5), HOUSE)
        self.buildings.append(b)

        # 공원 옆 집 (day 2 배달 대상)
        b = Building('house_park_side', '공원 옆 집', (8, 0, 3),
                     color.rgb(200, 235, 200), (1.5, 2, 1.5), HOUSE)
        self.buildings.append(b)

        # 노란 지붕 집 (day 2 배달 대상)
        b = Building('house_yellow_roof', '노란 지붕 집', (0, 0, 6),
                     color.rgb(255, 240, 160), (1.5, 2, 1.5), HOUSE)
        self.buildings.append(b)

        # ── 주민 NPC 배치 ────────────────────────────────────────────────
        # 각 집 앞(건물 z-0.8)에 서 있는 주민
        # (npc_id, 이름, building_id, 위치, 색상)
        npc_layout = [
            ('npc_kim',  '김할머니',  'house_blue',         (-8, 0.45, 2.2), color.rgb(180, 140, 220)),
            ('npc_park', '박씨 가족', 'house_flower_side',  (-4, 0.45, 2.2), color.rgb(100, 180, 100)),
            ('npc_lee',  '이청년',   'house_bakery_opp',   ( 4, 0.45, 2.2), color.rgb(100, 160, 220)),
            ('npc_yun',  '윤씨 부부', 'house_post_opp',     ( 0, 0.45, 2.2), color.rgb(220, 160, 100)),
            ('npc_choi', '최씨',     'house_park_side',    ( 8, 0.45, 2.2), color.rgb(200, 100, 100)),
            ('npc_jung', '정할아버지','house_yellow_roof',  ( 0, 0.45, 5.0), color.rgb(160, 200, 160)),
        ]
        for nid, name, bid, pos, col in npc_layout:
            n = NPC(nid, name, bid, pos, col)
            self.npcs.append(n)
