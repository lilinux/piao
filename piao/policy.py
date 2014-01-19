#!/usr/bin/env python
#-*-coding: utf-8 -*-
import os
import sys
import threading
from piao.config import DATA_DIR
from piao.init import logger
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
        logger.info('letf tickets: [%d]', left_num)
        if left_num < num:
            raise TicketSoldOut('not enough')
    return ticket


def play_wav(wav):
    import pyaudio
    import wave
    wave_file = wave.open(wav, 'rb')
    audio = pyaudio.PyAudio()
    stream = audio.open(format=audio.get_format_from_width(
                        wave_file.getsampwidth()),
                        channels=wave_file.getnchannels(),
                        rate=wave_file.getframerate(),
                        output=True)
    stream.write(wave_file.readframes(wave_file.getnframes()))
    stream.stop_stream()
    stream.close()
    audio.terminate()


def notify_passcode():
    wav = '%s/message.wav' % DATA_DIR
    try:
        threading.Thread(target=play_wav, args=(wav,)).start()
        return
    except ImportError:
        pass
    if sys.platform == 'darwin':
        os.system('afplay %s&' % wav)
    elif sys.platform == 'linux':
        os.system('mplayer %s&' % wav)
    else:
        os.system('rundll32 amovie.ocx,RunDll /play /close %s' % wav)


passcode_tool = None
def recognize_passcode(data):
    png = DATA_DIR + '/passcode.png'
    open(png, 'wb').write(data)
    notify_passcode()
    if passcode_tool:
        return os.popen('%s %s' % (passcode_tool, png)).read().strip()
    else:
        try:
            return raw_input('please validate: ')
        except EOFError:
            return ''
