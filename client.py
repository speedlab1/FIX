import sys
import time
import _thread
import argparse
from datetime import datetime
import quickfix as fix
from tools.echo import echo
import pandas as pd
import numpy as np

class Application(fix.Application):
    orders = []
    orderID = 100
    execID = 100

    def gen_ord_id(self):
        global orderID
        orderID += 1
        return orderID

    def onCreate(self, sessionID):
            print(f'New Session created!\n ID: {sessionID.toString()}')
            return

    def onLogon(self, sessionID):
            self.sessionID = sessionID
            print ("Successful Logon to session '%s'." % sessionID.toString())
            return

    def onLogout(self, sessionID):
        self.sessionID = sessionID
        print("Successful Logout from session '%s'." % sessionID.toString())
        return

    def toAdmin(self,  message, sessionID):
        self.sessionID = sessionID
        self.message = message
        if self.message.getHeader().getField(35) == '0':
            print('->HrtBt')
        else:
            print(f'-> ADMIN... {self.message}')

        return

    def fromAdmin(self,  message, sessionID):
        self.sessionID = sessionID
        self.message = message
        if self.message.getHeader().getField(35) == '0':
            print('<-HrtBt')
        elif self.message.getHeader().getField(35) == 'A':
            print('<- ADMIN for LOGON !')
            print(self.message)
        elif self.message.getHeader().getField(35) == '3':
            print(self.message)
        else:
            print(f'<- ADMIN...{self.message}')
        return


    def toApp(self,  message, sessionID):
        print ("-> APP: %s..." % message.toString())
        return

    def fromApp(self, message, sessionID):
        self.message = message
        if self.message.getHeader().getField(35) == '8':
            self.orders.append(self.message.getField(11))
            if self.message.getField(150) == '0':
                print('NEW ORDER ACKNOWLEDGED!')
            elif self.message.getField(150) == '8':
                print('.')
            print ('EXECUTION REPORT:\n')
            print(message.toString())
        else:
            print(f'<- APP: {message.toString()}')
        return

    def genOrderID(self):
        self.orderID = self.orderID+1
        return str(self.orderID)

    def genExecID(self):
        self.execID = self.execID+1
        return str(self.execID)

    def put_order(self,security_type,symbol,currency,quantity,side,order_type,account,price=None):
        trade = fix.Message()
        '''
        STANDARD MESSAGE HEADER
        Required Tags: 8(BeginString) - 9(BodyLength) - 35(MsgType) - 49(SenderCompID) - 56(TargetCompID) - 34(MsgSeqNum) - 52(SendingTime)
        '''
        trade.getHeader().setField(fix.BeginString(fix.BeginString_FIX42)) #
        trade.getHeader().setField(fix.MsgType(fix.MsgType_NewOrderSingle)) #39=D
        trade.getHeader().setField(fix.SendingTime(1))
        # unique_order_id = self.genExecID()
        # print(f'Unique Order ID: {unique_order_id}')
        # trade.setField(fix.ClOrdID(unique_order_id)) #11=Unique order

        trade.setField(fix.HandlInst(fix.HandlInst_AUTOMATED_EXECUTION_ORDER_PUBLIC_BROKER_INTERVENTION_OK)) #21=3 (Manual order), 21=2 automated execution only supported value
        trade.setField(fix.Symbol(str(symbol))) #55
        trade.setField(fix.Currency(str(currency))) #15
        trade.setField(fix.SecurityType(str(security_type))) #167
        trade.setField(fix.Side(str(side))) #54=1 Buy
        trade.setField(fix.OrdType(str(order_type))) #40=2 Limit order, 40=1 Market
        trade.setField(fix.OrderQty(quantity)) #38
        # trade.setField(fix.Price(1.12)) # if market should be absent
        trade.setField(fix.Account(str(account)))
        trade.setField(fix.ExDestination('IDEALPRO'))
        trade.setField(fix.CustomerOrFirm(0))
        trade.setField(fix.ClOrdID(datetime.utcnow().strftime('%Y%m%d%H%M%S')+trade.getField(55)+trade.getField(15)+trade.getField(54))) #11=

        # dnow = datetime.utcnow().strftime('%Y%m%d-%H:%M:%S')
        # tag = fix.TransactTime() #default = current time, SendingTime does the same thing
        # tag.setString(dnow.strftime('%Y%m%d-%H:%M:%S'))
        # trade.setField(tag)
        print(f'Creating the following order:\n {trade.toString()}')
        fix.Session.sendToTarget(trade, self.sessionID)
        print('order sent!')

    def order_status_request(self):
        ord_status_request = fix.Message()
        ord_status_request.getHeader().setField(fix.BeginString(fix.BeginString_FIX42)) #
        ord_status_request.getHeader().setField(fix.MsgType('H')) #39=D
        ord_status_request.getHeader().setField(fix.SendingTime(1))
        # ord_status_request.setField(fix.Symbol('EUR')) #55
        # ord_status_request.setField(fix.Account('U01049'))
        # ord_status_request.setField(fix.SecurityReqID('1'))
        ord_status_request.setField(fix.ClOrdID(str(self.orders[0]))) #11=
        # ord_status_request.setField(fix.ClOrdID(str('*'))) #11=
        # ord_status_request.setField(fix.ClOrdID(datetime.utcnow().strftime('%Y%m%d%H%M%S')+ 'statReq' + self.genExecID())) #11=
        # ord_status_request.setField(fix.OrderID(datetime.utcnow().strftime('%Y%m%d%H%M%S')+ 'statReq' + self.genExecID()))
        # ord_status_request.setField(fix.OrderID('*'))
        # ord_status_request.setField(fix.SecurityType('CASH')) #167
        # ord_status_request.setField(fix.Side(fix.Side_SELL))
        print(f'Order status message \n {ord_status_request}')
        fix.Session.sendToTarget(ord_status_request,self.sessionID)
        print('order status request for open orders sent!')

    def test_req(self):
        print("Creating testing message... ")
        test_message = fix.Message()
        test_message.getHeader().setField(fix.MsgType('1'))
        test_message.setField(fix.TestReqID('test'))
        print('sending Test message...')
        print (f'test message: {test_message.toString()}')
        # print(f'session ID: {self.sessionID}')
        fix.Session.sendToTarget(test_message, self.sessionID)
        print('test message sent!')

    def order_cancel_request(self,account,symbol,side,quantity):
        print("Creating order_cancel_request message... ")
        cancel_request_message = fix.Message()
        cancel_request_message.getHeader().setField(fix.BeginString(fix.BeginString_FIX42)) #
        cancel_request_message.getHeader().setField(fix.MsgType('F')) #39=D
        cancel_request_message.getHeader().setField(fix.SendingTime(1))

        cancel_request_message.setField(fix.Account(str(account))) #1
        cancel_request_message.setField(fix.ClOrdID(str('order_cancel_request'+self.genOrderID()))) #11
        cancel_request_message.setField(fix.OrigClOrdID(str(self.orders[0]))) #41
        cancel_request_message.setField(fix.Symbol(str(symbol))) #55
        cancel_request_message.setField(fix.Side(str(side))) #54
        cancel_request_message.setField(fix.OrderQty(quantity)) #38

        print('sending order_cancel_request message...')
        print(f'order_cancel_request message: {cancel_request_message.toString()}')
        fix.Session.sendToTarget(cancel_request_message, self.sessionID)
        print('order_cancel_request message sent!')

    def order_cancel_replace(self,account,symbol,side,quantity,order_type,price):
        print("Creating order_cancel_replace message... ")
        cancel_replace_message = fix.Message()
        cancel_replace_message.getHeader().setField(fix.BeginString(fix.BeginString_FIX42)) #
        cancel_replace_message.getHeader().setField(fix.MsgType('G')) #39=D
        cancel_replace_message.getHeader().setField(fix.SendingTime(1))

        cancel_replace_message.setField(fix.Account(str(account))) #1
        cancel_replace_message.setField(fix.HandlInst(fix.HandlInst_AUTOMATED_EXECUTION_ORDER_PUBLIC_BROKER_INTERVENTION_OK)) #21=3 (Manual order), 21=2 automated execution only supported value
        cancel_replace_message.setField(fix.ClOrdID(str('order_cancel_replace'+self.genOrderID()))) #11
        cancel_replace_message.setField(fix.OrigClOrdID(str(self.orders[0]))) #41
        cancel_replace_message.setField(fix.Symbol(str(symbol))) #55
        cancel_replace_message.setField(fix.Side(str(side))) #54
        cancel_replace_message.setField(fix.OrderQty(quantity)) #38
        cancel_replace_message.setField(fix.OrdType(str(order_type))) #40
        cancel_replace_message.setField(fix.Price(price)) #44

        print('sending order_cancel_replace message...')
        print(f'order_cancel_replace message: {cancel_replace_message.toString()}')
        fix.Session.sendToTarget(cancel_replace_message, self.sessionID)
        print('order_cancel_replace message sent!')


