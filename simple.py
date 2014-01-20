#!/usr/bin/env python
#-*-coding: utf-8 -*-

from piao.api import *
import piao.init
import piao.policy
#piao.policy.passcode_tool = None  # if no Tkinter or PIL library
piao.policy.passcode_tool = 'tools/passwin_ui.py'

def main():
    username = 'user'
    password = 'pass'
    date = '2014-02-02'
    src = u'吉安'
    dst = u'南昌'
    passengers = [u'张三', u'李四']
    seat = u'硬座'
    train = 'K88'
    detail = '0'

    piao.init.add_proxy(None)  # add proxy like "proxy.xxoo.com:8080"
    orders = query_incomplete_order_with_login(username, password)
    if orders:
        print '有未完成订单，车次为[%s]' % ','.join(orders)
        print '请先在页面上支付订单或取消订单'
        return
    simple_order(date, src, dst, passengers, seat, train, detail)
    print '购票成功，请在页面上进行支付'

if __name__ == '__main__':
    main()
