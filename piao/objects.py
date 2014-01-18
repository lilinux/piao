#!/usr/bin/env python
#-*-coding: utf-8 -*-


class Passenager(object):
    def __init__(self, rsp_data_item):
        self.__dict__.update(rsp_data_item)


class Ticket(object):
    def __init__(self, rsp_data_item):
        self.__dict__['secretStr'] = rsp_data_item.get('secretStr')
        self.__dict__.update(rsp_data_item['queryLeftNewDTO'])
