from ursina import *
from game.npc import NPC
import json, os

# ── 에셋 경로 ──────────────────────────────────────────────────────────
SUBURBAN    = 'assets/kenney_city-kit-suburban_20/Models/GLB format/'
ROADS       = 'assets/kenney_city-kit-roads/Models/GLB format/'
COMMERCIAL  = 'assets/kenney_city-kit-commercial_2.1/Models/GLB format/'
NATURE      = 'assets/kenney_nature-kit/Models/GLTF format/'
CARS        = 'assets/kenney_car-kit/Models/GLB format/'

# ── 스케일 상수 (모델 크기에 따라 조정) ────────────────────────────────
ROAD_S   = (2, 2, 2)           # 도로 타일
BLDG_S   = (2, 2, 2)           # 건물
TREE_S   = (1.5, 1.5, 1.5)     # 나무 (보통)
TREE_L   = (2, 2, 2)           # 나무 (큰)
FLOWER_S = (1, 1, 1)           # 꽃·식물
CAR_S    = (1.5, 1.5, 1.5)     # 차량
LIGHT_S  = (1.5, 1.5, 1.5)     # 가로등
FENCE_S  = (1.5, 1.5, 1.5)     # 울타리
DETAIL_S = (1.5, 1.5, 1.5)     # 파라솔·어닝
POND_S   = (2, 2, 2)           # 연못 타일


# ── 배치 헬퍼 ──────────────────────────────────────────────────────────

def _road(model, x, z, rot_y=0):
    """도로 타일 배치"""
    Entity(model=ROADS + model, position=(x, 0, z),
           rotation_y=rot_y, scale=ROAD_S)


def _deco(path, pos, s=BLDG_S, rot_y=0, **kw):
    """장식 오브젝트 배치"""
    Entity(model=path, position=pos, scale=s, rotation_y=rot_y, **kw)


# ── Building ───────────────────────────────────────────────────────────

class Building(Entity):
    """배달 가능한 건물"""

    def __init__(self, building_id, label, pos,
                 model_path=None, col=color.white,
                 scale=BLDG_S, rot_y=0):
        super().__init__(
            model=model_path or 'cube',
            position=pos,
            color=col if not model_path else color.white,
            scale=scale,
            rotation_y=rot_y,
            collider='box',
        )
        self.building_id    = building_id
        self.label          = label
        self.interactable   = True
        self.interact_label = label

        Text(label, parent=self, y=1.2, scale=4,
             billboard=True, color=color.black)

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


# ── Mailbox ────────────────────────────────────────────────────────────

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


# ── Map ────────────────────────────────────────────────────────────────

MAPS_DIR = 'game/maps/'

