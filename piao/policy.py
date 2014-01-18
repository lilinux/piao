#!/usr/bin/env python
#-*-coding: utf-8 -*-
from piao.config import DATA_DIR
from piao.errors import NoSuchTrain, NoSuchSeat, TicketSoldOut

SEAT_MAP = {
    '商务座': 'swz',
    '特等座': 'tz',
    '一等座': 'zy',
    '二等座': 'ze',
    '高级软卧': 'gr',
    '软卧': 'rw',
    '硬卧': 'yw',
    '软座': 'rz',
    '硬座': 'yz',
    '无座': 'wz',
    '其它': 'qt',
}

SEAT_TYPE = {
    '硬座': '1',
    '硬卧': '3',
    '软卧': '4',
    '一等软座': '7',
    '二等软座': '8',
    '商务座': '9',
    '一等座': 'M',
    '二等座': 'O',
    '特等座': 'P',
}


def from_yp_info(yp_info):
    # TODO(lilinux)
    # 1013553001403775000030240500001013550000
    pass


def select_specific_ticket(tickets, train, seat, num=1):
    try:
        seat_str = SEAT_MAP[seat]
    except KeyError:
        raise NoSuchSeat('seat[%s]' % seat)
    seat_str += '_num'
    try:
        ticket = next((ticket for ticket in tickets if ticket.station_train_code == train))
    except StopIteration:
        raise NoSuchTrain('train[%s]' % train)
    if not ticket.secretStr or ticket.canWebBuy != 'Y':
        raise TicketSoldOut()
    left = getattr(ticket, seat_str)
    if not left == '有' and not left.isdigit():
        raise TicketSoldOut()
    if left.isdigit():
        left_num = int(left)
        if left_num < num:
            raise TicketSoldOut('not enough')
    return ticket


def recognize_passcode(data):
    open(DATA_DIR + '/passcode.png', 'wb').write(data)
    # TODO(lilinux): popup image and wait for passcode ?
    # XXX: only support macos with poor experience
    import os
    os.system('afplay %s/message.wav&' % DATA_DIR)
    os.system('open %s/passcode.png' % DATA_DIR)
    try:
        return raw_input('please validate: ')
    except EOFError:
        return ''
