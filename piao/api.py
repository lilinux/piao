#!/usr/bin/env python
#-*-coding: utf-8 -*-
import json
import os
import pickle
import re
import time
import urllib
from piao.config import DATA_DIR
from piao.init import urllib2, cookie, logger
from piao.objects import Passenager, Ticket
from piao.policy import recognize_passcode, select_specific_ticket, SEAT_TYPE
from piao. errors import (ValidateError, LoginError, SubmitOrderError,
                          SubmitTokenError, CheckOrderError, ConfirmOrderError,
                          QueryOrderError, OrderResultError, TicketSoldOut,
                          NotLogin, NotEnoughTicket)


class Resource(object):
    def __init__(self, url, headers=None, timeout=60, data=None):
        self.url = url
        self.headers = headers
        self.timeout = timeout
        self._req = None
        self.data = data

    def urlencode(self, data):
        return urllib.urlencode(data)

    @property
    def req(self):
        if not self._req:
            if self.data:
                data = self.urlencode(self.data)
                self._req = urllib2.Request(self.url, data)
            else:
                self._req = urllib2.Request(self.url)
            if self.headers:
                for header in self.headers:
                    value = self.headers[header]
                    self.req.add_header(header, value)
        return self._req

    def send(self, timeout=None):
        timeout = timeout if timeout else self.timeout
        logger.debug('SEND: %s, %s', self.req.get_full_url(),
                     self.req.get_data())
        stime = time.time()
        rsp = urllib2.urlopen(self.req, timeout=timeout)
        logger.debug('[%s] waste time [%f]' % (type(self), time.time() - stime))
        return rsp

    def check_data(self, data):
        pass

    def process(self):
        rsp = self.send()
        data = rsp.read()
        #logger.debug('RECV: %s', data)
        return self.check_data(data)


class StationResource(Resource):
    def __init__(self):
        url = "https://kyfw.12306.cn/otn/resources/js/framework/station_name.js"
        Resource.__init__(self, url)

    def process(self):
        dump_file = DATA_DIR + '/stations.dump'
        if os.path.exists(dump_file):
            return pickle.load(open(dump_file))
        rsp = self.send()
        data = rsp.read()
        items = data.split('@')[1:]
        items = [item.split('|') for item in items]
        stations = dict([(item[1], item[2]) for item in items])
        pickle.dump(stations, open(dump_file, 'w'))
        return stations


class AudioResource(Resource):
    def __init__(self):
        url = 'https://kyfw.12306.cn/otn/resources/js/framework/audio/message.wav'

        Resource.__init__(self, url)

    def process(self):
        wav_file = DATA_DIR + '/message.wav'
        if os.path.exists(wav_file):
            return
        rsp = self.send()
        data = rsp.read()
        open(wav_file, 'wb').write(data)


class NoCompleteInitResource(Resource):
    def __init__(self):
        url = 'https://kyfw.12306.cn/otn/queryOrder/initNoComplete'
        data = {'_json_att': ''}
        Resource.__init__(self, url, data=data)

    def check_data(self, data):
        pass


class NoCompleteOrderResource(Resource):
    '查询未完成订单'
    def __init__(self):
        url = 'https://kyfw.12306.cn/otn/queryOrder/queryMyOrderNoComplete'
        data = {'_json_att': ''}
        Resource.__init__(self, url, data=data)

    def check_data(self, data):
        data = json.loads(data)
        if 'url' in data and data['url'] == 'login/init':
            raise NotLogin
        if 'data' not in data or 'orderDBList' not in data['data']:
            return None
        # TODO(lilinux): more infomation return
        orders = data['data']['orderDBList']
        orders = [o['train_code_page'] for o in orders]
        return orders



class PassCodeResource(Resource):
    def __init__(self, module, rand, code_fun=recognize_passcode):
        url = 'https://kyfw.12306.cn/otn/passcodeNew/getPassCodeNew.do?module=%s&rand=%s' % (module, rand)
        self.code_fun = code_fun
        Resource.__init__(self, url)

    def check_data(self, data):
        return self.code_fun(data)

    def process(self):
        rsp = self.send()
        data = rsp.read()
        return self.check_data(data)


