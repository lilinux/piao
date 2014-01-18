#!/usr/bin/env python
#-*-coding: utf-8 -*-


class BasePiaoError(Exception):
    pass


class ValidateError(BasePiaoError):
    pass


class LoginError(BasePiaoError):
    pass


class SubmitOrderError(BasePiaoError):
    pass


class SubmitTokenError(BasePiaoError):
    pass


class CheckOrderError(BasePiaoError):
    pass


class ConfirmOrderError(BasePiaoError):
    pass


class QueryOrderError(BasePiaoError):
    pass


class OrderResultError(BasePiaoError):
    pass


class PayOrderError(BasePiaoError):
    pass


class NoSuchTrain(BasePiaoError):
    pass


class NoSuchSeat(BasePiaoError):
    pass


class TicketSoldOut(BasePiaoError):
    pass


class NotLogin(BasePiaoError):
    pass


class NotEnoughTicket(BasePiaoError):
    pass
