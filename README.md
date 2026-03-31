# 우편배달부

> 작은 마을의 우편배달부가 되어 편지를 나르고, 주민들과 조금씩 가까워지는 잔잔한 3D 쿼터뷰 배달 게임

---

## 실행 방법

**의존성 설치**
```bash
pip install -r requirements.txt
```

**게임 실행**
```bash
python main.py
```

---

## 조작법

| 키 | 동작 |
|----|------|
| `W A S D` | 이동 |
| `E` | 상호작용 (우체통 / 건물 / NPC) |

---

## 기술 스택

| 항목 | 버전 |
|------|------|
| Python | 3.13 |
| Ursina | 8.3.0+ |

---

## 폴더 구조

```
mail deliver/
├── main.py          # 진입점 — 게임 루프, 카메라
├── requirements.txt
├── game/
│   ├── mail.py      # 우편물 데이터
│   ├── map.py       # 맵 레이아웃
│   ├── npc.py       # 주민 NPC
│   ├── player.py    # 플레이어 이동
│   └── ui.py        # HUD
└── assets/          # 3D 모델, 텍스처
```

---

## 에셋 출처

- [Kenney City Kit (Suburban)](https://kenney.nl) — CC0
- [Kenney City Kit (Roads)](https://kenney.nl) — CC0
- [Kenney Mini Characters](https://kenney.nl) — CC0