class ValidateResource(Resource):
    def __init__(self, rand, code, **kwargs):
        url = 'https://kyfw.12306.cn/otn/passcodeNew/checkRandCodeAnsyn'
        data = {'randCode': code, 'rand': rand}
        if kwargs:
            data.update(kwargs)
        Resource.__init__(self, url, data=data)

    def check_data(self, data):
        data = json.loads(data)
        if data['data'] != 'Y':
            raise ValidateError('validate error!!!')


class InitResource(Resource):
    def __init__(self):
        url = 'https://kyfw.12306.cn/otn/login/init'
        Resource.__init__(self, url)

    def process(self):
        rsp = self.send()
        data = rsp.read()
        return self.check_data(data)


class LoginResource(Resource):
    def __init__(self, username, passwd, passcode):
        url = "https://kyfw.12306.cn/otn/login/loginAysnSuggest"
        data = (
            ('loginUserDTO.user_name', username),
            ('userDTO.password', passwd),
            ('randCode', passcode),
        )
        Resource.__init__(self, url, data=data)

    def check_data(self, data):
        data = json.loads(data)
        if data['data']['loginCheck'] != 'Y':
            raise LoginError('login error!!!')
        cookie.save(ignore_discard=True, ignore_expires=True)


class PassenagerResource(Resource):
    '当前账户的乘客资源'
    def __init__(self):
        url = 'https://kyfw.12306.cn/otn/confirmPassenger/getPassengerDTOs'
        Resource.__init__(self, url, data={'': ''})

    def check_data(self, data):
        data = json.loads(data)
        return map(Passenager, data['data']['normal_passengers'])


class TicketResource(Resource):
    '可用的余票'
    def __init__(self, date, src, dst, purpose_code='ADULT'):
        url = 'https://kyfw.12306.cn/otn/leftTicket/query?'
        data = [
            ('leftTicketDTO.train_date', date),
            ('leftTicketDTO.from_station', src),
            ('leftTicketDTO.to_station', dst),
            ('purpose_codes', purpose_code),
        ]
        url += urllib.urlencode(data)
        Resource.__init__(self, url)

    def check_data(self, data):
        data = json.loads(data)
        tickets = map(Ticket, data['data'])
        #return [ticket for ticket in tickets if ticket.secretStr]
        return tickets


class SubmitOrderResource(Resource):
    '相当于查询页的"预订"按钮'
    def __init__(self, secstr, date, src, dst, purpose_code='ADULT'):
        prepare_url = 'https://kyfw.12306.cn/otn/leftTicket/submitOrderRequest'
        data = [
            ('secretStr', secstr),
            ('train_date', date),
            ('back_train_date', date),  # only support "dc" mode
            ('tour_flag', 'dc'),
            ('purpose_codes', purpose_code),
            ('query_from_station_name', src),
            ('query_to_station_name', dst),
            ('undefined', '')
        ]
        Resource.__init__(self, prepare_url, data=data)

    def urlencode(self, data):
        # XXX: can not use urllib.urlencode in this interface
        if isinstance(data, dict):
            data = data.items()
        return '&'.join(['='.join(item) for item in data])

    def check_data(self, data):
        data = json.loads(data)
        if not data['status']:
            raise SubmitOrderError('submit order error!!!')


class SubmitTokenResource(Resource):
    '获取订单所需要的token和key'
    def __init__(self):
        url = 'https://kyfw.12306.cn/otn/confirmPassenger/initDc'
        data = {'_json_att': ''}
        Resource.__init__(self, url, data=data)

    def check_data(self, data):
        try:
            token = re.findall("var globalRepeatSubmitToken *= *'([0-9a-zA-Z]+)';", data)[0]
            key = re.findall("'key_check_isChange':'([0-9a-zA-Z]+)',", data)[0]
        except Exception:
            raise SubmitTokenError('can not find "token" or "key"')
        return token, key


