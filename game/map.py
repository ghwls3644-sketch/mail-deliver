from ursina import *
from game.npc import NPC

GLB = 'assets/kenney_city-kit-suburban_20/Models/GLB format/'


class Building(Entity):
    """배달 가능한 건물"""

    def __init__(self, building_id, label, pos, model_path=None, col=color.white, scale=(2, 2, 2)):
        super().__init__(
            model=model_path or 'cube',
            position=pos,
            color=col if not model_path else color.white,
            scale=scale,
            collider='box',
        )
        self.building_id    = building_id
        self.label          = label
        self.interactable   = True
        self.interact_label = label

        Text(
            label,
            parent=self,
            y=1.2,
            scale=4,
            billboard=True,
            color=color.black
        )

    def interact(self, player):
        matched = [m for m in player.mails
                   if m.target_id == self.building_id and not m.delivered]
        if not matched:
            self._msg('배달할 우편물이 없어요')
            return
        mail = matched[0]
        if mail.mail_type == 'express':
            self._msg(f'등기는 {mail.recipient}에게 직접 전달하세요!')
            return
        mail.delivered = True
        self._msg(f'{mail.type_name} 배달 완료! ✓')
        self.color = color.lime
        invoke(lambda: setattr(self, 'color', color.white), delay=0.6)

    def _msg(self, text):
        m = Text(text, origin=(0, 0), position=(0, 0.15),
                 color=color.white, background=True, scale=1.5)
        destroy(m, delay=2)


class Mailbox(Entity):
    """우체통 — 편지(letter) 전용"""

    def __init__(self, building_id, pos, box_color=color.red):
        super().__init__(
            model='cube',
            position=pos,
            color=box_color,
            scale=(0.35, 0.55, 0.35),
            collider='box'
        )
        self.building_id    = building_id
        self.box_color      = box_color
        self.interactable   = True
        self.interact_label = '우체통에 편지 넣기'

    def interact(self, player):
        matched = [m for m in player.mails
                   if m.target_id == self.building_id
                   and m.mail_type == 'letter'
                   and not m.delivered]
        if not matched:
            self._msg('넣을 편지가 없어요')
            return
        matched[0].delivered = True
        self._msg('편지 투입 완료! ✓')
        self.color = color.lime
        invoke(lambda: setattr(self, 'color', self.box_color), delay=0.6)

    def _msg(self, text):
        m = Text(text, origin=(0, 0), position=(0, 0.15),
                 color=color.white, background=True, scale=1.5)
        destroy(m, delay=2)


class Map:
    """튜토리얼 맵 — 배달 3건 (편지·소포·등기)"""

    def __init__(self):
        self.buildings     = []
        self.mailboxes     = []
        self.npcs          = []
        self.interactables = []
        self._build()

    def _build(self):
        # ── 우체국 (시작 지점, 상호작용 없음) ────────────────────────────
        Entity(
            model=GLB + 'building-type-e.glb',
            position=(0, 0, 0),
            scale=(2, 2, 2),
        )
        Text('[우체국]', position=(0, 0, 0), origin=(0,0),
             scale=80, billboard=True, color=color.black, y=5)

        # ── 집 A — 김할머니 (letter → 빨간 우체통) ───────────────────────
        b_kim = Building('house_kim', '김할머니 집', (-5, 0, 8),
                         model_path=GLB + 'building-type-a.glb')
        self.buildings.append(b_kim)

        mb_red = Mailbox('house_kim', (-5, 0.3, 5.5), color.red)
        self.mailboxes.append(mb_red)

        # ── 집 B — 박씨 가족 (parcel → 건물에 직접) ─────────────────────
        b_park = Building('house_park', '박씨 집', (0, 0, 8),
                          model_path=GLB + 'building-type-b.glb')
        self.buildings.append(b_park)

        mb_blue = Mailbox('house_park_deco', (0, 0.3, 5.5), color.blue)
        mb_blue.interactable = False   # 소포는 건물로 — 우체통은 표식용
        self.mailboxes.append(mb_blue)

        # ── 집 C — 이청년 (express → NPC) ────────────────────────────────
        b_lee = Building('house_lee', '이청년 집', (5, 0, 8),
                         model_path=GLB + 'building-type-c.glb')
        self.buildings.append(b_lee)

        mb_yellow = Mailbox('house_lee_deco', (5, 0.3, 5.5), color.yellow)
        mb_yellow.interactable = False   # 등기는 NPC로 — 우체통은 표식용
        self.mailboxes.append(mb_yellow)

        npc_lee = NPC('npc_lee', '이청년', 'house_lee',
                      (5, 0.45, 5.8), color.rgb(100, 160, 220))
        self.npcs.append(npc_lee)

        # ── 나무 장식 ──────────────────────────────────────────────────
        for pos in [(-8, 0, 4), (8, 0, 4), (-3, 0, 10), (3, 0, 10)]:
            Entity(model=GLB + 'tree-large.glb', position=pos, scale=(1.5, 1.5, 1.5))

        # ── 상호작용 가능 오브젝트 통합 리스트 ──────────────────────────
        self.interactables = self.buildings + self.mailboxes + self.npcs
