# -*- coding: utf-8 -*-
import datetime
from quik import Quik
from trading import market
from trading.order import Order, BUY, SELL, EXECUTED, ACTIVE, KILLED
    
ORDER_OP = {"Купля":BUY,"Продажа":SELL}

class QuikMarket(market.Market):

    def __init__(self, path, dde):
        market.Market.__init__(self)

        self.conn = Quik( path, dde )
        self.bid = {}
        self.ask = {}
        self.conn.subscribe( "TICKERS", {
            "seccode":"Код бумаги",
            "classcode":"Код класса",
            "price":"Цена послед."
        }, self.ontick )

        self.conn.subscribe( "ORDERS", {
            "order_key":"Номер",
            "seccode":"Код бумаги",
            "operation":"Операция",
            "price":"Цена",
            "quantity":"Кол-во",
            "left":"Остаток",
            "state":"Состояние"
        }, self.onorder )

        self.conn.subscribe( "BOOK", {
            "price":"Цена",
            "ask":"Покупка",
            "bid":"Продажа"
        }, self.onbook, self.onbookready )

    def onbookready(self,tool):
        ticker = self.ticker( tool )
        ticker.book( self.bid, self.ask )
        self.bid = {}
        self.ask = {}

    def onbook(self,data):
        if data["bid"]:
            self.bid[ data["price"] ] = data["bid"]
        if data["ask"]:
            self.ask[ data["price"] ] = data["ask"]
 
    def ontick(self,data):
        """ Quik tickers data handler """
        ticker = self.ticker( data["seccode"] )
        ticker.classcode = data["classcode"]
        ticker.time = datetime.datetime.now()
        ticker.price = data["price"]
        ticker.volume = 0
        self.tick(ticker)

    def onorder(self,data):
        state = data["state"]
        ticker = self.__getattr__( data["seccode"] )
        order = ticker.order( int( data["order_key"] ) )
        order.operation = ORDER_OP[ data["operation"] ]
        order.price = float( data["price"] )
        order.quantity = int( data["quantity"] )
        order.quantity_left = int( data["left"] )
        if state == "Исполнена": 
            order.status = EXECUTED
            order.onexecuted()
            order.delete()
        if state == "Активна": 
            order.status = ACTIVE
            order.onregistered()
        if state == "Снята": 
            order.status = KILLED
            order.onkilled()
            order.delete()
