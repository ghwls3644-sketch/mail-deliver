from ursina import *


class Player(Entity):
    def __init__(self, mails, interactables=None):
        super().__init__(
            model='cube',
            color=color.orange,
            scale=(0.5, 1.0, 0.5),
            position=(0, 0.5, 0),
            collider='box'
        )
        self.speed = 5
        self.mails = mails
        self.interactables = interactables or []
        self._interact_cooldown = 0

        # 머리
        Entity(
            parent=self,
            model='sphere',
            color=color.yellow,
            scale=0.6,
            y=0.8
        )

        # 상호작용 힌트 — camera.ui HUD로 표시
        self.hint = Text(
            '',
            parent=camera.ui,
            origin=(0, 0),
            position=(0, -0.40),
            color=color.white,
            background=True,
            visible=False
        )

    def update(self):
        self._move()
        self._check_nearby()
        if self._interact_cooldown > 0:
            self._interact_cooldown -= time.dt

    def _move(self):
        import math
        yaw   = math.radians(camera.rotation_y)
        fwd   = Vec3( math.sin(yaw), 0,  math.cos(yaw))
        right = Vec3( math.cos(yaw), 0, -math.sin(yaw))

        move = Vec3(0, 0, 0)
        if held_keys['w']: move += fwd - right   # 좌상단 대각선
        if held_keys['s']: move -= fwd - right   # 우하단 대각선
        if held_keys['a']: move -= fwd + right   # 좌하단
        if held_keys['d']: move += fwd + right   # 우상단

        if move.length() > 0:
            self.position += move.normalized() * self.speed * time.dt

    def _check_nearby(self):
        nearest, dist = self._find_nearest()
        if nearest and dist < 2.5:
            self.hint.text    = f'[E]  {nearest.interact_label}'
            self.hint.visible = True
        else:
            self.hint.visible = False

    def input(self, key):
        if key == 'e' and self._interact_cooldown <= 0:
            nearest, dist = self._find_nearest()
            if nearest and dist < 2.5:
                nearest.interact(self)
                self._interact_cooldown = 2.0

    def _find_nearest(self):
        nearest, min_dist = None, float('inf')
        for e in self.interactables:
            if getattr(e, 'interactable', False):
                d = distance(self, e)
                if d < min_dist:
                    min_dist = d
                    nearest  = e
        return nearest, min_dist
