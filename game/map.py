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
                 color=color.black, background=True, scale=1.5)
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
                 color=color.black, background=True, scale=1.5)
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
        # ── 우체국 (시작 지점, collider 포함) ───────────────────────────────
        Entity(model=GLB + 'building-type-e.glb', position=(0, 0, 0),
               scale=(2, 2, 2), collider='box')
        Text('[우체국]', position=(0, 0, 0), origin=(0, 0),
             scale=80, billboard=True, color=color.black, y=5)

        BKIT = 'assets/kenney_building-kit/Models/GLB format/'

        # ── 중앙 도로 (남북, z=2~18) — 우체국(z=0) 뒤부터 시작 ──────────
        for zi in range(1, 10):
            Entity(model=BKIT + 'floor.glb', position=(0, 0, zi * 2),
                   scale=(2.5, 0.15, 2.5))

        # ── 횡단 도로 1 (동서, z=8) — x=±4 범위 (집 앞까지만) ───────────
        for xi in range(-2, 3):
            Entity(model=BKIT + 'floor.glb', position=(xi * 2, 0, 8),
                   scale=(2.5, 0.15, 2.5))

        # ── 횡단 도로 2 (동서, z=14) — x=±4 범위 ─────────────────────────
        for xi in range(-2, 3):
            Entity(model=BKIT + 'floor.glb', position=(xi * 2, 0, 14),
                   scale=(2.5, 0.15, 2.5))

        # ── 집 A — 김할머니 (letter → 빨간 우체통, 좌z=10) ──────────────
        b_kim = Building('house_kim', '김할머니 집', (-5, 0, 10),
                         model_path=GLB + 'building-type-a.glb')
        self.buildings.append(b_kim)
        mb_red = Mailbox('house_kim', (-3.5, 0.3, 10), color.red)
        self.mailboxes.append(mb_red)

        # ── 집 B — 박씨 가족 (parcel → 건물 직접, 우z=10) ───────────────
        b_park = Building('house_park', '박씨 집', (5, 0, 10),
                          model_path=GLB + 'building-type-b.glb')
        self.buildings.append(b_park)
        mb_blue = Mailbox('house_park_deco', (3.5, 0.3, 10), color.blue)
        mb_blue.interactable = False
        self.mailboxes.append(mb_blue)

        # ── 집 C — 이청년 (express → NPC, 안쪽 중앙 z=16) ──────────────
        b_lee = Building('house_lee', '이청년 집', (0, 0, 16),
                         model_path=GLB + 'building-type-c.glb')
        self.buildings.append(b_lee)
        mb_yellow = Mailbox('house_lee_deco', (0, 0.3, 15.2), color.yellow)
        mb_yellow.interactable = False
        self.mailboxes.append(mb_yellow)
        npc_lee = NPC('npc_lee', '이청년', 'house_lee',
                      (1.5, 0.45, 15.5), color.rgb(100, 160, 220))
        self.npcs.append(npc_lee)

        # ── 이웃집 (collider='box' 로 통과 불가) ─────────────────────────
        deco_houses = [
            (GLB + 'building-type-d.glb', (-5, 0,  4)),
            (GLB + 'building-type-f.glb', ( 5, 0,  4)),
            (GLB + 'building-type-g.glb', (-5, 0, 12)),
            (GLB + 'building-type-h.glb', ( 5, 0, 12)),
            (GLB + 'building-type-i.glb', (-5, 0, 18)),
            (GLB + 'building-type-j.glb', ( 5, 0, 18)),
        ]
        for model, pos in deco_houses:
            Entity(model=model, position=pos, scale=(2, 2, 2), collider='box')


        # ── 화분 (우체국 앞, 교차로) ─────────────────────────────────────
        for pos in [(-1.5, 0, 1.5), (1.5, 0, 1.5),
                    (-1.5, 0, 8),   (1.5, 0, 8),
                    (-1.5, 0, 14),  (1.5, 0, 14)]:
            Entity(model=GLB + 'planter.glb', position=pos, scale=(1.2, 1.2, 1.2))

        # ── 가로수 (도로변 규칙 배치) ─────────────────────────────────────
        for zi in (4, 6, 10, 12, 16, 18):
            Entity(model=GLB + 'tree-small.glb', position=(-2.5, 0, zi), scale=(1.4, 1.4, 1.4))
            Entity(model=GLB + 'tree-small.glb', position=( 2.5, 0, zi), scale=(1.4, 1.4, 1.4))

        # ── 외곽 큰 나무 ──────────────────────────────────────────────────
        for pos in [(-8, 0, 4), (8, 0, 4), (-8, 0, 10), (8, 0, 10),
                    (-8, 0, 16), (8, 0, 16), (0, 0, 20)]:
            Entity(model=GLB + 'tree-large.glb', position=pos, scale=(2, 2, 2))

        # ── 상호작용 가능 오브젝트 통합 리스트 ───────────────────────────
        self.interactables = self.buildings + self.mailboxes + self.npcs