def main(config_file):

    path = 'C:/Users/ak\Downloads\quickfix_example/'
    order = pd.read_csv(f'{path}speedlab_orders.csv')
    symbol = ''.join([a for a in order.iloc[1][0] if a.isalnum()])
    strategy = ''.join([a for a in order.iloc[1][1] if a.isalnum()])
    action = ''.join([a for a in order.iloc[1][5] if a.isalnum()])
    account = ''.join([a for a in order.iloc[1][7] if a.isalnum()])
    exec_time = ''.join([a for a in order.iloc[1][15] if a.isalnum()])
    price = None
    quantity = ''.join([a for a in order.iloc[1][30] if a.isalnum()])
    # tag_55 = symbol[6:9] #Symbol
    # tag_15 = symbol[9:12] #Currency
    # tag_54 = str(np.where('BUY' in action,1,2)) #Side
    security_type = 'CASH' #tag 167
    symbol = 'EUR' #tag 55
    currency = 'AUD' #tag 15
    quantity = 10000 #tag 38
    side = 1 #tag 54
    order_type = 1 #tag 40
    account = 'U01049' #tag 1
    if order_type == 1:
        price = None
    else:
        price = 1. #limit


    try:
        settings = fix.SessionSettings(config_file)
        application = Application()
        storeFactory = fix.FileStoreFactory(settings)
        logFactory = fix.FileLogFactory(settings)
        initiator = fix.SocketInitiator(application, storeFactory, settings, logFactory)
        initiator.start()

        while 1:
                # input = '1'
                input_ = input('enter 1 for order, 2 for exit, 3 for order status update, 4 for order cancel request test for test request :\n ')
                print('\n')
                if input_ == '1':
                    print ("Putin Order")
                    application.put_order(security_type=security_type, symbol=symbol, currency=currency, quantity=quantity, side=side, order_type=order_type,
                                  account=account,price=price)
                    # initiator.stop()
                if input_ == '2':
                    sys.exit(0)
                if input_ == 'test':
                    application.test_req()
                if input_ == '3':
                    print('requesting order status...')
                    application.order_status_request()
                if input_ == '4':
                    print('order cancel request...')
                    application.order_cancel_request(account=account,symbol=symbol,side=side,quantity=quantity)
                if input_ == '5':
                    print('order cancel replace...')
                    application.order_cancel_replace(account=account,symbol=symbol,side=side,quantity=quantity,
                                                     order_type=2,price=1.1)

                if input_ == 'd':
                    import pdb
                    pdb.set_trace()
                else:
                    print ("Valid input is 1 for order, 2 for exit")
                    continue
    # except (fix.ConfigError, fix.RuntimeError), e:
    except :
        print ('ERROR')