class CheckOrderResource(Resource):
    '提交前确认订单'
    def __init__(self, passenger, old_str, passcode, token):
        url = 'https://kyfw.12306.cn/otn/confirmPassenger/checkOrderInfo'
        data = [
            ('cancel_flag', '2'),
            ('bed_level_order_num', '000000000000000000000000000000'),
            ('passengerTicketStr', passenger),
            ('oldPassengerStr', old_str),
            ('tour_flag', 'dc'),
            ('randCode', passcode),
            ('_json_att', ''),
            ('REPEAT_SUBMIT_TOKEN', token),
        ]
        Resource.__init__(self, url, data=data)

    def check_data(self, data):
        data = json.loads(data)
        if not data['data']['submitStatus']:
            msg = data['data'].get('errMsg', 'check order error!!!')
            raise CheckOrderError(msg)


class ConfirmOrderResource(Resource):
    '提交订单'
    def __init__(self, newstr, oldstr, passcode, key, token, yp_info, location_code):
        url = 'https://kyfw.12306.cn/otn/confirmPassenger/confirmSingleForQueue'
        data = [
            ('passengerTicketStr', newstr),
            ('oldPassengerStr', oldstr),
            ('randCode', passcode),
            ('purpose_codes', '00'),
            ('key_check_isChange', key),
            ('leftTicketStr', yp_info),
            ('train_location', location_code),
            ('_json_att', ''),
            ('REPEAT_SUBMIT_TOKEN', token),
        ]
        Resource.__init__(self, url, data=data)

    def check_data(self, data):
        data = json.loads(data)
        if not data['status'] or not data['data']['submitStatus']:
            raise ConfirmOrderError('confirm order error!!!')


class QueryOrderResource(Resource):
    '查询订单号'
    def __init__(self, token):
        url = 'https://kyfw.12306.cn/otn/confirmPassenger/queryOrderWaitTime?random=%d&tourFlag=dc&_json_att=&REPEAT_SUBMIT_TOKEN=%s' % (int(time.time() * 1000), token)
        Resource.__init__(self, url)

    def check_data(self, data):
        '可能返回None'
        data = json.loads(data)
        if not data['status'] or not data['data']['queryOrderWaitTimeStatus']:
            raise QueryOrderError('query order error!!!')
        if 'msg' in data['data'] and data['data']['msg'] == '没有足够的票!':
            raise NotEnoughTicket
        return data['data']['orderId']


class OrderResultResource(Resource):
    '查询订票结果'
    def __init__(self, order_id, token):
        url = 'https://kyfw.12306.cn/otn/confirmPassenger/resultOrderForDcQueue'
        data = [
            ('orderSequence_no', order_id),
            ('_json_att', ''),
            ('REPEAT_SUBMIT_TOKEN', token),
        ]
        Resource.__init__(self, url, data=data)

    def check_data(self, data):
        data = json.loads(data)
        if not data['status'] or not data['data']['submitStatus']:
            raise OrderResultError('order result error!!!')


class PayOrderResource(Resource):
    '查询付款信息'
    def __init__(self, token):
        url = 'https://kyfw.12306.cn/otn//payOrder/init?random=%d' % int(time.time() * 1000)
        data = [
            ('_json_att', ''),
            ('REPEAT_SUBMIT_TOKEN', token),
        ]
        Resource.__init__(self, url, data=data)


def validate_passcode(module, rand, **kwargs):
    passcode_res = PassCodeResource(module, rand)
    passcode = passcode_res.process()
    if len(passcode) != 4:
        raise ValidateError
    validate_res = ValidateResource(rand, passcode, **kwargs)
    validate_res.process()
    return passcode


def build_passenger_str(passengers):
    def _build_str1(p):
        phone = p.__dict__.get('mobile_no') or p.__dict__.get('phone_no') or ''
        return ','.join((p.seat_type, p.seat_detail, p.ticket_type, p.passenger_name, p.card_type, p.passenger_id_no, phone)) + ',N'

    def _build_str2(p):
        return ','.join((p.passenger_name, p.card_type, p.passenger_id_no))

    str1 = '_'.join(map(_build_str1, passengers))
    str2 = ',1_'.join(map(_build_str2, passengers)) + ',1_'
    return str1, str2


