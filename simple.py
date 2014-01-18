from piao.api import *
#-*-coding: utf-8 -*-

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

    orders = query_incomplete_order_with_login(username, password)
    if orders:
        print '有未完成订单，车次为[%s]' % ','.join(orders)
        print '请先在页面上支付订单或取消订单'
        return
    simple_order(date, src, dst, passengers, seat, train, detail)
    print '购票成功，请在页面上进行支付'

if __name__ == '__main__':
    main()