if __name__=='__main__':

    config_path = 'C:/Users/ak\Downloads\quickfix_example/client.cfg'

    # def get_config_params(path=config_path):
    #     # parser = argparse.ArgumentParser(description='FIX Client')
    #     # parser.add_argument('file_name', type=str, help='Name of configuration file')
    #     # args = parser.parse_args()

    # import configparser
    # config = configparser.ConfigParser()
    # config['DEFAULT'] = {'ConnectionType':'initiator',
    #                      'LogonTimeout' :'30',
    #                     'ReconnectInterval' : '30'
    #                      }
    # config['SESSION'] = {}
    # config['SESSION']['BeginString'] = 'FIX.4.2'
    # config['SESSION']['SenderCompID'] = 'qafix49'
    # config['SESSION']['TargetCompID'] = 'IB'
    # config['SESSION']['StartTime'] = '00:00:00'
    # config['SESSION']['EndTime'] = '00:00:00'
    # config['SESSION']['HeartBtInt'] = '30'
    # config['SESSION']['SocketConnectPort'] = '7496'
    # config['SESSION']['HeartBtInt'] = '30'
    # config['SESSION']['SocketConnectHost'] = '127.0.0.1'
    # config['SESSION']['DataDictionary'] = 'C:/Users/ak\Downloads\quickfix - 1.15.1_python_un\quickfix - 1.15.1\spec/FIX42.xml'
    # with open('config_file.ini','w') as config_file:
    #     config.write(config_file)
    # main(config)
    main(config_path)