def login(username, passwd, validate_retry=100):
    # 1. 进入登录页面
    AudioResource().process()
    init_res = InitResource()
    init_res.process()

    # 2. 输入验证码
    for i in xrange(validate_retry):
        try:
            login_passcode = validate_passcode('login', 'sjrand')
            break
        except ValidateError:
            logger.debug('validate error! retry!')
    else:
        raise ValidateError('try times[%d]' % validate_retry)

    # 3. 登录
    login_res = LoginResource(username, passwd, login_passcode)
    login_res.process()


def query_incomplete_order_with_login(username, passwd):
    res = NoCompleteOrderResource()
    try:
        return res.process()
    except NotLogin:
        logger.debug('not loged in, login and try again')
        login(username, passwd)
        return res.process()

def get_ticket(date, src, dst, train, seat, num=1, retry_times=10000):
    # deprecated!
    for i in xrange(retry_times):
        logger.debug('try select ticket: %d', i + 1)
        ticket_res = TicketResource(date, src, dst)
        tickets = ticket_res.process()
        try:
            ticket = select_specific_ticket(tickets, train, seat, num)
            return ticket
        except TicketSoldOut:
            logger.info('sold out!!')
            time.sleep(1)
    else:
        raise TicketSoldOut('try times[%d]' % retry_times)


def submit_order(ticket, date, passengers_newstr, passengers_oldstr):
    newstr = passengers_newstr
    oldstr = passengers_oldstr
    # 1. 预订
    submit_order_res = SubmitOrderResource(ticket.secretStr, date, ticket.from_station_name, ticket.to_station_name)
    submit_order_res.process()

    # 2. 获取token和key
    submit_token_res = SubmitTokenResource()
    token, key = submit_token_res.process()

    # 3. 输入提交订单的验证码
    for i in xrange(10):
        try:
            passcode = validate_passcode('passenger', 'randp', _json_att='', REPEAT_SUBMIT_TOKEN=token)
            break
        except ValidateError:
            logger.debug('validate error')
    else:
        raise ValidateError

    # 4. 检查订单信息
    check_order_res = CheckOrderResource(newstr, oldstr, passcode, token)
    check_order_res.process()

    # 5. 提交订单
    confirm_order_res = ConfirmOrderResource(newstr, oldstr, passcode, key, token, ticket.yp_info, ticket.location_code)
    confirm_order_res.process()

    # 6. 获取订单ID
    for i in range(10):
        query_order_res = QueryOrderResource(token)
        order_id = query_order_res.process()
        if order_id:
            break
        time.sleep(1)
    else:
        raise QueryOrderError

    # 7. 查询订单情况
    order_result_res = OrderResultResource(order_id, token)
    order_result_res.process()

    '''
    # 8. 查询支付信息
    pay_order_res = PayOrderResource(token)
    pay_order_res.process()
    '''


def simple_order(date, src, dst, names, seat, train, seat_detail='0'):
    # 1. 获取站点信息
    station_res = StationResource()
    stations = station_res.process()
    if isinstance(src, unicode):
        src = src.encode('utf8')
    if isinstance(dst, unicode):
        dst = dst.encode('utf8')
    if isinstance(seat, unicode):
        seat = seat.encode('utf8')
    src = stations[src]
    dst = stations[dst]
    seat_type = SEAT_TYPE[seat]

    # 2. 获取乘客信息
    passenager_res = PassenagerResource()
    passengers = passenager_res.process()

    # 3. 初始化乘客数据
    passengers = [passenger for passenger in passengers if passenger.passenger_name in names]

    for passenger in passengers:
        passenger.seat_type = seat_type
        passenger.seat_detail = seat_detail
        passenger.ticket_type = passenger.passenger_type
        passenger.card_type = passenger.passenger_id_type_code
    newstr, oldstr = build_passenger_str(passengers)
    num = len(passengers)

    # 4. 开始刷票
    while True:
        try:
            # 5. 获取余票信息并选择列车
            ticket_res = TicketResource(date, src, dst)
            tickets = ticket_res.process()
            ticket = select_specific_ticket(tickets, train, seat, num)
        except Exception:
            logger.exception('query ticket')
            time.sleep(1)
            continue
        try:
            # 6. 提交订单
            submit_order(ticket, date, newstr, oldstr)
            return
        except Exception:
            logger.exception('submit order error')
            time.sleep(1)
