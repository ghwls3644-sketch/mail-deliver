from ursina import *

class Player(Entity):
    def __init__(self, mails):
        super().__init__(
            model='cube',
            color=color.orange,
            scale=(0.5, 1.0, 0.5),
            position=(0, 0.5, 0),
            collider='box'
        )
        self.speed = 5
        self.mails = mails

        # 머리 (시각적 구분용)
        self.head = Entity(
            parent=self,
            model='sphere',
            color=color.yellow,
            scale=0.6,
            y=0.8
        )

        # 상호작용 안내 텍스트
        self.hint = Text(
            '',
            origin=(0, 0),
            position=(0, -0.35),
            color=color.white,
            background=True,
            visible=False
        )

    def update(self):
        self._move()
        self._check_nearby()

    def _move(self):
        # 쿼터뷰 기준 이동 방향 보정 (카메라 -45도 회전 기준)
        move = Vec3(0, 0, 0)
        if held_keys['w']: move += Vec3( 1, 0,  1)
        if held_keys['s']: move += Vec3(-1, 0, -1)
        if held_keys['a']: move += Vec3(-1, 0,  1)
        if held_keys['d']: move += Vec3( 1, 0, -1)

        if move.length() > 0:
            move = move.normalized() * self.speed * time.dt
            self.position += move

    def _check_nearby(self):
        nearest, dist = self._find_nearest_interactable()
        if nearest and dist < 2.0:
            self.hint.text    = f'[E] {nearest.interact_label}'
            self.hint.visible = True
        else:
            self.hint.visible = False

    def input(self, key):
        if key == 'e':
            nearest, dist = self._find_nearest_interactable()
            if nearest and dist < 2.0:
                nearest.interact(self)

    def _find_nearest_interactable(self):
        nearest, min_dist = None, float('inf')
        for e in scene.entities:
            if getattr(e, 'interactable', False):
                d = distance(self, e)
                if d < min_dist:
                    min_dist = d
                    nearest  = e
        return nearest, min_dist
