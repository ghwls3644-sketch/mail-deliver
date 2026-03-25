from dataclasses import dataclass, field
from ursina import color

# 우편물 종류 — (표시명, 색상, 전달 방식)
MAIL_TYPES = {
    'letter':  ('편지', color.yellow,      '우체통에 투입'),
    'parcel':  ('소포', color.rgb(139,90,43), '현관 앞에 놓기'),
    'express': ('등기', color.azure,       '직접 전달'),
}

@dataclass
class Mail:
    mail_type:    str        # 'letter' / 'parcel' / 'express'
    recipient:    str        # 수신인 이름
    address_hint: str        # 시각적 단서 — 항상 제공
    target_id:    str        # 배달 대상 건물 ID (map.py와 연결)
    delivered:    bool = False

    @property
    def type_name(self):
        return MAIL_TYPES[self.mail_type][0]

    @property
    def mail_color(self):
        return MAIL_TYPES[self.mail_type][1]

    @property
    def delivery_method(self):
        return MAIL_TYPES[self.mail_type][2]

    @property
    def label(self):
        check = '✓' if self.delivered else '□'
        return f"{check} [{self.type_name}] {self.recipient} / {self.address_hint}"


# 날짜별 우편물 목록
# day 파라미터로 나중에 날짜별 다른 우편물 추가 가능
def get_daily_mails(day=1):
    if day == 1:
        return [
            Mail('letter',  '김할머니', '골목 파란 우체통 집',  'house_blue'),
            Mail('parcel',  '박씨 가족', '꽃집 옆 집',          'house_flower_side'),
            Mail('express', '이청년',   '광장 빵집 맞은편 집',  'house_bakery_opp'),
        ]
    if day == 2:
        return [
            Mail('letter',  '최씨',    '공원 옆 집',            'house_park_side'),
            Mail('parcel',  '정할아버지', '노란 지붕 집',        'house_yellow_roof'),
            Mail('express', '윤씨 부부', '우체국 맞은편 집',    'house_post_opp'),
        ]
    # 기본: day 1과 동일 구성으로 반복
    return get_daily_mails(day=1)