class Map:
    """튜토리얼 맵 — 구역 A (마을 광장) + 구역 B (주택가 골목)
    좌표 기준: 맵_배치_계획서.md 참고
    """

    def __init__(self, map_name='tutorial'):
        self._map_name     = map_name   # 에디터 저장 파일명 (확장자 제외)
        self.buildings     = []
        self.mailboxes     = []
        self.npcs          = []
        self.interactables = []
        self._build()

    # ── 헬퍼 ──────────────────────────────────────────────

    def _add_bldg(self, bid, label, pos, model, rot_y=0):
        b = Building(bid, label, pos, model_path=model, rot_y=rot_y)
        self.buildings.append(b)

    def _add_mb(self, bid, pos, col=color.red, active=True):
        mb = Mailbox(bid, pos, col)
        if not active:
            mb.interactable = False
        self.mailboxes.append(mb)

    def _add_npc(self, npc_id, name, bid, pos, col=color.cyan):
        npc = NPC(npc_id, name, bid, pos, col)
        self.npcs.append(npc)

    # ── 빌드 ─────────────────────────────────────────────

    def _build(self):
        self._build_roads()
        self._build_zone_a()
        self._build_zone_b()
        self._build_park()
        self._build_trees()
        self._build_decorations()
        self._load_editor_objects()          # 에디터 배치 추가 로드
        self.interactables = self.buildings + self.mailboxes + self.npcs

    def _load_editor_objects(self):
        """에디터(editor.py)로 저장한 game/maps/{map_name}.json 을 읽어 장식 오브젝트 생성.
        파일이 없으면 조용히 건너뜀 — 게임 로직(배달·NPC)에 영향 없음."""
        path = MAPS_DIR + self._map_name + '.json'
        if not os.path.exists(path):
            return
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        for obj in data.get('objects', []):
            Entity(model=obj['model'], position=obj['pos'],
                   scale=obj['scale'], rotation_y=obj['rot_y'])

    # ── 1. 도로 ──────────────────────────────────────────

    def _build_roads(self):
        # 중앙 남북 간선도로
        _road('road-end.glb',       0, -1)
        for z in (1, 3, 5, 7):
            _road('road-straight.glb', 0, z)
        _road('road-roundabout.glb', 0,  9)           # 로터리
        _road('road-straight.glb',   0, 11)
        _road('road-crossroad.glb',  0, 13)            # 교차로 1
        _road('road-straight.glb',   0, 15)
        _road('road-crossroad.glb',  0, 17)            # 교차로 2
        _road('road-straight.glb',   0, 19)
        _road('road-crossroad.glb',  0, 21)            # 교차로 3
        for z in (23, 25):
            _road('road-straight.glb', 0, z)
        _road('road-end.glb',       0, 27, rot_y=180)  # 북쪽 끝

        # 동서 횡단 도로 3개
        self._ew_road(13)
        self._ew_road(17)
        self._ew_road(21, x_west=-9, x_east=9)

        # 로터리 동서 분기
        _road('road-straight.glb', -5, 9, rot_y=90)
        _road('road-end.glb',     -8, 9, rot_y=270)
        _road('road-straight.glb',  5, 9, rot_y=90)
        _road('road-end.glb',      8, 9, rot_y=90)

    def _ew_road(self, z, x_west=-7, x_east=7):
        """동서 횡단 도로 배치"""
        _road('road-end.glb', x_west, z, rot_y=270)
        for x in range(x_west + 2, 0, 2):
            _road('road-straight.glb', x, z, rot_y=90)
        for x in range(3, x_east, 2):
            _road('road-straight.glb', x, z, rot_y=90)
        _road('road-end.glb', x_east, z, rot_y=90)

    # ── 2. 구역 A — 마을 광장 ────────────────────────────

    def _build_zone_a(self):
        # ── 우체국 (배달 대상 아님) ──
        _deco(SUBURBAN + 'building-type-e.glb', (0, 0, 0), collider='box')
        Text('[우체국]', position=(0, 5, 0), origin=(0, 0),
             scale=80, billboard=True, color=color.black)

        # ── 상업 건물 ──
        self._add_bldg('B_FLOWER', '꽃집',   (-8, 0, 8),
                        COMMERCIAL + 'building-b.glb', 90)
        self._add_bldg('B_BAKERY', '빵집',   (8, 0, 8),
                        COMMERCIAL + 'building-a.glb', 270)
        self._add_bldg('B_CAFE',   '카페',   (-9, 0, 5),
                        COMMERCIAL + 'building-c.glb', 90)
        self._add_bldg('B_SHOP',   '잡화점', (9, 0, 4),
                        COMMERCIAL + 'building-d.glb', 270)

        # ── 주거 건물 ──
        self._add_bldg('B_KIM',  '김할머니 집', (-5, 0, 10),
                        SUBURBAN + 'building-type-a.glb', 90)
        self._add_bldg('B_PARK', '박씨 집',    (5, 0, 10),
                        SUBURBAN + 'building-type-b.glb', 270)

        # ── 이웃집 ──
        self._add_bldg('B_NBRA', '이웃집 A', (-11, 0, 4),
                        SUBURBAN + 'building-type-f.glb', 90)
        self._add_bldg('B_NBRB', '이웃집 B', (11, 0, 4),
                        SUBURBAN + 'building-type-g.glb', 270)
        self._add_bldg('B_NBRC', '이웃집 C', (-11, 0, 12),
                        SUBURBAN + 'building-type-h.glb', 90)
        self._add_bldg('B_NBRD', '이웃집 D', (11, 0, 12),
                        SUBURBAN + 'building-type-i.glb', 270)

        # ── 우체통 ──
        self._add_mb('B_KIM',  (-3.5, 0.3, 10), color.red)
        self._add_mb('B_PARK', (3.5, 0.3, 10),  color.blue, active=False)
        self._add_mb('B_NBRA', (-9.5, 0.3, 4))
        self._add_mb('B_NBRB', (9.5, 0.3, 4))
        self._add_mb('B_NBRC', (-9.5, 0.3, 12))
        self._add_mb('B_NBRD', (9.5, 0.3, 12))

        # ── 진입로 ──
        for zi in (9, 10):
            _deco(SUBURBAN + 'path-short.glb', (-4.5, 0, zi))   # 김할머니
            _deco(SUBURBAN + 'path-short.glb', (4.5, 0, zi))    # 박씨
        _deco(SUBURBAN + 'path-short.glb', (0, 0, 15))          # 이청년

    # ── 3. 구역 B — 주택가 골목 ──────────────────────────

    def _build_zone_b(self):
        # ── 이청년 집 + NPC ──
        self._add_bldg('B_LEE', '이청년 집', (0, 0, 16),
                        SUBURBAN + 'building-type-c.glb', 180)
        self._add_mb('B_LEE_DECO', (0, 0.3, 15.2),
                     color.yellow, active=False)
        self._add_npc('npc_lee', '이청년', 'B_LEE',
                      (1.5, 0.45, 15.5), color.rgb(100, 160, 220))

        # ── 주택 B-01 ~ B-10 ──
        houses = [
            ('B_01', '주택 B-01', -8,  16, 'building-type-e.glb', 90),
            ('B_02', '주택 B-02',  8,  16, 'building-type-j.glb', 270),
            ('B_03', '주택 B-03', -8,  20, 'building-type-k.glb', 90),
            ('B_04', '주택 B-04',  8,  20, 'building-type-l.glb', 270),
            ('B_05', '주택 B-05', -11, 23, 'building-type-m.glb', 90),
            ('B_06', '주택 B-06',  11, 23, 'building-type-n.glb', 270),
            ('B_07', '주택 B-07', -8,  26, 'building-type-o.glb', 90),
            ('B_08', '주택 B-08',  8,  26, 'building-type-p.glb', 270),
            ('B_09', '주택 B-09', -5,  29, 'building-type-q.glb', 180),
            ('B_10', '주택 B-10',  5,  29, 'building-type-r.glb', 180),
        ]
        for bid, label, x, z, model, rot in houses:
            self._add_bldg(bid, label, (x, 0, z), SUBURBAN + model, rot)

        # ── 우체통 ──
        for bid, x, z in [
            ('B_01', -6.5, 16), ('B_02', 6.5, 16),
            ('B_03', -6.5, 20), ('B_04', 6.5, 20),
            ('B_05', -9.5, 22), ('B_06', 9.5, 22),
            ('B_07', -6.5, 26), ('B_08', 6.5, 26),
            ('B_09', -3.5, 28), ('B_10', 3.5, 28),
        ]:
            self._add_mb(bid, (x, 0.3, z))

    # ── 4. 소공원 (z=22~26, x=-3~+3) ────────────────────

    def _build_park(self):
        # 연못 타일
        _deco(NATURE + 'ground_riverStraight.glb', (0, 0, 23),  POND_S)
        _deco(NATURE + 'ground_riverBend.glb',     (-1, 0, 23), POND_S)
        _deco(NATURE + 'ground_riverBend.glb',     (1, 0, 23),  POND_S, rot_y=90)
        _deco(NATURE + 'ground_riverEnd.glb',      (0, 0, 24),  POND_S)

        # 수련
        _deco(NATURE + 'lily_large.glb', (0, 0.05, 23.5),    FLOWER_S)
        _deco(NATURE + 'lily_small.glb', (-0.5, 0.05, 23),   FLOWER_S)

        # 덤불
        _deco(NATURE + 'plant_bush.glb',      (-2, 0, 22.5),  FLOWER_S)
        _deco(NATURE + 'plant_bush.glb',      (2, 0, 22.5),   FLOWER_S)
        _deco(NATURE + 'plant_bushLarge.glb',  (-2, 0, 25),   FLOWER_S)
        _deco(NATURE + 'plant_bushLarge.glb',  (2, 0, 25),    FLOWER_S)

        # 바위 & 그루터기
        _deco(NATURE + 'rock_smallA.glb', (-1.5, 0, 24.5), FLOWER_S)
        _deco(NATURE + 'rock_smallB.glb', (1.5, 0, 24.5),  FLOWER_S)
        _deco(NATURE + 'rock_largeA.glb', (-2.5, 0, 23.5), FLOWER_S)
        _deco(NATURE + 'stump_round.glb', (2.5, 0, 25.5),  FLOWER_S)
        _deco(NATURE + 'log.glb',         (-2, 0, 26),      FLOWER_S)

    # ── 5. 나무 ──────────────────────────────────────────

    def _build_trees(self):
        # 가로수 (도로변, 좌우 대칭)
        for model, s, zs in [
            (SUBURBAN + 'tree-large.glb', BLDG_S,       (3, 11)),
            (NATURE   + 'tree_oak.glb',   TREE_S,       (5, 19)),
            (NATURE   + 'tree_fat.glb',   TREE_S,       (15,)),
            (NATURE   + 'tree_tall.glb',  TREE_S,       (23,)),
            (SUBURBAN + 'tree-small.glb', (1.4,1.4,1.4),(27,)),
        ]:
            for z in zs:
                _deco(model, (-2.5, 0, z), s)
                _deco(model, (2.5, 0, z), s)

        # 외곽 나무 (맵 경계, 좌우 대칭)
        for model, zs in [
            (NATURE + 'tree_cone.glb',    (3, 7)),
            (NATURE + 'tree_tall.glb',    (11, 15)),
            (NATURE + 'tree_oak.glb',     (19,)),
            (NATURE + 'tree_fat.glb',     (23,)),
        ]:
            for z in zs:
                _deco(model, (-13, 0, z), TREE_L)
                _deco(model, (13, 0, z),  TREE_L)

        # 북쪽 경계 나무
        for x in (-6, 0, 6):
            _deco(NATURE + 'tree_default.glb', (x, 0, 31), TREE_L)

    # ── 6. 장식 (화분·가로등·꽃·차량·울타리) ─────────────

    def _build_decorations(self):
        # ── 화분 ──
        for pos in [(-1.5, 0, 1.5), (1.5, 0, 1.5),
                    (-1.5, 0, 8),   (1.5, 0, 8),
                    (-1.5, 0, 14),  (1.5, 0, 14)]:
            _deco(SUBURBAN + 'planter.glb', pos, (1.2, 1.2, 1.2))

        # ── 가로등 (도로변 좌우) ──
        for z in (3, 11, 15, 19, 23, 27):
            _deco(ROADS + 'light-square.glb', (-2, 0, z), LIGHT_S)
            _deco(ROADS + 'light-square.glb', (2, 0, z),  LIGHT_S)

        # ── 카페 파라솔 & 어닝 ──
        _deco(COMMERCIAL + 'detail-parasol-a.glb', (-10, 0, 5.5), DETAIL_S)
        _deco(COMMERCIAL + 'detail-parasol-b.glb', (-9, 0, 5.5),  DETAIL_S)
        _deco(COMMERCIAL + 'detail-awning.glb',    (-9, 0, 4.5),  DETAIL_S)
        _deco(COMMERCIAL + 'detail-awning-wide.glb', (8, 0, 7),   DETAIL_S)
        _deco(COMMERCIAL + 'detail-awning.glb',    (-8, 0, 7),    DETAIL_S)

        # ── 차량 ──
        _deco(CARS + 'delivery.glb', (-9, 0, 7),  CAR_S, rot_y=90)
        _deco(CARS + 'sedan.glb',    (9, 0, 7),   CAR_S, rot_y=270)
        _deco(CARS + 'taxi.glb',     (7, 0, 20),  CAR_S, rot_y=270)
        _deco(CARS + 'suv.glb',      (-7, 0, 25), CAR_S, rot_y=90)

        # ── 꽃 (꽃집 마당) ──
        _deco(NATURE + 'flower_redA.glb',    (-9, 0, 9),      FLOWER_S)
        _deco(NATURE + 'flower_redB.glb',    (-9.5, 0, 9.5),  FLOWER_S)
        _deco(NATURE + 'flower_purpleA.glb', (-8.5, 0, 9),    FLOWER_S)
        _deco(NATURE + 'flower_yellowA.glb', (-7.5, 0, 9),    FLOWER_S)

        # ── 꽃 (김할머니 마당) ──
        _deco(NATURE + 'flower_redC.glb',    (-6, 0, 11),     FLOWER_S)
        _deco(NATURE + 'flower_purpleB.glb', (-5.5, 0, 11),   FLOWER_S)
        _deco(NATURE + 'flower_yellowB.glb', (-4.5, 0, 11),   FLOWER_S)

        # ── 꽃 (박씨 마당) ──
        _deco(NATURE + 'flower_redA.glb',    (4.5, 0, 11),    FLOWER_S)
        _deco(NATURE + 'flower_purpleC.glb', (5, 0, 11.5),    FLOWER_S)
        _deco(NATURE + 'flower_yellowC.glb', (6, 0, 11),      FLOWER_S)

        # ── 주택가 마당 식물 ──
        _deco(NATURE + 'plant_bushSmall.glb',    (-7, 0, 17),  FLOWER_S)
        _deco(NATURE + 'plant_bushSmall.glb',    (7, 0, 17),   FLOWER_S)
        _deco(NATURE + 'plant_bushDetailed.glb', (-10, 0, 25), FLOWER_S)
        _deco(NATURE + 'plant_bushDetailed.glb', (10, 0, 25),  FLOWER_S)

        # ── 울타리 (구역 A — 꽃집/빵집 마당) ──
        for x in range(-10, -5, 2):
            _deco(SUBURBAN + 'fence-1x2.glb', (x, 0, 10), FENCE_S)
        for x in range(6, 11, 2):
            _deco(SUBURBAN + 'fence-1x2.glb', (x, 0, 10), FENCE_S)

        # ── 울타리 (구역 B — 주택가 마당) ──
        for x in range(-10, -5, 2):
            _deco(NATURE + 'fence_planks.glb', (x, 0, 14), FENCE_S)
        for x in range(6, 11, 2):
            _deco(NATURE + 'fence_planks.glb', (x, 0, 14), FENCE_S)
