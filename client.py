import sys
import time
import _thread
import argparse
from datetime import datetime
import quickfix as fix
from tools.echo import echo

ECHO_DEBUG=False
if ECHO_DEBUG:
    from tools.echo import echo
else:
    def echo(f):
        def decorated(*args, **kwargs):
            f(*args, **kwargs)
        return decorated

class Application(fix.Application):
    orderID = 0
    execID = 0
    def gen_ord_id(self):
        global orderID
        orderID+=1
        return orderID

    @echo
    def onCreate(self, sessionID):
            return
    @echo
    def onLogon(self, sessionID):
            self.sessionID = sessionID
            print ("Successful Logon to session '%s'." % sessionID.toString())
            return
    @echo
    def onLogout(self, sessionID):
        self.sessionID = sessionID
        print("Successful Logout from session '%s'." % sessionID.toString())
        return
    @echo
    def toAdmin(self, sessionID, message):
        self.sessionID = sessionID
        self.message = message
        msg = fix.Message()
        msg.getHeader().setField(fix.MsgType('1'))
        print(f'Outcoming message:{self.message}')

        if message == fix.MsgType_Heartbeat:
            print('HEARTBEAT!')
        return
    @echo
    def fromAdmin(self, sessionID, message):
        self.sessionID = sessionID
        self.message = message
        print(f'Incoming message:{self.message}')
        if message == fix.MsgType_Heartbeat:
            print('HEARTBEAT!')
        return

    @echo
    def toApp(self, sessionID, message):
        print ("Received the following message: %s" % message.toString())
        return
    @echo
    def fromApp(self, message, sessionID):
        return
    @echo
    def genOrderID(self):
    	self.orderID = self.orderID+1
    	return self.orderID
    @echo
    def genExecID(self):
    	self.execID = self.execID+1
    	return self.execID
    def put_order(self):
        print("Creating the following order: ")
        trade = fix.Message()
        trade.getHeader().setField(fix.BeginString(fix.BeginString_FIX42)) #
        trade.getHeader().setField(fix.MsgType(fix.MsgType_NewOrderSingle)) #39=D
        trade.getHeader().setField(fix.SendingTime(1))
        trade.getHeader().setField(fix.MsgType('0'))
        trade.setField(fix.ClOrdID(self.genExecID())) #11=Unique order

        trade.setField(fix.HandlInst(fix.HandlInst_MANUAL_ORDER_BEST_EXECUTION)) #21=3 (Manual order, best executiona)
        trade.setField(fix.Symbol('EURUSD')) #55=SMBL ?
        trade.setField(fix.Side(fix.Side_BUY)) #43=1 Buy
        trade.setField(fix.OrdType(fix.TriggerOrderType_LIMIT)) #40=2 Limit order
        trade.setField(fix.OrderQty(100)) #38=100
        trade.setField(fix.Price(10))
        trade.setField(fix.Account('U01049'))
        trade.setField(fix.ExDestination('IDEALPRO'))
        trade.setField(fix.CustomerOrFirm(0))
        # tag = fix.TransactTime()
        # tag.setString(datetime.utcnow().strftime('%Y%m%d-%H:%M:%S'))
        # trade.setField(tag)
        # trade.setField((fix.Text('test_order')))
        # trade.setField(fix.TransactTime(int(datetime.utcnow().strftime("%S"))))
        # trade.setField(fix.TransactTime().setString(datetime.utcnow().strftime('%Y%m%d-%H:%M:%S')))
        print (trade.toString())
        fix.Session.sendToTarget(trade, self.sessionID)



def main(config_file):
    try:
        settings = fix.SessionSettings(config_file)
        application = Application()
        storeFactory = fix.FileStoreFactory(settings)
        logFactory = fix.FileLogFactory(settings)
        initiator = fix.SocketInitiator(application, storeFactory, settings, logFactory)
        initiator.start()

        while 1:
                # input = '1'
                input_ = input('enter 1 for order, 2 for exit: ')
                print('\n')
                if input_ == '1':
                    print ("Putin Order")
                    application.put_order()
                    # initiator.stop()
                if input_ == '2':
                    sys.exit(0)
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
