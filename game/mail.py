from dataclasses import dataclass
from ursina import color

MAIL_TYPES = {
    'letter':  ('편지', color.yellow,           '우체통에 투입'),
    'parcel':  ('소포', color.rgb(139, 90, 43), '현관 앞에 놓기'),
    'express': ('등기', color.azure,            '직접 전달'),
}

@dataclass
class Mail:
    mail_type:    str
    recipient:    str
    address_hint: str
    target_id:    str
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
        return f"{check} [{self.type_name}] {self.recipient} — {self.address_hint}"


def get_tutorial_mails():
    return [
        Mail('letter',  '김할머니',  '빨간 우체통',  'house_kim'),
        Mail('parcel',  '박씨 가족', '파란 우체통 집', 'house_park'),
        Mail('express', '이청년',    '노란 우체통 집', 'house_lee'),
    ]
