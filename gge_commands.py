import hashlib
import time
import pprint
import math
import copy
import json
from queue import Empty

from gge_model import AuthenticatedPlayer, Castle, RV, Commander, BladeCoast
from gge_utils import decode2, getError
from gge_constants import *
import logging

# Timeout in seconds

GG_HEADER = "%xt%EmpirefourkingdomsExGG_4%"
GG_TAIL = "%\0"

LOG_TOOLS_TROOPS_BUILDING_IDS = True

# Global State
model = {}
pp = pprint.PrettyPrinter(indent=3)
logger = None


####################
# Model management
####################

def setPlayer(player):
    global model
    model['player'] = player


def getPlayer():
    # global model
    return model['player']


def setMovements(movements):
    global model
    _log("READ {:d} movement records".format(len(movements)))
    model['movements'] = movements


def setBonus(bonus):
    global model
    model['bonus'] = bonus


def getBonus():
    return model['bonus']


def getMovements():
    return model['movements']


def setBladeCoast(bc):
    global model
    _log("Blade Coast is ON")
    model['blade_coast'] = bc


def getBladeCoast():
    if 'blade_coast' in model:
        return model['blade_coast']
    return None


def updateCoins(coins, rubies):
    global model
    model['coins'] = coins
    model['rubies'] = rubies


def getCoins():
    """
    Returns coins and rubies
    :return: 2 ints
    """
    return model['coins'], model['rubies']


##################
# Logging & Utils
##################

def pretty_print(toPrint, msgPrefix=''):
    _log(pp.pformat(toPrint), msgPrefix)


def error(msg):
    logging.getLogger('commands').error(msg)


def info(msg):
    logging.getLogger('commands').info(msg)


def _log(msg, msgPrefix=''):
    if msgPrefix is not None and len(msgPrefix) > 0:
        msg = msgPrefix + ' ' + msg
    logging.getLogger('commands').debug(msg)


def formatMessage(payload):
    return GG_HEADER + payload + GG_TAIL


#################
# Commands
#################


class Command(object):
    def __init__(self):
        pass


class Login(Command):
    def __init__(self, username, password, phoneID, gameVersion):
        Command.__init__(self)
        self.username = username
        self.password = password
        self.phoneID = phoneID
        self.gameVersion = gameVersion

#     def execute(self, processor):
#         # Version check
#         print ("login-start")
# # 0000   00 19 c6 02 9d e3 94 c6 91 d0 52 e8 08 00 45 00   ..........R...E.
# # 0010   00 6e 2c 8f 40 00 80 06 0e b7 c0 a8 6e 15 ae 81   .n,.@.......n...
# # 0020   e2 04 e0 fb 01 bb 40 6b 00 47 5e 0a 0b 4a 50 18   ......@k.G^..JP.
# # 0030   02 04 d0 a1 00 00 3c 6d 73 67 20 74 3d 27 73 79   ......<msg t='sy
# # 0040   73 27 3e 3c 62 6f 64 79 20 61 63 74 69 6f 6e 3d   s'><body action=
# # 0050   27 76 65 72 43 68 6b 27 20 72 3d 27 30 27 3e 3c   'verChk' r='0'><
# # 0060   76 65 72 20 76 3d 27 31 36 36 27 20 2f 3e 3c 2f   ver v='166' /></
# # 0070   62 6f 64 79 3e 3c 2f 6d 73 67 3e 00               body></msg>.


#         message = "<msg t='sys'><body action='verChk' r='0'>"
#         message += "<ver v='" + self.gameVersion + "' /></body></msg>\0"
#         processor.sendMessage(message)
        
#         response = processor.readResult()  # read: <msg t='sys'><body action='apiOK' r='0'></body></msg>
#         _log("R1: " + response)
# # 0000   00 19 c6 02 9d e3 94 c6 91 d0 52 e8 08 00 45 00   ..........R...E.
# # 0010   00 d1 2c 90 40 00 80 06 0e 53 c0 a8 6e 15 ae 81   ..,.@....S..n...
# # 0020   e2 04 e0 fb 01 bb 40 6b 00 8d 5e 0a 0b 80 50 18   ......@k..^...P.
# # 0030   02 04 59 7d 00 00 3c 6d 73 67 20 74 3d 27 73 79   ..Y}..<msg t='sy
# # 0040   73 27 3e 3c 62 6f 64 79 20 61 63 74 69 6f 6e 3d   s'><body action=
# # 0050   27 6c 6f 67 69 6e 27 20 72 3d 27 30 27 3e 3c 6c   'login' r='0'><l
# # 0060   6f 67 69 6e 20 7a 3d 27 45 6d 70 69 72 65 66 6f   ogin z='Empirefo
# # 0070   75 72 6b 69 6e 67 64 6f 6d 73 45 78 47 47 5f 32   urkingdomsExGG_2
# # 0080   39 27 3e 3c 6e 69 63 6b 3e 3c 21 5b 43 44 41 54   9'><nick><![CDAT
# # 0090   41 5b 5d 5d 3e 3c 2f 6e 69 63 6b 3e 3c 70 77 6f   A[]]></nick><pwo
# # 00a0   72 64 3e 3c 21 5b 43 44 41 54 41 5b 31 36 30 36   rd><![CDATA[1606
# # 00b0   38 33 39 33 36 34 37 32 34 25 65 6e 25 30 5d 5d   839364724%en%0]]
# # 00c0   3e 3c 2f 70 77 6f 72 64 3e 3c 2f 6c 6f 67 69 6e   ></pword></login
# # 00d0   3e 3c 2f 62 6f 64 79 3e 3c 2f 6d 73 67 3e 00      ></body></msg>.

#         # Login 29, 4
#         message = "<msg t='sys'><body action='login' r='0'>"
#         message += "<login z='EmpirefourkingdomsExGG_4'>"
#         message += "<nick><![CDATA[]]></nick>"
#         message += "<pword><![CDATA[1606839364724%en%0]]></pword>"
#         message += "</login></body></msg>\0"

#         processor.sendMessage(message)
        
#         response = processor.readResult()  # read: %xt%rlu%-1%1%3585%100000%2%Lobby%
#         _log("R2: " + response)
        
#         message = "<msg t='sys'><body action='autoJoin' r='-1'></body></msg>\0"
#         processor.sendMessage(message)

#         response = processor.readResult()  # read: %xt%core_nfo%-1%0%{"minNameSize":3,"sectorCountX":99,"sectorCountY":99,"XML":"8.RC.35"}%
#         _log("R3: " + response)

#         response = processor.readResult()  # read: <msg t='sys'><body action='joinOK' r='1'><pid id='0'/><vars /><uLs r='1'></uLs></body></msg>
#         _log("R4: " + response)

#         # message = "<msg t='sys'><body action='roundTrip' r='1'></body></msg>"
#         # processor.sendMessage(message)

#         # message = formatMessage('core_vck%1%{"S":"itunes","SI":"1874167067","V":1036051,"P":"com.goodgamestudios.empirefourkingdoms"}')
#         # processor.sendMessage(message)
        
#         # response = processor.readResult()  # read: <msg t='sys'><body action='roundTripRes' r='1'></body></msg>
#         # _log("R5: " + response)
#         # response = processor.readResult()  # read: %xt%core_vck%1%0%11.RC.40%4.2.1%
#         # _log("R6: " + response)

#         # md5pswrd = hashlib.md5(self.password).hexdigest()
#         # message = formatMessage('core_lga%1%{' + '"L":"en"' + ',"PW":"' + md5pswrd +
#         #                         '","NM":"' + self.username + '","DID":5' + ',"AID":"' +
#         #                         self.phoneID + '","PLFID":"3"' + '}')
#         # message = formatMessage('core_lga%1%{' + '"L":"en"' + ',"PW":"' + md5pswrd +
#         #                         '","NM":"' + self.username + '","DID":5' + ',"AID":"' +
#         #                         self.phoneID + '","PLFID":"3"' + '}')

#         # message = formatMessage('%xt%EmpirefourkingdomsExGG_29%core_avl%1%{"LN":"moon","P":"asdasd2123"}%\0')
#         message = '%xt%EmpirefourkingdomsExGG_4%core_avl%1%{"LN":"' + self.username + '","P":"'+self.password+'"}%\0'
#         processor.sendMessage(message)
        
        
        
#         response = processor.readResult()  # read: %xt%ufa%1%0%
#         _log("8: " + response)

#         print ("login-end")
#         # data = processor.q_gbd.get(True, TIMEOUT)
#         data = processor.q_gbd.get(True)
        
#         _log("DATA: " + data)
#         decoded = decode2(data)
#         player = self.parse_gbd_response(decoded)
#         setPlayer(player)
#         updateCoins(decoded['gcu']['C1'], decoded['gcu']['C2'])

#         # This is a hack, it sometimes takes a little longer to get %gam% messages representing movements.
#         time.sleep(2)

#         movements = []
#         while not processor.q_gam.empty():
#             data = processor.q_gam.get(True)
#             movements.append(decode2(data))

#         setMovements(movements)
#         return player

    def execute(self, processor):
        # Version check
        print ("login-start")
# 0000   00 19 c6 02 9d e3 94 c6 91 d0 52 e8 08 00 45 00   ..........R...E.
# 0010   00 6e 2c 8f 40 00 80 06 0e b7 c0 a8 6e 15 ae 81   .n,.@.......n...
# 0020   e2 04 e0 fb 01 bb 40 6b 00 47 5e 0a 0b 4a 50 18   ......@k.G^..JP.
# 0030   02 04 d0 a1 00 00 3c 6d 73 67 20 74 3d 27 73 79   ......<msg t='sy
# 0040   73 27 3e 3c 62 6f 64 79 20 61 63 74 69 6f 6e 3d   s'><body action=
# 0050   27 76 65 72 43 68 6b 27 20 72 3d 27 30 27 3e 3c   'verChk' r='0'><
# 0060   76 65 72 20 76 3d 27 31 36 36 27 20 2f 3e 3c 2f   ver v='166' /></
# 0070   62 6f 64 79 3e 3c 2f 6d 73 67 3e 00               body></msg>.


        message = "<msg t='sys'><body action='verChk' r='0'>"
        message += "<ver v='" + self.gameVersion + "' /></body></msg>\0"
        processor.sendMessage(message)
        
        response = processor.readResult()  # read: <msg t='sys'><body action='apiOK' r='0'></body></msg>
        _log("R1: " + response)
# 0000   00 19 c6 02 9d e3 94 c6 91 d0 52 e8 08 00 45 00   ..........R...E.
# 0010   00 d1 2c 90 40 00 80 06 0e 53 c0 a8 6e 15 ae 81   ..,.@....S..n...
# 0020   e2 04 e0 fb 01 bb 40 6b 00 8d 5e 0a 0b 80 50 18   ......@k..^...P.
# 0030   02 04 59 7d 00 00 3c 6d 73 67 20 74 3d 27 73 79   ..Y}..<msg t='sy
# 0040   73 27 3e 3c 62 6f 64 79 20 61 63 74 69 6f 6e 3d   s'><body action=
# 0050   27 6c 6f 67 69 6e 27 20 72 3d 27 30 27 3e 3c 6c   'login' r='0'><l
# 0060   6f 67 69 6e 20 7a 3d 27 45 6d 70 69 72 65 66 6f   ogin z='Empirefo
# 0070   75 72 6b 69 6e 67 64 6f 6d 73 45 78 47 47 5f 32   urkingdomsExGG_2
# 0080   39 27 3e 3c 6e 69 63 6b 3e 3c 21 5b 43 44 41 54   9'><nick><![CDAT
# 0090   41 5b 5d 5d 3e 3c 2f 6e 69 63 6b 3e 3c 70 77 6f   A[]]></nick><pwo
# 00a0   72 64 3e 3c 21 5b 43 44 41 54 41 5b 31 36 30 36   rd><![CDATA[1606
# 00b0   38 33 39 33 36 34 37 32 34 25 65 6e 25 30 5d 5d   839364724%en%0]]
# 00c0   3e 3c 2f 70 77 6f 72 64 3e 3c 2f 6c 6f 67 69 6e   ></pword></login
# 00d0   3e 3c 2f 62 6f 64 79 3e 3c 2f 6d 73 67 3e 00      ></body></msg>.

        # Login 29, 4
        message = "<msg t='sys'><body action='login' r='0'>"
        message += "<login z='EmpirefourkingdomsExGG_4'>"
        message += "<nick><![CDATA[]]></nick>"
        message += "<pword><![CDATA[1606839364724%en%0]]></pword>"
        message += "</login></body></msg>\0"

        processor.sendMessage(message)
        
        response = processor.readResult()  # read: %xt%rlu%-1%1%3585%100000%2%Lobby%
        _log("R2: " + response)
        
        message = "<msg t='sys'><body action='autoJoin' r='-1'></body></msg>\0"
        processor.sendMessage(message)

        response = processor.readResult()  # read: %xt%core_nfo%-1%0%{"minNameSize":3,"sectorCountX":99,"sectorCountY":99,"XML":"8.RC.35"}%
        _log("R3: " + response)

        response = processor.readResult()  # read: <msg t='sys'><body action='joinOK' r='1'><pid id='0'/><vars /><uLs r='1'></uLs></body></msg>
        _log("R4: " + response)

        # message = "<msg t='sys'><body action='roundTrip' r='1'></body></msg>"
        # processor.sendMessage(message)

        # message = formatMessage('core_vck%1%{"S":"itunes","SI":"1874167067","V":1036051,"P":"com.goodgamestudios.empirefourkingdoms"}')
        # processor.sendMessage(message)
        
        # response = processor.readResult()  # read: <msg t='sys'><body action='roundTripRes' r='1'></body></msg>
        # _log("R5: " + response)
        # response = processor.readResult()  # read: %xt%core_vck%1%0%11.RC.40%4.2.1%
        # _log("R6: " + response)

        # md5pswrd = hashlib.md5(self.password).hexdigest()
        # message = formatMessage('core_lga%1%{' + '"L":"en"' + ',"PW":"' + md5pswrd +
        #                         '","NM":"' + self.username + '","DID":5' + ',"AID":"' +
        #                         self.phoneID + '","PLFID":"3"' + '}')
        # message = formatMessage('core_lga%1%{' + '"L":"en"' + ',"PW":"' + md5pswrd +
        #                         '","NM":"' + self.username + '","DID":5' + ',"AID":"' +
        #                         self.phoneID + '","PLFID":"3"' + '}')

        # message = formatMessage('%xt%EmpirefourkingdomsExGG_29%core_avl%1%{"LN":"moon","P":"asdasd2123"}%\0')
        message = '%xt%EmpirefourkingdomsExGG_4%core_avl%1%{"LN":"' + self.username + '","P":"'+self.password+'"}%\0'
        processor.sendMessage(message)
        
        
        
        response = processor.readResult()  # read: %xt%ufa%1%0%
        _log("8: " + response)
        decoded = decode2(response)
        print(decoded['M'])
        # response = processor.readResult()  # read: %xt%ufa%1%0%
        # response = processor.readResult()  # read: %xt%ufa%1%0%
        # response = processor.readResult()  # read: %xt%ufa%1%0%
        print ("login-end")

        # Version check
        print ("loading-start")
# 0000   00 19 c6 02 9d e3 94 c6 91 d0 52 e8 08 00 45 00   ..........R...E.
# 0010   00 6e 2c 8f 40 00 80 06 0e b7 c0 a8 6e 15 ae 81   .n,.@.......n...
# 0020   e2 04 e0 fb 01 bb 40 6b 00 47 5e 0a 0b 4a 50 18   ......@k.G^..JP.
# 0030   02 04 d0 a1 00 00 3c 6d 73 67 20 74 3d 27 73 79   ......<msg t='sy
# 0040   73 27 3e 3c 62 6f 64 79 20 61 63 74 69 6f 6e 3d   s'><body action=
# 0050   27 76 65 72 43 68 6b 27 20 72 3d 27 30 27 3e 3c   'verChk' r='0'><
# 0060   76 65 72 20 76 3d 27 31 36 36 27 20 2f 3e 3c 2f   ver v='166' /></
# 0070   62 6f 64 79 3e 3c 2f 6d 73 67 3e 00               body></msg>.


        message = "<msg t='sys'><body action='verChk' r='0'>"
        message += "<ver v='" + self.gameVersion + "' /></body></msg>\0"
        processor.sendMessage(message)
        
        response = processor.readResult()  # read: <msg t='sys'><body action='apiOK' r='0'></body></msg>
        _log("L1: " + response)
# 0000   00 19 c6 02 9d e3 94 c6 91 d0 52 e8 08 00 45 00   ..........R...E.
# 0010   00 d1 2c 90 40 00 80 06 0e 53 c0 a8 6e 15 ae 81   ..,.@....S..n...
# 0020   e2 04 e0 fb 01 bb 40 6b 00 8d 5e 0a 0b 80 50 18   ......@k..^...P.
# 0030   02 04 59 7d 00 00 3c 6d 73 67 20 74 3d 27 73 79   ..Y}..<msg t='sy
# 0040   73 27 3e 3c 62 6f 64 79 20 61 63 74 69 6f 6e 3d   s'><body action=
# 0050   27 6c 6f 67 69 6e 27 20 72 3d 27 30 27 3e 3c 6c   'login' r='0'><l
# 0060   6f 67 69 6e 20 7a 3d 27 45 6d 70 69 72 65 66 6f   ogin z='Empirefo
# 0070   75 72 6b 69 6e 67 64 6f 6d 73 45 78 47 47 5f 32   urkingdomsExGG_2
# 0080   39 27 3e 3c 6e 69 63 6b 3e 3c 21 5b 43 44 41 54   9'><nick><![CDAT
# 0090   41 5b 5d 5d 3e 3c 2f 6e 69 63 6b 3e 3c 70 77 6f   A[]]></nick><pwo
# 00a0   72 64 3e 3c 21 5b 43 44 41 54 41 5b 31 36 30 36   rd><![CDATA[1606
# 00b0   38 33 39 33 36 34 37 32 34 25 65 6e 25 30 5d 5d   839364724%en%0]]
# 00c0   3e 3c 2f 70 77 6f 72 64 3e 3c 2f 6c 6f 67 69 6e   ></pword></login
# 00d0   3e 3c 2f 62 6f 64 79 3e 3c 2f 6d 73 67 3e 00      ></body></msg>.

        # Login 29, 4
        message = "<msg t='sys'><body action='login' r='0'>"
        message += "<login z='EmpirefourkingdomsExGG_4'>"
        message += "<nick><![CDATA[]]></nick>"
        message += "<pword><![CDATA[1606839364724%en%0]]></pword>"
        message += "</login></body></msg>\0"

        processor.sendMessage(message)
        
        response = processor.readResult()  # read: %xt%rlu%-1%1%3585%100000%2%Lobby%
        _log("L2_1: " + response)

        response = processor.readResult()  # read: %xt%rlu%-1%1%3585%100000%2%Lobby%
        _log("L2_2: " + response)
        
        message = "<msg t='sys'><body action='autoJoin' r='-1'></body></msg>\0"
        processor.sendMessage(message)

        response = processor.readResult()  # read: %xt%core_nfo%-1%0%{"minNameSize":3,"sectorCountX":99,"sectorCountY":99,"XML":"8.RC.35"}%
        _log("L3: " + response)

        message = "<msg t='sys'><body action='roundTrip' r='1'></body></msg>"
        processor.sendMessage(message)

        message = '%xt%EmpirefourkingdomsExGG_4%core_vck%1%{"S":"googleplay","V":4006034,"P":"com.goodgamestudios.empirefourkingdoms","SI":"3129777221"}%\0'
        processor.sendMessage(message)
        
        time.sleep(2)
        response = processor.readResult()  # read: <msg t='sys'><body action='roundTripRes' r='1'></body></msg>
        _log("L4: " + response)
        

# %xt%Empire
# 0040   66 6f 75 72 6b 69 6e 67 64 6f 6d 73 45 78 47 47   fourkingdomsExGG
# 0050   5f 34 25 63 6f 72 65 5f 6c 67 61 25 31 25 7b 22   _4%core_lga%1%{"
# 0060   44 49 44 22 3a 37 2c 22 4c 22 3a 22 65 6e 22 2c   DID":7,"L":"en",
# 0070   22 41 49 44 22 3a 22 31 36 30 37 36 36 31 39 31   "AID":"160766191
# 0080   34 30 32 39 39 32 39 32 38 37 22 2c 22 4e 4d 22   4029929287","NM"
# 0090   3a 22 6b 6a 75 64 79 36 40 79 61 68 6f 6f 2e 63   :"kjudy6@yahoo.c
# 00a0   6f 6d 22 2c 22 41 46 55 49 44 22 3a 22 31 36 30   om","AFUID":"160
# 00b0   37 36 36 31 39 31 33 38 39 31 2d 37 39 31 39 33   7661913891-79193
# 00c0   32 32 38 32 34 39 30 32 37 34 34 35 37 33 22 2c   22824902744573",
# 00d0   22 50 4c 46 49 44 22 3a 22 33 22 2c 22 50 57 22   "PLFID":"3","PW"
# 00e0   3a 22 31 65 39 37 61 66 65 37 31 33 33 33 36 35   :"1e97afe7133365
# 00f0   36 33 39 34 39 63 30 63 32 61 65 65 38 32 32 64   63949c0c2aee822d
# 0100   30 65 22 2c 22 49 44 46 56 22 3a 6e 75 6c 6c 2c   0e","IDFV":null,
# 0110   22 41 44 49 44 22 3a 22 35 34 32 63 36 38 35 35   "ADID":"542c6855
# 0120   2d 32 37 33 66 2d 34 64 33 64 2d 38 34 33 36 2d   -273f-4d3d-8436-
# 0130   33 66 37 37 38 30 38 61 62 39 37 36 22 7d 25 00   3f77808ab976"}%
        # message = '%xt%EmpirefourkingdomsExGG_4%core_lga%1%{"DID":7,"L":"en","AID":"1607661914029929287","NM":"kjudy6@yahoo.com","AFUID":"1607661913891-7919322824902744573","PLFID":"3","PW":"1e97afe713336563949c0c2aee822d0e","IDFV":null,"ADID":"542c6855-273f-4d3d-8436-3f77808ab976"}%\0'
        message = '%xt%EmpirefourkingdomsExGG_4%core_lga%1%{"DID":7,"L":"en","AID":"1607661914029929287","NM":'+decoded['M']+',"AFUID":"1607661913891-7919322824902744573","PLFID":"3","PW":"'+decoded['P']+'","IDFV":null,"ADID":"542c6855-273f-4d3d-8436-3f77808ab976"}%\0'
        processor.sendMessage(message)

        response = processor.readResult()  # read: <msg t='sys'><body action='roundTripRes' r='1'></body></msg>
        # _log("L5: " + response)

        response = processor.readResult()  # read: %xt%core_vck%1%0%11.RC.40%4.2.1%
        _log("L6: " + response)
        
        response = processor.readResult()  # read: %xt%ufa%1%0%
        _log("L7: " + response)

        response = processor.readResult()  # read: %xt%ufa%1%0%
        _log("L8: " + response)

        print ("loading-end")
        # data = processor.q_gbd.get(True, TIMEOUT)
        data = processor.q_gbd.get(True)
        
        # _log("DATA: " + data)
        decoded = decode2(data)
        player = self.parse_gbd_response(decoded)
        setPlayer(player)
        updateCoins(decoded['gcu']['C1'], decoded['gcu']['C2'])

        # This is a hack, it sometimes takes a little longer to get %gam% messages representing movements.
        time.sleep(2)

        movements = []
        while not processor.q_gam.empty():
            data = processor.q_gam.get(True)
            movements.append(decode2(data))

        setMovements(movements)
        return player

    def parse_gbd_response(self, response):
        playerLevel = response['gxp']['LVL']
        playerXP = response['gxp']['XP']
        xpOfPreviousLevel = response['gxp']['XPFCL']
        xpForNextLevel = response['gxp']['XPTNL']

        email = response['gpi']['E']
        playerID = response['gpi']['PID']
        playerName = response['gpi']['PN']
        allianceID = response['gal']['AID']
        allianceName = response['gal']['N']

        feast = response['boi']['bfs']

        # pretty_print(response)
        ops, castleGreen, castleIce, castleSand, castleFire, castleBerimond = parse_castles(response['gcl']['C'])
        rvMap = parseRVs(response)
        kts = []
        if 'gkl' in response:
            for entry in response['gkl']['AI']:
                kts.append(entry[0])

        # TODO replace commanders dict with this ... but need to update all references to it elsewhere...
        newCommanders = {}
        # newCommanders = self.parse_commanders(response['gli']['G'])
        # castellans = self.parse_castellans(response['gli']['B'])

        commanders = {}
        for com in response['gli']['G']:
            # Commander map: Name = ID
            commanders[com['N']] = com['ID']

        if 'tmp' in response:
            bc = self.parse_blade_coast(response['tmp'])
            if bc:
                setBladeCoast(bc)

        timeSkips = None
        # if 'MS' in response['msc']:
        #     # Speed boosts per slot: 1min, 5min, 10min, 30min, 1h, 5h, 24h
        #     # "msc":{"MS":[20,12,3,0,0,0,0]},
        #     timeSkips = response['msc']['MS']

        player = AuthenticatedPlayer(playerName, playerID, allianceName, allianceID, castleGreen, ops, castleIce, castleSand, castleFire,
                                     castleBerimond, rvMap, commanders, newCommanders, timeSkips, feast)
        return player

    @staticmethod
    def parse_commanders(payload):
        _log("L9: " + json.dumps(payload))
        # Using a list allows for multiple commanders with the same name to exist (although there is still no easy way to distinctly each one specifically)
        commanders = []
        for com in payload:
            armor_attributes = {}
            for piece in com['EQ']:
                for attribute in piece[5]:
                    atype = attribute[0]
                    avalue = attribute[1][0]
                    if atype not in armor_attributes:
                        armor_attributes[atype] = 0
                    armor_attributes[atype] = armor_attributes[atype] + avalue

            for a in armor_attributes.keys():
                _log("Com {} attribute {}={:3.1f}".format(com['N'], equipment_bonus_to_string(a), armor_attributes[a]))

            # commanders[com['N']] = {}
            # commanders[com['N']]['ID'] = com['ID']
            # commanders[com['N']]['EQ_BONUS'] = armor_attributes

            commanders.append(Commander(com['ID'], com['N'], armor_attributes))

        return commanders

    @staticmethod
    def parse_castellans(payload):
        castellans = {}
        for cast in payload:
            # They do not have names, they are associated to a castle
            # castellans[com['N']] = cast['ID']
            pass
        return castellans

    @staticmethod
    def parse_blade_coast(payload):
        # Conditional checks to ensure we don't break anything when the event is not on.
        # 1- Not sure if 'tmp' is only for blade coast
        # 2- Not sure if 'TM' can be absent if 'tmp' is present
        # 3- Not sure if positions can change if more than one event is on and how to distinguish between events

        if 'TM' in payload and len(payload['TM']) > 0:
            # Content of GBD response
            # bladeCoastID = payload['tmp']['TM'][0]['MID']
            # campContent = payload['tmp']['TM'][0]['S'] # Wood, Stone, Food, Max capacity for Stone, Food, Wood
            # campTroops  = payload['tmp']['TM'][0]['I'] # Troops

            # Content of TMP response
            # bladeCoastID = payload['TM'][0]['MID']
            # campContent = payload['TM'][0]['S'] # Wood, Stone, Food, Max capacity for Stone, Food, Wood
            # campTroops  = payload['TM'][0]['I'] # Troops
            return BladeCoast(payload['TM'][0])
        return None


def parse_castles(kingdoms):
    ops = []
    castleGreen = None
    castleIce = None
    castleSand = None
    castleFire = None
    castleBerimond = None
    for kingdom in kingdoms:
        kingdomID = kingdom['KID']
        if kingdomID == KINGDOM_GREEN:
            for castle in kingdom['AI']:
                ai = castle['AI']
                c = parseCastle(KINGDOM_GREEN, ai)
                opType = ai[0]

                # Seems more reliable for castle type than ai[0]: -1 for main in all kingdoms, 0 for food op...
                # whereas: ai[0] is 1 for green main, 4 for food op, 12 for non green main ...
                # TODO what are the values for wood/stone ops as well as 8-2/6-2 variants
                # opType = castle['TA']
                # _log("type=" + str(opType))
                if opType == 1:
                    castleGreen = c
                elif opType == 4:
                    ops.append(c)
        else:
            # This happens in some cases I can't explain
            if len(kingdom['AI']) == 0:
                _log("Skipping kid={:d}".format(kingdom['KID']))
                continue

            c = parseCastle(kingdomID, kingdom['AI'][0]['AI'])
            if kingdomID == KINGDOM_SANDS:
                castleSand = c
            if kingdomID == KINGDOM_ICE:
                castleIce = c
            if kingdomID == KINGDOM_FIRE:
                castleFire = c
            if kingdomID == KINGDOM_BERIMOND:
                castleBerimond = c

    return ops, castleGreen, castleIce, castleSand, castleFire, castleBerimond


def parseCastle(kingdomID, ai):
    return Castle(ai[0], ai[1], ai[2], ai[3], ai[10], kingdomID)


#
# Response parsing routines common to multiple command responses
#
def parseRVs(response):
    """Parse RV info portion of GBD/GDI response
       Both GBD (this is for you) and GDI (this is info about any player) contain a kgv{VI:[]} array.
       The difference is that for GBD each element contains 2 sub-elements the RV and the troop/tool counts. Whereas GDI only contains 1 sub-element the RV.
       Sample elements:
       GBD [[10,667,361,2352813,1241521,2,2,-1,"Food 4"],[[628,25],[603,1],[631,35]]]
       GDI [[10,667,361,2352813,1241521,2,2,-1,"Food 4"]]
       :param response:
    """
    rvMap = {}
    if 'kgv' in response:
        for entry in response['kgv']['VI']:
            rvinfo = entry[0]
            rvkingdom = rvinfo[6]  # 1: sands, 2: ice, 3: peaks
            rv = parseRV(rvinfo, entry[1])
            if rvkingdom in rvMap:
                rvList = rvMap[rvkingdom]
            else:
                rvList = []
                rvMap[rvkingdom] = rvList
            rvList.append(rv)

            # Only present in GBD
            if len(entry) > 1:
                troopToolCounters = entry[1]
                # TODO expand on this if needed rv.setTroopToolCounters(entry[1])
    return rvMap


def parseRV(rvInfo, rvTroops):
    # rvInfo[0]             # no idea always: 10
    # rvInfo[1]             # X coord
    # rvInfo[2]             # Y coord
    # rvInfo[3]             # Looks like an ID
    # rvInfo[4]             # same as PlayerID
    # rvInfo[5]             # 0: wood, 1: stone, 2: food
    # rvInfo[6]             # 1: sands, 2: ice, 3: peaks
    # rvInfo[7]             # No idea, always -1
    # rvInfo[8]             # Name (unicode string)
    # rvTroops              # List of [troop/tool ID, count pairs], ie: [[631, 1], [628, 1], [606, 1], [685, 1]]
    return RV(rvInfo[5], rvInfo[1], rvInfo[2], rvInfo[3], rvInfo[8], rvInfo[6], rvTroops)


def createLoginCommand(ini):
    return Login(ini['Auth.username'], ini['Auth.password'], ini['Auth.device_id'], ini['Game.version'])


def createJumpToIce(castleID):
    return JumpToCastle(KINGDOM_ICE, castleID)


def createJumpToSands(castleID):
    return JumpToCastle(KINGDOM_SANDS, castleID)


def createJumpToFire(castleID):
    return JumpToCastle(KINGDOM_FIRE, castleID)


def createJumpToGreen(castleID):
    return JumpToCastle(KINGDOM_GREEN, castleID)


class JumpToWorld(Command):
    """
    """

    def __init__(self, kingdomID=KINGDOM_GREEN):
        Command.__init__(self)
        self.kingdomID = kingdomID
        self.result = None
        self.allCastlesOnMap = None

    def execute(self, processor):
        info("WGD - Jump to World {}".format(kingdom_to_string(self.kingdomID)))
        processor.sendMessage(formatMessage('wgd%1%{"KID":' + str(self.kingdomID) + '}'))
        response = processor.q_gaa.get(True)
        decoded = decode2(response)

        # The GAA response format varies a bit depending on what is being sent back with it ... in response to a wgd it contains barons you've hit in the past under 'AI'
        # as well as Nomads
        #
        # --> 2 means baron
        # --> 27 means nomad castle
        #
        # [ 2, X, Y, spy_report_id, level, time_till_attackable, kingdom_id]         << RBC
        # [27, X, Y, spy_report_id, level, time_till_attackable, kingdom_id, -601]   << Nomad
        #
        # {   u'AI': [   [2, 1157, 418, -1, 18, 0, 0]
        #                [2, 1150, 419, -1, 25, 0, 0]
        #                [2, 1154, 1222, -1, 12, 0, 0]
        #                [2, 1145, 420, -1, 1, 0, 0]
        #                [2, 1154, 420, -1, 108, 0, 0]
        #                [27, 1149, 424, -1, 8, 8629, 0, -601]
        #                [27, 1148, 425, -1, 7, 11753, 0, -601]
        #                [27, 1155, 426, -1, 8, 9413, 0, -601]
        #                [27, 1158, 421, -1, 6, 3594, 0, -601]  <<< Don't know what -601 means
        #                [13, 1144, 437, -1, 75, 1]             <<< Robber baron king entry (identified by 13)
        # }
        #
        # ----------------------------------------------------
        #
        # In response to a GAA request it doesn't list barons but it does list players+villages, fortress, monuments, Nomads, foreign legions (and probably samurais didnt check this one)
        #
        # -->  1 means human main castle (YOURS AND SOMEONE ELSE'S)
        # -->  4 means human OP (YOURS AND SOMEONE ELSE'S)
        # --> 23 means KT (YOURS AND SOMEONE ELSE'S)
        #
        # --> 11 means fortress
        # --> 26 means Monument
        # --> 27 means nomad castle
        #
        # There is also an extra field for fortresses right before the kingdom id (probably the id of the last player who defeated it)
        #
        # [11, X, Y, spy_report_id, level, time_till_attackable, ?last_conqueror_id?, kingdom_id]
        # [11,594,516,-1,45,35286,1014328,1]
        #
        # ----------------------------------------------------
        #
        # --> 21 means foreign legion castle
        #
        # %xt%gaa%1%0%{"KID":0,"uap":{"KID":0,"NS":-1,"PMS":-1,"PMT":0},
        # "AI":[
        #       [21,1150,422,61,-1,0,80,80,10],
        #       [21,1150,425,62,22203,0,80,80,10],
        #       [21,1157,412,69,5002,0,100,100,20] << level 69 so last 3 values seem to point to wall/gate/moat bonuses ) which is better than on level 68 and below which is coherent
        #
        # [21, X, Y, castle level, ???py_report_id or time_since_spied_on???, 0, wall?, gate?, moat?]
        #
        # ----------------------------------------------------
        #
        #  --> ?? means samurai?
        #

        # pretty_print(decoded, "WGD response\n")
        self.result = decoded
        self.allCastlesOnMap = parse_gaa_response(decoded)
        return decoded


class GetPlayerTargetData(Command):
    """
    """

    def __init__(self, srcX, srcY, targetX, targetY, kingdomID=KINGDOM_GREEN):
        Command.__init__(self)
        self.kingdomID = kingdomID
        self.srcX = srcX
        self.srcY = srcY
        self.targetX = targetX
        self.targetY = targetY
        self.result = None

    def execute(self, processor):
        info("ACI - Get Target Data")
        # %xt%EmpirefourkingdomsExGG_4%aci%1%{"SY":587,"TX":363,"TY":819,"KID":2,"SX":866}%
        processor.sendMessage(formatMessage('aci%1%{"SY":' + str(self.srcY) + ',"TX":' + str(self.targetX) + ',"TY":' +
                                            str(self.targetY) + ',"KID":' + str(self.kingdomID) + ',"SX":' + str(self.srcX) + '}'))
        response = processor.q_aci.get(True)
        decoded = decode2(response)
        rc = getError(response)
        if rc == 131:
            info("This castle lord is protected from attacks")  # Bird
            raise Exception("This castle lord is protected from attacks")
        # pretty_print(decoded, "ACI response\n")
        self.result = decoded
        return decoded


class GetTargetData(Command):
    """
    """

    def __init__(self, srcX, srcY, targetX, targetY, kingdomID=KINGDOM_GREEN):
        Command.__init__(self)
        self.kingdomID = kingdomID
        self.srcX = srcX
        self.srcY = srcY
        self.targetX = targetX
        self.targetY = targetY
        self.result = None

    def execute(self, processor):
        info("ADI - Get Target Data")
        # TODO the order has probably changed in the most recent releases
        # {"TX":600,"KID":1,"SX":598,"TY":491,"SY":493}%
        processor.sendMessage(formatMessage('adi%1%{"TX":' + str(self.targetX) + ',"KID":' + str(self.kingdomID) +
                                            ',"SX":' + str(self.srcX) + ',"TY":' + str(self.targetY) + ',"SY":' + str(self.srcY) + '}'))
        response = processor.q_adi.get(True)
        decoded = decode2(response)
        # pretty_print(decoded, "ADI response\n")
        self.result = decoded
        return decoded


class CheckAvailableSpies(Command):
    def __init__(self, targetX, targetY, kingdomID):
        Command.__init__(self)
        self.__kingdomID = kingdomID
        self.__targetX = targetX
        self.__targetY = targetY
        self.result = None
        self.availableSpies = 0

    def execute(self, processor):
        info("SSI - ")
        # %xt%EmpirefourkingdomsExGG_4%ssi%1%{"TY":772,"KID":1,"TX":515}%
        # <<< Here are you're available spies
        # %xt%ssi%1%0%{"TX":515,"TY":772,"gaa":{"KID":1,"uap":{"KID":1,"NS":-1,"PMS":-1,"PMT":0},"AI":[],"OI":[]},"AS":15,"APM":0,"TPM":0,"GC":50}%

        processor.sendMessage(formatMessage('ssi%1%{"TY":' + str(self.__targetY) + ',"KID":' + str(self.__kingdomID) + ',"TX":' + str(self.__targetX) + '}'))
        response = processor.q_ssi.get(True)
        decoded = decode2(response)
        pretty_print(decoded, "SSI response\n")
        self.availableSpies = decoded['AS']
        self.result = response


class BaseSpyCommand(Command):
    def __init__(self, targetX, targetY, kingdomID, sourceCastleID, spyCount, percentage, speed):
        Command.__init__(self)
        self._kingdomID = str(kingdomID)
        self._targetX = str(targetX)
        self._targetY = str(targetY)
        self._castleID = str(sourceCastleID)
        self._speed = str(speed)
        self._spyCount = str(spyCount)
        self._percentage = str(percentage)
        self.result = None


class Sabotage(BaseSpyCommand):
    def __init__(self, targetX, targetY, kingdomID, sourceCastleID, spyCount, percentage=100, speed=-1):
        BaseSpyCommand.__init__(self, targetX, targetY, kingdomID, sourceCastleID, spyCount, percentage, speed)

    def execute(self, processor):
        info("CSM - ")
        #
        # Sabotage is almost identical to a Spy command but it has and extra "SD" attribute I don't know what it means and "ST"=2 for sab vs 0 for normal spy
        #    "KID":0       in green
        #    "SE":50       ss the % (100% accuracy requested),
        #    "ST":2        means sabotage
        #    "TX":1155     is the target's X coord.
        #    "SID":1363756 is the source castle's ID,
        #    "HBW":1007    is the speed,
        #    "TY":424      is the target's Y coord.
        #    "SC":5        is the number of spies
        #    "SD":0        I DON'T KNOW
        # %xt%EmpirefourkingdomsExGG_4%csm%1%{"KID":0,"SE":50,"ST":2,"TX":1155,"SID":1363756,"HBW":1007,"TY":424,"SC":5,"SD":0}%

        # @formatter:off
        processor.sendMessage(formatMessage('csm%1%{' +
                                            '"KID":' + self._kingdomID +
                                            ',"SE":' + self._percentage +
                                            ',"ST":' + '2'
                                            ',"TX":' + self._targetX +
                                            ',"SID":' + self._castleID +
                                            ',"HBW":' + self._speed +
                                            ',"TY":' + self._targetY +
                                            ',"SC":' + self._spyCount +
                                            ',"SD":' + '0' +
                                            '}'))
        # @formatter:on

        # Spies traveling to target
        response = processor.q_csm.get(True)
        decoded = decode2(response)
        # pretty_print(decoded, "CSM response\n")
        self.result = decoded


class SendSpies(BaseSpyCommand):
    def __init__(self, targetX, targetY, kingdomID, sourceCastleID, spyCount, percentage=100, speed=-1):
        BaseSpyCommand.__init__(self, targetX, targetY, kingdomID, sourceCastleID, spyCount, percentage, speed)
        self.armyTravelingID = 0
        self.spyReport = None
        self.spyReportStatus = None
        self.spyReportID = 0

    def execute(self, processor):
        info("CSM - ")

        # This is the berimond variant, the speed is 1021 (it is not something you can select in the dialog, it is automatically done for you)
        # %xt%EmpirefourkingdomsExGG_4%csm%1%{"TX":1425,"TY":45,"SD":0,"ST":0,"SID":2001,"HBW":1021,"SC":30,"SE":100,"KID":10}%
        #

        # >>> Spy on it:
        #     "ST":0 # 0 Spy, 2 Sabotage, (I'll assume 1 is economic spy report)
        #     "SID":3689099" is my sand castle's ID,
        #     "HBW":1007 is the speed,
        #     "SC":15  is the number of spies
        #     "TY":772 is the target RBC's X coord,
        #     "SE":100 is the % (100% accuracy requested),
        #     "KID":1 in sands,
        #     "TX":515 is the target RBC's Y coord.
        # %xt%EmpirefourkingdomsExGG_4%csm%1%{"ST":0,"SID":3689099,"HBW":1007,"SC":15,"TY":772,"SE":100,"KID":1,"TX":515}%

        processor.sendMessage(formatMessage('csm%1%{' + '"ST":0' + ',"SID":' + self._castleID + ',"HBW":' +
                                            self._speed + ',"SC":' + self._spyCount + ',"TY":' + self._targetY +
                                            ',"SE":' + self._percentage + ',"KID":' + self._kingdomID + ',"TX":' +
                                            self._targetX + '}'))

        # Spies traveling to target
        response = processor.q_csm.get(True)
        decoded = decode2(response)
        pretty_print(decoded, "CSM response\n")

        self.result = decoded
        self.armyTravelingID = decoded["A"]["M"]["MID"]

        # Empty the queue to await new messages
        while not processor.q_sne.empty():
            processor.q_sne.get_nowait()

        response = processor.q_sne.get(True, 60)  # 1 min is enough for most non Player targets except FL.
        self.spyReport = decode2(response)
        pretty_print(self.spyReport, "SNE response\n")

        # "1+2+2#1+-220+": Failed spy report on RBC in sands (could be any failed spies on RBC ???)
        # "1+0+2#1+-220+": Successful spy report on RBC in sands (could be any successful report on RBC or other???)
        self.spyReportStatus = self.spyReport['MSG'][0][3]
        if self.spyReportStatus == "1+0+2#1+-220+":
            self.spyReportID = self.spyReport['MSG'][0][0]

        # Spies traveling back to castle from Target
        response = processor.q_csm.get(True)
        spiesTravelingBack = decode2(response)
        pretty_print(spiesTravelingBack, "CSM response\n")


class SendSpiesBerimond(SendSpies):
    def __init__(self, targetX, targetY, sourceCastleID, spyCount, percentage=100):
        SendSpies.__init__(self, targetX, targetY, KINGDOM_BERIMOND, sourceCastleID, spyCount, percentage, SPEED_LVL_BERIMOND_COIN_BOOST)


class ReadSpyReport(Command):
    def __init__(self, reportID):
        Command.__init__(self)
        self.__reportID = reportID
        self.result = None

    def execute(self, processor):
        # >>> See spy report details
        # %xt%EmpirefourkingdomsExGG_4%bsd%1%{"MID":514993038}%
        # >>> See spy report details 2nd part?? They seem to be sent together
        # %xt%EmpirefourkingdomsExGG_4%mmr%1%{"MID":514993038}%
        # <<< RESPONSE with RBC's defense formation and update info of player (coin count, rubies, etc)

        # TODO Not sure if both are always sent. And what happens when the report is no longer available in your inbox but you can see it when looking at the baron

        info("BSD - ")
        processor.sendMessage(formatMessage('bsd%1%{"MID":' + str(self.__reportID) + '}'))
        info("MMR - ")
        processor.sendMessage(formatMessage('mmr%1%{"MID":' + str(self.__reportID) + '}'))
        response = processor.q_bsd.get(True)
        decoded = decode2(response)
        pretty_print(decoded, "MMR response\n")
        self.result = decoded


class Pin(Command):
    def __init__(self):
        Command.__init__(self)

    def execute(self, processor):
        info("PIN - ")
        processor.sendMessage(formatMessage('pin%1%{}'))
        processor.q_pin.get(True)


class GetFortressInfo(Command):
    """
    Must NOT be called if target is already on fire (or error code 95 is returned).

    This is actually the message sent to the server when you press on the attack icon on the target fortress.
    """

    def __init__(self, kingdomID, startX, startY, endX, endY):
        Command.__init__(self)
        self.kingdomID = kingdomID
        self._startX = startX
        self._startY = startY
        self._endX = endX
        self._endY = endY
        self.result = None

    def execute(self, processor):
        info("ABI - Get Fortress Info")
        # EmpirefourkingdomsExGG_4%abi%1%{"TX":575,"KID":1,"SX":598,"TY":497,"SY":493}%
        msg = formatMessage('abi%1%{"TX":' + str(self._endX) + ',"KID":' + str(self.kingdomID) + ',"SX":' + str(self._startX) +
                            ',"TY":' + str(self._endY) + ',"SY":' + str(self._startY) + '}')
        processor.sendMessage(msg)
        response = processor.q_abi.get(True)
        rc = getError(response)
        # pretty_print(decoded, "ABI response\n")
        if rc == 0:
            decoded = decode2(response)
            # self.result = parse_abi_response(decoded)
            self.result = decoded
        else:
            # 159: # means it got hit and wont give the info
            info("ABI - RC {:d}".format(rc))


class GetMap(Command):
    def __init__(self, kingdomID, startX, startY, endX, endY):
        Command.__init__(self)
        self.kingdomID = kingdomID
        self._startX = startX
        self._startY = startY
        self._endX = endX
        self._endY = endY
        self.result = None

    def execute(self, processor):
        # info("GAA - Get Map [{},{}] [{},{}]".format(str(self._startX), str(self._startY), str(self._endX), str(self._endY)))
        _log("GAA - Get Map [{},{}] [{},{}]".format(str(self._startX), str(self._startY), str(self._endX), str(self._endY)))
        msg = formatMessage('gaa%1%{"AX1":' + str(self._startX) + ',"AY1":' + str(self._startY) + ',"AX2":' + str(self._endX) +
                            ',"AY2":' + str(self._endY) + ',"KID":' + str(self.kingdomID) + '}')
        processor.sendMessage(msg)
        response = processor.q_gaa.get(True)
        decoded = decode2(response)
        # pretty_print(decoded, "GAA response\n")
        self.result = parse_gaa_response(decoded)


def parse_gaa_response(decoded):
    if False:
        targets = []
        for entry in decoded['AI']:
            # pretty_print(entry, '>>>>>>>>>>>>>>>>>>>>')
            # # There are sometimes empty entries
            if len(entry) == 0:
                continue
            targets.append(entry)
        return targets

    return [entry for entry in decoded['AI'] if len(entry) > 0]


# Run this after initial JCA
class GameStartCommands(Command):
    """
    """

    def __init__(self, allianceID=-1):
        Command.__init__(self)
        self.allianceID = allianceID
        if self.allianceID == -1:
            self.allianceID = getPlayer()._allianceID
        self._result = None

    def execute(self, processor):
        # TODO recent game changes introduced even more messages
        info("GRT -")
        processor.sendMessage(formatMessage('grt%1%{}%'))

        # Returns the daily bonus
        info("ALB -")
        processor.sendMessage(formatMessage('alb%1%{}%'))
        response = processor.q_alb.get(True)
        decoded = decode2(response)
        pretty_print(decoded, "LOGIN BONUS")

        info("SLI -")
        processor.sendMessage(formatMessage('sli%1%{}%'))
        info("SNE -")
        processor.sendMessage(formatMessage('sne%1%{}%'))
        info("AIN -")
        processor.sendMessage(formatMessage('ain%1%{"AID":' + str(self.allianceID) + '}'))
        info("AFA -")
        processor.sendMessage(formatMessage('afa%1%{}%'))
        info("ACL -")
        processor.sendMessage(formatMessage('acl%1%{}%'))
        info("AHL -")
        processor.sendMessage(formatMessage('ahl%1%{}%'))
        # Wasn't sent in my last pcap
        # info("GWH -")
        # processor.sendMessage(formatMessage('gwh%1%{}%'))
        # info("UHT -")
        # processor.sendMessage(formatMessage('uht%1%{}%'))

        info("GBL -")
        processor.sendMessage(formatMessage('gbl%1%{}%'))
        info("FWD -")
        processor.sendMessage(formatMessage('fwd%1%{}%'))


class JumpToCastle(Command):
    """
    """

    # 95% sure kingdomID=KINGDOM_GREEN, castleID=-1 will jump to main not to the map in greens
    def __init__(self, kingdomID=KINGDOM_GREEN, castleID=-1):
        Command.__init__(self)
        self.kingdomID = kingdomID
        self.castleID = castleID
        self._result = None

    def getToolOrTroopCount(self, troopType):
        key = 'tool' + str(troopType)
        if key in self._result:
            return self._result[key]
        return 0

    def execute(self, processor):

# 0000   00 19 c6 02 9d e3 94 c6 91 d0 52 e8 08 00 45 00   ..........R...E.
# 0010   00 5c e7 30 40 00 80 06 e2 60 c0 a8 6e 15 23 99   .\.0@....`..n.#.
# 0020   de b3 dd eb 01 bb 4b 46 70 e3 bd 3c 72 6a 50 18   ......KFp..<rjP.
# 0030   02 04 e7 42 00 00 25 78 74 25 45 6d 70 69 72 65   ...B..%xt%Empire
# 0040   66 6f 75 72 6b 69 6e 67 64 6f 6d 73 45 78 47 47   fourkingdomsExGG
# 0050   5f 34 25 74 78 73 25 31 25 7b 22 54 54 22 3a 30   _4%txs%1%{"TT":0
# 0060   2c 22 54 58 22 3a 33 7d 25 00                     ,"TX":3}%.
        # info("JCA - Jump to Castle, kingdom {}".format(kingdom_to_string(self.kingdomID)+str(self.castleID)))
        
        print ("start Taxes")
        processor.sendMessage('%xt%EmpirefourkingdomsExGG_4%txc%1%{"TR":29}%\0')

        processor.sendMessage('%xt%EmpirefourkingdomsExGG_4%txs%1%{"TT":0,"TX":3}%\0')

        print ("end Taxes")
        response = processor.q_jaa.get(True)
        _log("L11: " + response)
        
        decoded = decode2(response)
        # Produces a lot of output!
        # pretty_print(decoded, "JCA response\n")

        _log("------------------------------------------ " + decoded['gca']['A'][10] + " - START ------------------------------------------")
        self._result, buildings = parse_jaa_response(decoded, self.kingdomID == KINGDOM_BERIMOND)
        _log("------------------------------------------ " + decoded['gca']['A'][10] + " - END   ------------------------------------------")
        getPlayer().getCastleById(decoded['gca']['A'][3]).setBuildings(buildings)
# 0000   00 19 c6 02 9d e3 94 c6 91 d0 52 e8 08 00 45 00   ..........R...E.
# 0010   00 56 94 97 40 00 80 06 35 00 c0 a8 6e 15 23 99   .V..@...5...n.#.
# 0020   de b3 e5 5b 01 bb 35 bf 75 e5 ec 8f ab d2 50 18   ...[..5.u.....P.
# 0030   02 00 26 69 00 00 25 78 74 25 45 6d 70 69 72 65   ..&i..%xt%Empire
# 0040   66 6f 75 72 6b 69 6e 67 64 6f 6d 73 45 78 47 47   fourkingdomsExGG
# 0050   5f 34 25 74 78 63 25 31 25 7b 22 54 52 22 3a 32   _4%txc%1%{"TR":2
# 0060   39 7d 25 00                                       9}%.


def parse_jaa_response(decoded, berimond=False):
    playerData = {'troopSlots': 0, 'toolSlots': 0, 'troopTotalSlots': 0, 'toolTotalSlots': 0, 'hospitalSlots': 0, 'hospitalTotalSlots': 0}

    # if not berimond:
    #     for item in decoded['spl0']['PIDL']:
    #         status = item[0]
    #         if status == -1:
    #             playerData['troopSlots'] += 1
    #         if status != -2:
    #             playerData['troopTotalSlots'] += 1

    #     for item in decoded['spl1']['PIDL']:
    #         status = item[0]
    #         if status == -1:
    #             playerData['toolSlots'] += 1
    #         if status != -2:
    #             playerData['toolTotalSlots'] += 1

    #     # Hospital
    #     parse_hospital(decoded, playerData, 'spl2')

    if berimond:
        for item in decoded['spl2']['PIDL']:
            status = item[0]
            if status == -1:
                playerData['troopSlots'] += 1
            if status != -2:
                playerData['troopTotalSlots'] += 1

        for item in decoded['spl3']['PIDL']:
            status = item[0]
            if status == -1:
                playerData['toolSlots'] += 1
            if status != -2:
                playerData['toolTotalSlots'] += 1

        # TODO there is a hospital in Berimond not sure what it is mapped to though!

    playerData['food'] = int(decoded['grc']['F'])
    playerData['stone'] = int(decoded['grc']['S'])
    playerData['wood'] = int(decoded['grc']['W'])
    playerData['coal'] = int(decoded['grc']['C'])
    playerData['oil'] = int(decoded['grc']['O'])
    playerData['glass'] = int(decoded['grc']['G'])
    playerData['iron'] = int(decoded['grc']['I'])

    # float values with 1 decimal encoded as an ints
    playerData['foodProduction'] = math.floor(decoded['gpa']['DF'] / 10)
    playerData['foodConsumption'] = math.floor(decoded['gpa']['DFC'] / 10)
    playerData['stoneProduction'] = math.floor(decoded['gpa']['DS'] / 10)
    playerData['woodProduction'] = math.floor(decoded['gpa']['DW'] / 10)

    playerData['coalProduction'] = math.floor(decoded['gpa']['DC'] / 10)
    playerData['oilProduction'] = math.floor(decoded['gpa']['DO'] / 10)
    playerData['glassProduction'] = math.floor(decoded['gpa']['DG'] / 10)
    playerData['ironProduction'] = math.floor(decoded['gpa']['DI'] / 10)

    # Copy & remove known
    d2 = copy.deepcopy(decoded['gpa'])
    del d2['DF']
    del d2['DFC']
    del d2['DS']
    del d2['DW']
    del d2['DC']
    del d2['DO']
    del d2['DG']
    del d2['DI']
    playerData['gpa'] = d2

    playerData['barracks'] = -1
    playerData['siegeWorkshop'] = -1
    playerData['stables'] = -1
    playerData['hospital'] = -1

    buildings = {}

    if LOG_TOOLS_TROOPS_BUILDING_IDS:
        for building in decoded['gca']['BD']:
            _log("BUILDING DETAILS type {}, id {}, coords[{}, {}], unknown1 {}, construction elapsed time {}, unknown3 {}, damage {}%, "
                 "unknown4 {}, efficiency {}%, unknown5 {}, unknown6 {}, unknown7 {}, PO {}".format(building_to_string(building[0]).ljust(29, ' '),
                                                                                                    str(building[1]), str(building[2]), str(building[3]), str(building[4]),
                                                                                                    str(building[5]), str(building[6]), str(100 - building[7]),
                                                                                                    str(building[8]), str(building[9]), str(building[10]), str(building[11]),
                                                                                                    (building[12]), str(building[13])))

    allBuildings = decoded['gca']['BD']
    for building in allBuildings:

        buildingType = str(building[0])
        if buildingType not in buildings.keys():
            buildings[buildingType] = 1
        else:
            buildings[buildingType] += 1

        if LOG_TOOLS_TROOPS_BUILDING_IDS:
            _log("Building Type {}={} coords[{:d},{:d}] ID={:d}, damage={:d}%, efficiency={:d}%, PO={:d}".format(buildingType,
                                                                                                                 building_to_string(building[0]).ljust(20, ' '),
                                                                                                                 int(building[2]),
                                                                                                                 int(building[3]),
                                                                                                                 int(building[1]),
                                                                                                                 int(100 - building[7]),
                                                                                                                 int(building[9]),
                                                                                                                 int(building[13])))
        if building[0] in {BUILDING_BARRACKS_LEVEL_1, BUILDING_BARRACKS_LEVEL_2, BUILDING_BARRACKS_LEVEL_3, BUILDING_BARRACKS_LEVEL_4, BUILDING_BARRACKS_LEVEL_5}:
            playerData['barracks'] = building[0]
        elif building[0] in {BUILDING_SIEGE_WORKSHOP_LEVEL_1, BUILDING_SIEGE_WORKSHOP_LEVEL_2, BUILDING_SIEGE_WORKSHOP_LEVEL_3}:
            playerData['siegeWorkshop'] = building[0]
        elif building[0] in {BUILDING_STABLES_LEVEL_1, BUILDING_STABLES_LEVEL_2, BUILDING_STABLES_LEVEL_3}:
            playerData['stables'] = building[0]
        elif building[0] in {BUILDING_HOSPITAL_LEVEL_1, BUILDING_HOSPITAL_LEVEL_2, BUILDING_HOSPITAL_LEVEL_3}:
            #  TODO find ids for higher ospital levels
            playerData['hospital'] = building[0]
        elif building[0] in [BUILDING_BERIMOND_TRAINING_GROUNDS_LEVEL_1, BUILDING_BERIMOND_TRAINING_GROUNDS_LEVEL_2, BUILDING_BERIMOND_TRAINING_GROUNDS_LEVEL_3, BUILDING_BERIMOND_TRAINING_GROUNDS_LEVEL_4, BUILDING_BERIMOND_TRAINING_GROUNDS_LEVEL_5]:
            # Can only happen in berimond
            playerData['training-grounds'] = building[0]

    _log("BARRACKS building {}".format(str(playerData['barracks'])))

    # if LOG_TOOLS_TROOPS_BUILDING_IDS:
    #     _log("--------- Building type DUMP START ---------")
    #     for key, value in buildings.iteritems():
    #         _log("Building type {} count {}".format(building_to_string(key), str(value)))
    #     _log("--------- Building type DUMP END ---------")

    for item in decoded['gui']['I']:
        if LOG_TOOLS_TROOPS_BUILDING_IDS:
            _log("Troop or Tool ID {} count {} name {}".format(str(item[0]).rjust(3, ' '), str(item[1]).rjust(3, ' '), tools_and_troops_to_string(item[0])))
        playerData['tool' + str(item[0])] = item[1]  # use 'tool' for troop and tools doesn't matter

    # Shadow troops
    if 'gsi' in decoded:
        for item in decoded['gsi']['SI']:
            if LOG_TOOLS_TROOPS_BUILDING_IDS:
                _log("Shadow troop or Tool ID {} count {} name {}".format(str(item[0]).rjust(3, ' '), str(item[1]).rjust(3, ' '), tools_and_troops_to_string(item[0])))
            playerData['tool' + str(item[0])] = item[1]

    info("Slots      [troops={:d}/{:d}, tools={:d}/{:d}]".format((playerData['troopTotalSlots'] - playerData['troopSlots']), playerData['troopTotalSlots'],
                                                                 (playerData['toolTotalSlots'] - playerData['toolSlots']), playerData['toolTotalSlots']))
    info("Totals     [food={:d}, wood={:d}, stone={:d}, iron={:d}, glass={:d}, oil={:d}, coal={:d}]".format(playerData['food'], playerData['wood'], playerData['stone'],
                                                                                                            playerData['iron'], playerData['glass'], playerData['oil'],
                                                                                                            playerData['coal']))
    info("Production [food={:n}, wood={:n}, stone={:n}, iron={:n}, glass={:n}, oil={:n}, coal={:n}]".format(playerData['foodProduction'],
                                                                                                            playerData['woodProduction'],
                                                                                                            playerData['stoneProduction'],
                                                                                                            playerData['ironProduction'],
                                                                                                            playerData['glassProduction'],
                                                                                                            playerData['oilProduction'],
                                                                                                            playerData['coalProduction']))
    info("Consumption[food={:n}, net food={:n}]".format(playerData['foodConsumption'], playerData['foodProduction'] - playerData['foodConsumption']))

    return playerData, allBuildings


class JumpToOp(Command):
    def __init__(self, posX, posY):
        Command.__init__(self)
        self.__posX = str(posX)
        self.__posY = str(posY)
        self._result = None

    def getToolOrTroopCount(self, troopType):
        key = 'tool' + str(troopType)
        if key in self._result:
            return self._result[key]
        return 0

    def execute(self, processor):
        info("JAA - Jump to OP")
        # Jumping to an op consists of jumping to green and then jumping to the op's XY coords ...

        # %xt%EmpirefourkingdomsExGG_4%jaa%1%{"PY":730,"KID":0,"PX":1067}%
        processor.sendMessage(formatMessage('jaa%1%{"PY":' + self.__posY + ',"KID":' + str(KINGDOM_GREEN) + ',"PX":' + self.__posX + '}'))
        response = processor.q_jaa.get(True)
        decoded = decode2(response)
        # pretty_print(decoded, "JAA response\n")
        _log("------------------------------------------ " + decoded['gca']['A'][10] + " - START ------------------------------------------")
        self._result, buildings = parse_jaa_response(decoded)
        _log("------------------------------------------ " + decoded['gca']['A'][10] + " - END   ------------------------------------------")

        getPlayer().getCastleById(decoded['gca']['A'][3]).setBuildings(buildings)


class FindNextTowerInBerimond(Command):
    def __init__(self):
        Command.__init__(self)
        self.result = None

    def execute(self, processor):
        info("FNT - Find next tower in Berimond")
        # %xt%EmpirefourkingdomsExGG_4%fnt%1%{}%
        processor.sendMessage(formatMessage('fnt%1%{}'))
        response = processor.q_fnt.get(True)
        decoded = decode2(response)
        self.result =  decoded

# Jumping to the camp in berimond is exactly the same as jumping to and OP except the kingdom is different.
# Note that no world switch is sent prior, don't think there ever is in any jump  directly into a castle (don't see the point).
class JumpToBerimond(Command):
    def __init__(self, posX, posY):
        Command.__init__(self)
        self.__posX = str(posX)
        self.__posY = str(posY)
        self.result = None

    def execute(self, processor):
        info("JAA - Jump to Berimond")
        # %xt%EmpirefourkingdomsExGG_4%jaa%1%{"PX":1340,"PY":87,"KID":10}%
        processor.sendMessage(formatMessage('jaa%1%{"PX":' + self.__posX + ',"PY":' + self.__posY + ',"KID":' + str(KINGDOM_BERIMOND) +  '}'))
        response = processor.q_jaa.get(True)
        decoded = decode2(response)
        pretty_print(decoded, "JAA response\n")

        #  TODO is JAA response is the same as jumping to an castle or an OP, then refactor all 3 classes to use a common base class
        _log("------------------------------------------ " + decoded['gca']['A'][10] + " - START ------------------------------------------")
        self.result, buildings = parse_jaa_response(decoded, True)
        _log("------------------------------------------ " + decoded['gca']['A'][10] + " - END   ------------------------------------------")

        getPlayer().getCastleById(decoded['gca']['A'][3]).setBuildings(buildings)


# Move elements in recruit troops queue
# %xt%EmpirefourkingdomsExGG_4%mup%1%{"LID":0,"NS":3,"OS":1}%
# %xt%mup%1%0%{"spl":{"LID":0,"PIDL":[[686,1,260,531,0,0,1619875749,-1],[687,1,288,531,0,0,1037916640,-1],
#                                     [664,1,324,531,0,0,1006334154,2228971],[672,5,1695,531,0,0,1848682906,2117912],[-1,0,0,0,0,0,0,206232]]}}%



class BuildTroops(Command):
    """ Of interest, the reply %xt%bup%1%0% lists what is being recruited
        ex: [606,1,227,318,0,0,1544717147,-1] means 1 archer, 227 seconds till complete, and 318 rubies to double build them.
        I think last item is rental time left.

        If first item is -1, it's an empty slot.
        If first item is -2, it's locked till rubies are paid.
        The reply also contains resources, gold and ruby counts.
    """

    def __init__(self, troopTypeID=TROOP_TYPE_ARCHER, count=1, askForHelp=True):
        Command.__init__(self)
        if count < 0 or count > 5:
            raise ValueError("Troop count < 0 or > 5")
        self._troopTypeID = troopTypeID
        self._count = count
        self.result = None
        self._askForHelp = askForHelp

    def execute(self, processor):
        info("BUP - Build Troops - " + tools_and_troops_to_string(self._troopTypeID) + " : " + str(self._count))
        # processor.sendMessage(formatMessage('gui%1%{}') )
        # 1- This simulates the sequence done by the client
        # 2- The response actually contains current counters of all items in stock you have in the castle
        # time.sleep(2)
        # response = processor.q_gui.get(True)
        # decoded = decode2(response)
        # pretty_print(decoded, "GUI Response\n")
        # time.sleep(5)

        # req: %xt%EmpirefourkingdomsExGG_4%bup%1%{"LID":0,"WID":686,"PWR":0,"AMT":1}%
        #
        # res: %xt%bup%1%0%{"spl":{"LID":0,"PIDL":[[664,1,315,530,0,0,795282588,-1],[687,1,289,530,0,0,2033534690,-1],
        #                   [664,1,325,530,0,0,1668323679,2513516], [-1,0,0,0,0,0,0,2402457],[-1,0,0,0,0,0,0,213847]]},
        #                   "grc":{"AID":2683939,"W":5952.625,"S":42343.863,"F":50985.824,"KID":0},"gcu":{"C1":7123269,"C2":152732}}%
        #
        msg = formatMessage('bup%1%{' + '"LID":0' + ',' + '"WID":' + str(self._troopTypeID) + ',' + '"PWR":0' + ',' + '"AMT":' +
                            str(self._count) + '}')
        processor.sendMessage(msg)
        response = processor.q_bup.get(True)

        self.result, lastRequestId = parse_bup_response(response, 'troopSlots')
        _log("LAST REQUEST ID " + str(lastRequestId))

        if self._askForHelp and lastRequestId > 0:
            self.ask_for_help(processor, lastRequestId)
        return self.result

    @staticmethod
    def ask_for_help(processor, requestId):
        info("AHR - Request Help")
        time.sleep(0.5)  # (2)
        processor.sendMessage(formatMessage('ahr%1%{"T":1,' + '"ID":' + str(requestId) + '}'))
        response = processor.q_ahh.get(True)
        decoded = decode2(response)
        # pretty_print(decoded, "AHR Response\n")
        return decoded


class BuildBerimondTroops(BuildTroops):
    def __init__(self, troopTypeID=TROOP_TYPE_MARKSMAN, count=1, askForHelp=True):
        BuildTroops.__init__(self, troopTypeID, count, askForHelp)

    def execute(self, processor):
        info("BUP - Build Troops - " + tools_and_troops_to_string(self._troopTypeID) + " : " + str(self._count))

        msg = formatMessage('bup%1%{' + '"SK":15' + ',"LID":3' + ',' + '"WID":' + str(self._troopTypeID) + ',' + '"PWR":0' + ',' + '"AMT":' + str(self._count) + '}')
        processor.sendMessage(msg)
        response = processor.q_bup.get(True)

        self.result, lastRequestId = parse_bup_response(response, 'troopSlots')
        _log("LAST REQUEST ID " + str(lastRequestId))

        if self._askForHelp and lastRequestId > 0:
            self.ask_for_help(processor, lastRequestId)
        return self.result


def parse_bup_response(response, slotTypeName):
    rc = getError(response)
    decoded = decode2(response)
    # pretty_print(decoded)

    playerData = {slotTypeName: 0}
    lastRequestId = 0
    if rc == 0:
        for item in decoded['spl']['PIDL']:
            status = item[0]  # id of type being built or -1 for empty -2 for ruby locked
            # item[1] # Number of troops in slot
            # item[2] # Time
            # item[3] # ???
            # item[4] # ???
            # item[5] # ???
            # item[6] # Production request id
            # item[7] # Time remaining for rental of slot, -1 if not rented

            # For troop recruiting
            # TODO A) what indicates help request was sent
            # TODO B) what indicates help request was accepted (troop count doesn't seem to pass to 6 for example)
            if status == -1:
                playerData[slotTypeName] += 1
            elif item[6] > 0:
                lastRequestId = item[6]

        playerData['food'] = int(decoded['grc']['F'])
        playerData['stone'] = int(decoded['grc']['S'])
        playerData['wood'] = int(decoded['grc']['W'])
        playerData['coal'] = int(decoded['grc']['C'])
        playerData['oil'] = int(decoded['grc']['O'])
        playerData['glass'] = int(decoded['grc']['G'])
        playerData['iron'] = int(decoded['grc']['I'])
        playerData['coins'] = int(decoded['gcu']['C1'])
        playerData['rubies'] = int(decoded['gcu']['C2'])
        playerData['lastRequestId'] = lastRequestId
        updateCoins(decoded['gcu']['C1'], decoded['gcu']['C2'])
    else:
        info("Build Tools FAILED RC: {}".format(str(rc)))

    return playerData, lastRequestId


def parse_hru_response(response):
    decoded = decode2(response)
    playerData = {'hospitalSlots': 0, 'hospitalTotalSlots': 0}
    parse_hospital(decoded, playerData, 'spl')
    return playerData


def parse_hospital(decoded, playerData, splKey='spl'):
    _log(">>>> parse_hospital IN")
    if splKey in decoded and 'PIDL' in decoded[splKey]:
        for item in decoded[splKey]['PIDL']:
            status = item[0]
            _log("item in ['" + splKey + "']['PIDL']  status " + str(status))
            if status == -1:
                playerData['hospitalSlots'] += 1
            if status != -2:
                playerData['hospitalTotalSlots'] += 1

    # Same as
    injuredTroops = {}
    if 'HI' in decoded['gui']:
        _log(">>>> parse_hospital HI IN GUI")
        for injuredTroop in decoded['gui']['HI']:
            _log("adding entry " + str(injuredTroop) + " to injuredTroops")
            injuredTroops[injuredTroop[0]] = injuredTroop[1]
    else:
        _log(">>>> parse_hospital HI NOT IN GUI")
    playerData['injuredTroops'] = injuredTroops


class HealTroops(Command):
    def __init__(self, troopTypeID, troopCount, requestHelp=False):
        Command.__init__(self)
        self.__troopTypeID = troopTypeID
        self.__troopCount = troopCount
        self._result = None
        self.__requestHelp = requestHelp

    # def getResult(self):
    #     return self.__result

    def execute(self, processor):
        info("HRU - Heal Troops")
        # %xt%EmpirefourkingdomsExGG_4%hru%1%{"A":10,"U":76}%

        processor.sendMessage(formatMessage('hru%1%{' + '"A":' + str(self.__troopCount) + ',' + '"U":' + str(self.__troopTypeID) + '}'))
        response = processor.q_hru.get(True)
        # decoded = decode2(response)
        self._result = parse_hru_response(response)
        # self.__result,lastRequestId  = parse_hru_response(response)
        # TODO ask for help ask_for_help_for_hospital(lastRequestId)


class RemoveTroopsFromHospital(Command):
    def __init__(self, troopTypeID, troopCount=1):
        Command.__init__(self)
        self.__troopTypeID = troopTypeID
        self.__troopCount = troopCount
        self.__result = None

    def execute(self, processor):
        info("HDU - Remove Troops From Hospital")
        # %xt%EmpirefourkingdomsExGG_4%hdu%1%{"A":20,"U":759}%

        processor.sendMessage(formatMessage('hdu%1%{' + '"A":' + str(self.__troopCount) + ',' + '"U":' + str(self.__troopTypeID) + '}'))
        response = processor.q_hdu.get(True)
        decoded = decode2(response)
        self.__result = self.parse_hdu_response(decoded)

    @staticmethod
    def parse_hdu_response(response):
        return response  # TODO parse it and see what can be used


class BuildTools(Command):
    def __init__(self, toolTypeID, count=1):
        Command.__init__(self)
        if count < 0 or count > 5:
            raise ValueError("Tool count < 0 or > 5")
        self._toolTypeID = toolTypeID
        self._count = count
        self._result = None

    def execute(self, processor):
        # Get 19 glory banners (there is no build time for these)
        # %EmpirefourkingdomsExGG_4%bup%1%{"WID":661,"AMT":19,"PWR":0,"SK":22,"LID":1}%

        # Build 5 mantlets
        # %xt%EmpirefourkingdomsExGG_4%bup%1%{"PWR":0,"SK":22,"LID":1,"WID":620,"AMT":5}%

        info("BUP - Build Tools - " + tools_and_troops_to_string(self._toolTypeID))
        processor.sendMessage(formatMessage('bup%1%{' + '"LID":1' + ',' + '"WID":' + str(self._toolTypeID) + ',' + '"AMT":' + str(self._count) + '}'))
        response = processor.q_bup.get(True)
        rc = getError(response)
        if rc == 0:
            self._result, lastRequestId = parse_bup_response(response, 'toolSlots')
        else:
            raise Exception("BUP - RC {:d}".format(rc))


class GUI(Command):
    def __init__(self):
        Command.__init__(self)
        self._result = None

    def execute(self, processor):
        info("GUI - Print current tool and troop count")
        # 1- This simulates the sequence done by the client 2- The response actually contains current counters of all items in stock you have in the castle
        processor.sendMessage(formatMessage('gui%1%{}'))
        response = processor.q_gui.get(True)
        decoded = decode2(response)
        # pretty_print(decoded, "GUI Response\n")
        GUI.parse_gui_response(decoded)
        self._result = decoded

    @staticmethod
    def parse_gui_response(data):
        for e in data['I']:
            key = e[0]
            nb = e[1]
            if LOG_TOOLS_TROOPS_BUILDING_IDS:
                _log("key: " + str(key) + " [" + tools_and_troops_to_string(key).rjust(3, ' ') + "] count: " + str(nb).rjust(4, ' '))
        for e in data['gsi']['SI']:
            key = e[0]
            nb = e[1]
            if LOG_TOOLS_TROOPS_BUILDING_IDS:
                _log("key: " + str(key) + " [" + tools_and_troops_to_string(key).rjust(3, ' ') + "] count: " + str(nb).rjust(4, ' '))
        for e in data['HI']:  # Hospital
            key = e[0]
            nb = e[1]
            if LOG_TOOLS_TROOPS_BUILDING_IDS:
                _log("key: " + str(key) + " [" + tools_and_troops_to_string(key).rjust(3, ' ') + "] count: " + str(nb).rjust(4, ' '))


class HelpAll(Command):
    def __init__(self):
        Command.__init__(self)

    # TODO how to determine is help is needed ... the AHL message seems to be key, keyword AC seems key but haven't figured it out yet.
    def execute(self, processor):
        info("AHA - Help All")
        processor.sendMessage(formatMessage('aha%1%{}'))
        response = processor.q_aha.get(True)
        _log("AHA response ({})".format(str(response)))
        # decoded = decode2(response)
        # pretty_print(decoded, "AHA Response\n")


# class MUS(Command):
#   def __init__(self):
#     Command.__init__(self)
#     pass
#
#   def execute(self, processor):
#     info("MUS -")
#     # Seems to return what possible items you can build or exist
#     # %xt%EmpirefourkingdomsExGG_4%mus%1%{}%
#     processor.sendMessage(formatMessage('mus%1%{}'))
#     response = processor.q_mus.get(True)
#     #_log( "MUS response: " + response)
#     pretty_print(response)
#     decoded = decode2(response)

class TaxInfo(Command):
    def __init__(self):
        Command.__init__(self)
        self.amount = 0

    def execute(self, processor):
        info("TXI - Tax Info")
        processor.sendMessage(formatMessage('txi%1%{}'))
        response = processor.q_txi.get(True)
        _log("TXI response: " + response)
        decoded = decode2(response)
        self.amount = decoded['TX']['EM']

        # From automation script
        # timeRemaining = int(decoded['TX']['RT'])
        # taxCollecting = int(decoded['TX']['TT'])
        # if taxCollecting == -1:
        # return -1
        # elif timeRemaining <= 0:
        #   return 0
        # elif timeRemaining > 0:
        #   return timeRemaining


class SendTaxCollector(Command):
    """Response: %xt%txs%1%0%{"gcu":{"C1":29443,"C2":2591},"TX":{"TT":0,"RT":600,"EM":282,"IB":0,"PO":845,"BL":-1,"VB":0}}%
    """

    def __init__(self, ttime=0):
        Command.__init__(self)
        # 0 = 10 min
        # 1 = 30 min
        # 3 = 90 min
        # 4 = 180 min
        # 5 = 360 min
        self._time = ttime

    def execute(self, processor):
        info("TXS - Send Tax Collector")
        # sending:   %xt%EmpirefourkingdomsExGG_4%txs%1%{"TX":3,"TT":0}%
        # C1: is amount of coins player now has
        # C2: is amount of rubies player now has
        # RT: is Remaining Time till taxes can be collected (since this is for 10 min and when you send a collect taxes command RT is 0 in the response).
        # processed: %xt%txs%1%0%{"gcu":{"C1":64580,"C2":36917},"TX":{"TT":0,"RT":600,"EM":695,"IB":0,"PO":2085,"BL":-1,"VB":0}}%

        processor.sendMessage(formatMessage('txs%1%{"TX":3,"TT":' + str(self._time) + '}'))
        response = processor.q_txs.get(True)
        _log("TXS response: " + response)
        decoded = decode2(response)
        info("TXS - Taxes, amount to collect: {0}, ready in: {1} seconds. Current coins: {2}, rubies: {3}".format(str(decoded['txi']['TX']['EM']),
                                                                                                                  str(decoded['txi']['TX']['RT']),
                                                                                                                  str(decoded['gcu']['C1']),
                                                                                                                  str(decoded['gcu']['C2'])))
        updateCoins(decoded['gcu']['C1'], decoded['gcu']['C2'])


class CollectTaxes(Command):
    """Response: %xt%txc%1%0%{"CT":630,"gcu":{"C1":29443,"C2":2591},"TX":{"TT":-1,"RT":0,"EM":0,"IB":0,"PO":845,"BL":-1,"VB":0}}%
    C1: is coins
    C2: is rubies
    """

    def __init__(self):
        Command.__init__(self)
        self.result = None

    def execute(self, processor):
        info("TXC - Collect Taxes")
        processor.sendMessage(formatMessage('txc%1%{"RS":0,"TR":17}'))
        response = processor.q_txc.get(True)
        _log("TXC response: " + response)
        decoded = decode2(response)
        info("TXC - Collected coins, coins: " + str(decoded['gcu']['C1']) + ", rubies: " + str(decoded['gcu']['C2']))
        self.result = decoded
        updateCoins(decoded['gcu']['C1'], decoded['gcu']['C2'])


class GetPlayerCastleList(Command):
    """
    %xt%EmpirefourkingdomsExGG_4%gdi%1%{"PID":347270}%
    Response:
    """

    def __init__(self, playerUID):
        Command.__init__(self)
        self._playerUID = playerUID
        self.result = None

    def execute(self, processor):
        info("GDI - Player Castle List")
        # I had 5 in my trace, might always be different or depend on commander or whatever
        processor.sendMessage(formatMessage('gdi%1%{"PID":' + str(self._playerUID) + '}'))
        response = processor.q_gdi.get(True)
        _log("GDI response: " + response)
        decoded = decode2(response)
        # pretty_print(decoded)
        self.result = decoded


class MoveTroopsToCastle(Command):
    """
    %EmpirefourkingdomsExGG_4%cat%1%{"SY":1011,"A":[[664,1],[734,150],[734,150],[734,150],[734,150],[734,150],[734,150]],
    "TX":1151,"KID":0,"HBW":1007,"TY":421,"LID":5,"BPC":0,"SD":0,"SX":111}%
    Response:
    """

    def __init__(self, kingdomID, troopsTools, speed, sourceX, sourceY, targetX, targetY, commanderID):
        Command.__init__(self)
        self.__sourceX = str(sourceX)
        self.__sourceY = str(sourceY)
        self.__targetX = str(targetX)
        self.__targetY = str(targetY)
        self.__kingdomID = str(kingdomID)
        self.__speed = str(speed)
        self.__troopsTools = troopsTools
        self.__commanderID = str(commanderID)
        self.result = None

    def execute(self, processor):
        info("CAT - Station Troops")
        # @formatter:off
        msg = formatMessage('cat%1%{' +
                            '"SY":' + self.__sourceY +
                            ',"A":' + self.__troopsTools +
                            ',"TX":' + self.__targetX +
                            ',"KID":' + self.__kingdomID +
                            ',"HBW":' + self.__speed +
                            ',"TY":' + self.__targetY +
                            ',"LID":' + self.__commanderID +
                            ',"BPC":' + '0'
                            ',"SD":' + '0'
                            ',"SX":' + self.__sourceX +
                            '}')
        # @formatter:on

        processor.sendMessage(msg)

        response = processor.q_cat.get(True)
        _log("CAT response: " + response)

        rc = getError(response)
        if rc == 0:
            decoded = decode2(response)
            # pretty_print(decoded)
            self.result = decoded
        else:
            info("CAT - RC {:d}".format(rc))
            raise Exception("CAT - RC {:d}".format(rc))


class StationTroopsGetTargetInfo(Command):
    """
    This is called on a castle when you wanna send troops/tools to it.
    %xt%EmpirefourkingdomsExGG_4%sti%1%{"SX":111,"TY":421,"SY":1011,"TX":1151,"KID":0}%
    Response:

    """

    def __init__(self, kingdomID, sourceX, sourceY, targetX, targetY):
        Command.__init__(self)
        self.__kingdomID = str(kingdomID)
        self.__sourceX = str(sourceX)
        self.__sourceY = str(sourceY)
        self.__targetX = str(targetX)
        self.__targetY = str(targetY)
        self.result = None

    def execute(self, processor):
        info("STI - Get Target Info To Station Troops")
        # @formatter:off
        msg = formatMessage('sti%1%{' +
                            '"SX":' + self.__sourceX +
                            ',"TY":' + self.__targetY +
                            ',"SY":' + self.__sourceY +
                            ',"TX":' + self.__targetX +
                            ',"KID":' + self.__kingdomID +
                            '}')
        # @formatter:on

        processor.sendMessage(msg)

        response = processor.q_sti.get(True)
        _log("STI response: " + response)
        decoded = decode2(response)
        # pretty_print(decoded)
        self.result = decoded


class RepairBuilding(Command):
    def __init__(self, oid, power=0):
        Command.__init__(self)
        self.__oid = str(oid)
        self.__power = str(power)
        self.result = None

    def execute(self, processor):
        info("rbu - Repair building")
        # %xt%EmpirefourkingdomsExGG_4%rbu%1%{"OID":161,"PWR":0}%
        # %xt%EmpirefourkingdomsExGG_4%rbu%1%{"PWR":0,"OID":190}%
        msg = formatMessage('rbu%1%{"OID":' + self.__oid + ',"PWD":' + self.__power + '}')
        processor.sendMessage(msg)
        response = processor.q_rbu.get(True)
        rc = getError(response)
        if rc == 0:
            decoded = decode2(response)
            self.result = decoded
        else:
            info("RBU - RC {:d}".format(rc))


class LeaveAlliance(Command):
    def __init__(self):
        Command.__init__(self)
        self.result = None

    def execute(self, processor):
        info("AQI - Leave Alliance")
        # %xt%EmpirefourkingdomsExGG_4%aqi%1%{}%
        msg = formatMessage('aqi%1%{}')
        processor.sendMessage(msg)
        response = processor.q_aqi.get(True)
        rc = getError(response)
        if rc == 0:
            decoded = decode2(response)
            self.result = decoded
        else:
            info("AQI - RC {:d}".format(rc))


class ApplyToAlliance(Command):
    def __init__(self, allianceID, applyMessage="Get me in"):
        Command.__init__(self)
        self._allianceID = str(allianceID)
        self._applyMessage = applyMessage
        self.result = None

    def execute(self, processor):
        info("SAA - Apply To Alliance")
        # %xt%EmpirefourkingdomsExGG_4%saa%1%{"AT":"get me in","AID":5738}%
        msg = formatMessage('saa%1%{"AT":"' + self._applyMessage + '", "AID":' + self._allianceID + '}')
        processor.sendMessage(msg)
        # TODO i'm not sure the response comes through this
        response = processor.q_saa.get(True)
        rc = getError(response)
        if rc == 0:
            decoded = decode2(response)
            self.result = decoded
        else:
            info("SAA - RC {:d}".format(rc))


class GetEconomy(Command):
    def __init__(self, playerID):
        Command.__init__(self)
        self.playerID = str(playerID)
        self.result = None

    def execute(self, processor):
        info("DCL - Get Economy")

        # TODO parse glk as well for KTs ... also parse them in GBD
        processor.sendMessage(formatMessage('dcl%1%{' + '"CD":' + self.playerID + '}'))
        response = processor.q_dcl.get(True)
        _log("DCL response: " + response)
        decoded = decode2(response)
        # pretty_print(decoded['C'])
        dcl = parse_dcl_response(decoded['C'])
        getPlayer().setEconomicData(dcl)
        self.result = dcl


def parse_dcl_response(kingdoms):
    castles = {}
    for kingdom in kingdoms:
        for castle in kingdom['AI']:
            castleId, economyData = parse_castle_economy(castle)
            castles[castleId] = economyData

    return castles


def parse_castle_economy(castle):
    economicData = {}
    ac = castle['AC']
    for item in ac:
        if LOG_TOOLS_TROOPS_BUILDING_IDS:
            _log("Troop or Tool ID {} count {} name {}".format(str(item[0]).rjust(3, ' '), str(item[1]).rjust(3, ' '), tools_and_troops_to_string(item[0])))
        economicData['tool' + str(item[0])] = item[1]  # use 'tool' for troop and tools doesn't matter

    castleId = castle['AID']

    economicData['food'] = int(castle['F'])
    economicData['stone'] = int(castle['S'])
    economicData['wood'] = int(castle['W'])
    economicData['coal'] = int(castle['C'])
    economicData['oil'] = int(castle['O'])
    economicData['glass'] = int(castle['G'])
    economicData['iron'] = int(castle['I'])

    economicData['foodProduction'] = math.floor(castle['gpa']['DF'] / 10)
    economicData['foodConsumption'] = math.floor(castle['gpa']['DFC'] / 10)
    economicData['stoneProduction'] = math.floor(castle['gpa']['DS'] / 10)
    economicData['woodProduction'] = math.floor(castle['gpa']['DW'] / 10)

    economicData['coalProduction'] = math.floor(castle['gpa']['DC'] / 10)
    economicData['oilProduction'] = math.floor(castle['gpa']['DO'] / 10)
    economicData['glassProduction'] = math.floor(castle['gpa']['DG'] / 10)
    economicData['ironProduction'] = math.floor(castle['gpa']['DI'] / 10)

    return castleId, economicData


class SendResources2(Command):
    def __init__(self, kingdomID, srcID, destX, destY, food, wood, stone, iron, coal, oil, glass, speed=-1):
        Command.__init__(self)
        self.kingdomID = str(kingdomID)
        self.srcID = str(srcID)
        self.destX = str(destX)
        self.destY = str(destY)
        self.food = str(food)
        self.wood = str(wood)
        self.stone = str(stone)
        self.iron = str(iron)
        self.coal = str(coal)
        self.oil = str(oil)
        self.glass = str(glass)
        self.speed = str(speed)

        rssPresent = (food > 0 or wood > 0 or stone > 0)
        kingdomRssPresent = (iron > 0 or coal > 0 or oil > 0 or glass > 0)
        if rssPresent and kingdomRssPresent:
            raise Exception("Cannot send normal and kingdom rss in a single trip")
        if not rssPresent and not kingdomRssPresent:
            raise Exception("No rss type specified")

    def execute(self, processor):
        info("CRM - Send Barrows")
        # info("Sending: food={}, wood={}, stone={}, iron={}, coal={}, oil={}, glass={} at speed={}".format(
        #     self.food, self.wood, self.stone, self.iron, self.coal, self.oil, self.glass, self.speed))

        # This is the sequence sent each time you transfer
        # %xt%EmpirefourkingdomsExGG_4%cmi%1%{"S":0,"KID":2}%
        # %xt%EmpirefourkingdomsExGG_4%dcl%1%{"CD":1}%
        # %xt%EmpirefourkingdomsExGG_4%dcl%1%{"CD":1}%
        # %xt%EmpirefourkingdomsExGG_4%crm%1%{"TX":866,"G":[["W",0],["S",0],["F",12650]],"SID":2596159,"KID":2,
        # "HBW":1007,"TY":587,"goods":[["W",0],["S",0],["F",12650]],"kingdomID":2,"castleID":2596159}%

        processor.sendMessage(formatMessage('cmi%1%{' + '"S":0' + ',' + '"KID":' + self.kingdomID + '}'))
        processor.q_cmi.get(True)
        processor.sendMessage(formatMessage('dcl%1%{' + '"CD":1' + '}'))
        processor.q_dcl.get(True)
        processor.sendMessage(formatMessage('dcl%1%{' + '"CD":1' + '}'))
        processor.q_dcl.get(True)

        # req  %xt%EmpirefourkingdomsExGG_4%crm%1%{"TX":1155,"TY":424,"SID":1363756,"KID":0,"G":[["W",378],["S",0],["F",0]],"HBW":-1}%"
        # "HBW" serves for the coin/ruby speed boost: -1 = none
        # Starting from foreign castle upgrade they added: goods, castleID, kingdomID (basically 2 redundant messages in 1)

        # resp Omitted it is 4k long see: crm_response_snippet_(send_resources).json
        if int(self.wood) > 0 or int(self.stone) > 0 or int(self.food) > 0:
            processor.sendMessage(formatMessage('crm%1%{"TX":' + self.destX + ',"HBW":' + self.speed + ',"SID":' + self.srcID + ',"TY":' + self.destY +
                                                ',"G":[["W",' + self.wood + '],["S",' + self.stone + '],["F",' + self.food + ']]' + ',"KID":' + self.kingdomID +
                                                ',"goods":[["W",' + self.wood + '],["S",' + self.stone + '],["F",' + self.food + ']]' +
                                                ',"kingdomID":' + self.kingdomID + ',"castleID":' + self.srcID + '}'))
        elif int(self.iron) > 0 or int(self.coal) > 0 or int(self.oil) > 0 or int(self.glass) > 0:
            # %xt%EmpirefourkingdomsExGG_4%crm%1%{"TY":723,"KID":3,"G":[["C",3192],["O",3468],["G",3582],["I",3728]],"TX":529,"HBW":1007,"SID":3634935,"kingdomID":3,
            # "goods":[["C",3192],["O",3468],["G",3582],["I",3728]],"castleID":3634935}%.
            processor.sendMessage(formatMessage('crm%1%{' + '"TY":' + self.destY + ',' + '"KID":' + self.kingdomID + ',' +
                                                '"G":[["C",' + self.coal + '],["O",' + self.oil + '],["G",' + self.glass + '],["I",' + self.iron + ']]' + ',' +
                                                '"TX":' + self.destX + ',' + '"HBW":' + self.speed + ',' + '"SID":' + self.srcID + ',' +
                                                '"kingdomID":' + self.kingdomID + ',' +
                                                '"goods":[["C",' + self.coal + '],["O",' + self.oil + '],["G",' + self.glass + '],["I",' + self.iron + ']]' + ',' +
                                                '"castleID":' + self.srcID + '}'))

        response = processor.q_crm.get(True)
        _log("CRM response: " + response)
        rc = getError(response)
        if rc != 0:
            error("ERROR CODE " + str(rc))
            if rc == 109:
                error("QUANTITY SPECIFIED IS PROBABLY MORE THAN BARROW MAX! Check the barrow limit for this source!")
            return

        decoded = decode2(response)
        if decoded is None:
            error("FAILED to SEND RSS from {} in kingdom {}".format(self.srcID, kingdom_to_string(self.kingdomID)))



class GetRankings(Command):
    """
    Open Rankings dialog dispatches this
    %xt%EmpirefourkingdomsExGG_4%hgh%1%{"LT":5,"SV":"-1","LID":1}%

    Sometimes it is "LT":6

    Search for target player by name
    %xt%EmpirefourkingdomsExGG_4%hgh%1%{"LT":5,"SV":"newport","LID":6}%

    Response:
    """

    def __init__(self, targetPlayerName="-1"):
        Command.__init__(self)
        # "-1" is used to display the default rankings in the game
        self._targetPlayerName = targetPlayerName
        self.result = None

    def execute(self, processor):
        info("HGH - Player Rankings Info")
        # I had 5 in my trace, might always be different or depend on commander or whatever
        if isinstance(self._targetPlayerName, unicode):
            # Supports unicode player names
            processor.sendMessage((u"%xt%EmpirefourkingdomsExGG_4%" + u'hgh%1%{"LT":5,"SV":"').encode('utf-8') +
                                  self._targetPlayerName.encode('utf-8') + (u'","LID":1' + u'}' + u"%\0").encode('utf-8'))
        else:
            processor.sendMessage(formatMessage('hgh%1%{"LT":' + str(5) + ',"SV":"' + self._targetPlayerName + '","LID":1' + '}'))
        response = processor.q_hgh.get(True)
        _log("HGH response: " + response)

        if getError(response) == 21:
            _log("PLAYER NOT FOUND: " + self._targetPlayerName)
        else:
            decoded = decode2(response)
            # pretty_print(decoded)
            self.result = decoded


class GetSamuraiEventRankings(Command):
    """
    Open Rankings dialog dispatches this
    %xt%EmpirefourkingdomsExGG_4%hgh%1%{"LT":500,"LID":1,"SV":"-1"}%
    Scrolling down the pages dispatches
    %xt%EmpirefourkingdomsExGG_4%hgh%1%{"LT":500,"LID":7,"SV":"1"}%
    Response:
    """

    def __init__(self, LID=1, targetPlayerName="-1"):
        Command.__init__(self)
        # "1" is used to display the default rankings in the event
        self._LID = str(LID)
        # "-1" is used to display the default rankings in the event
        self._targetPlayerName = targetPlayerName
        self.result = None
        self.resultLID = None

    def execute(self, processor):
        info("HGH - Player Rankings Info")
        # I had 500 in my trace, might always be different, not sure where this value comes from!!!
        if isinstance(self._targetPlayerName, unicode):
            # Supports unicode player names
            processor.sendMessage(u'%xt%EmpirefourkingdomsExGG_4%hgh%1%{'.encode('utf-8') +
                                  u'"LT":500'.encode('utf-8') +
                                  u',"LID":'.encode('utf-8') + self._LID.encode('utf-8') +
                                  u',"SV":"'.encode('utf-8') + self._targetPlayerName.encode('utf-8') + u'"'.encode('utf-8') +
                                  u'}'.encode('utf-8') +
                                  u"%\0".encode('utf-8'))
        else:
            processor.sendMessage(formatMessage('hgh%1%{' +
                                                '"LT":' + str(500) + ','+
                                                '"LID":' + self._LID +','+
                                                '"SV":"' + self._targetPlayerName + '"'
                                                + '}'))
        response = processor.q_hgh.get(True)
        _log("HGH response: " + response)

        if getError(response) == 21:
            _log("PLAYER NOT FOUND: " + self._targetPlayerName)
        else:
            decoded = decode2(response)
            # pretty_print(decoded)
            self.result = decoded
            self.resultLID = self.result["LID"]


class GetForeignLegionEventRankings(Command):
    """
    %xt%EmpirefourkingdomsExGG_4%pep%1%{"EID":71}% I think this is get personal event info
    %xt%EmpirefourkingdomsExGG_4%hgh%1%{"SV":"-1","LT":44,"LID":1}% This is player
    %xt%EmpirefourkingdomsExGG_4%pep%1%{"EID":71}%
    %xt%EmpirefourkingdomsExGG_4%hgh%1%{"SV":"-1","LT":45,"LID":1}% This is alliance
    """

    def __init__(self, LID=1, targetPlayerName="-1"):
        Command.__init__(self)
        # "1" is used to display the default rankings in the event
        self._LID = str(LID)
        # "-1" is used to display the default rankings in the event
        self._targetPlayerName = targetPlayerName
        self.result = None
        self.resultLID = None

    def execute(self, processor):
        info("HGH - Player Rankings Info")
        # I had 500 in my trace, might always be different, not sure where this value comes from!!!
        if isinstance(self._targetPlayerName, unicode):
            # Supports unicode player names
            processor.sendMessage(u'%xt%EmpirefourkingdomsExGG_4%hgh%1%{'.encode('utf-8') +
                                  u'"LT":44'.encode('utf-8') +
                                  u',"LID":'.encode('utf-8') + self._LID.encode('utf-8') +
                                  u',"SV":"'.encode('utf-8') + self._targetPlayerName.encode('utf-8') + u'"'.encode('utf-8') +
                                  u'}'.encode('utf-8') +
                                  u"%\0".encode('utf-8'))
        else:
            processor.sendMessage(formatMessage('hgh%1%{' +
                                                '"LT":' + str(44) + ','+
                                                '"LID":' + self._LID +','+
                                                '"SV":"' + self._targetPlayerName + '"'
                                                + '}'))
        response = processor.q_hgh.get(True)
        _log("HGH response: " + response)

        if getError(response) == 21:
            _log("PLAYER NOT FOUND: " + self._targetPlayerName)
        else:
            decoded = decode2(response)
            # pretty_print(decoded)
            self.result = decoded
            self.resultLID = self.result["LID"]


#
# This is the same message type as get player ranking but the payload is different
#
class GetAllianceID(Command):
    def __init__(self, allianceName):
        Command.__init__(self)
        self.__allianceName = allianceName
        self.result = None

    def execute(self, processor):
        # TODO unicode support like in player ranking
        info("HGH - Alliance ID")
        # %xt%EmpirefourkingdomsExGG_4%hgh%1%{"SV":"Minions","LID":1,"LT":10}%

        # Sometimes it is "LT":11
        processor.sendMessage(formatMessage('hgh%1%{"SV":"' + self.__allianceName + '"' + ',"LID":1' + ',"LT":10}'))
        response = processor.q_hgh.get(True)

        rc = getError(response)
        if rc != 0:
            error("FAILED to lookup alliance, ERROR CODE " + str(rc))
        else:
            decoded = decode2(response)
            self.result = decoded


class GetAlliancePlayers(Command):
    def __init__(self, allianceID):
        Command.__init__(self)
        self.__allianceID = str(allianceID)
        self.result = None

    def execute(self, processor):
        info("AIN - Alliance Players")

        try:  # Can be empty or return residual information from when we logged in
            processor.q_ain.get_nowait()
        except Empty:
            pass

        # %xt%EmpirefourkingdomsExGG_4%ain%1%{"AID":'43332'}%
        processor.sendMessage(formatMessage('ain%1%{"AID":' + self.__allianceID + '}'))
        response = processor.q_ain.get(True)

        rc = getError(response)
        if rc != 0:
            error("FAILED to lookup alliance players, ERROR CODE " + str(rc))
        else:
            decoded = decode2(response)
            self.result = decoded


class DailyBonusCommand(Command):
    """
    Bonus item index position (basically a 0 based array).
    0,1,2
    3,4,5
    6,7,8
    """

    def __init__(self, index):
        Command.__init__(self)
        if index < 0 or index > 8:
            raise ValueError("index should be [0-8]")
        self.__index = str(index)

    def execute(self, processor):
        info("CLB - Daily Bonus")
        # %xt%EmpirefourkingdomsExGG_4%clb%1%{"I":1}%
        processor.sendMessage(formatMessage('clb%1%{"I":' + self.__index + '}'))
        response = processor.q_clb.get(True)

        rc = getError(response)
        if rc != 0:
            error("FAILED to get daily Bonus, ERROR CODE " + str(rc))


class AttackCommand(Command):
    def __init__(self, kingdomID, attack, srcX, srcY, destX, destY, commanderID, speed=-1, nomadOrBerimondTower=False):
        Command.__init__(self)
        self._kingdomID = kingdomID
        self._attack = attack
        self._srcX = srcX
        self._srcY = srcY
        self._destX = destX
        self._destY = destY
        self._commanderID = commanderID
        self._speed = speed
        self._nomadOrBerimondTower = nomadOrBerimondTower

    def execute(self, processor):
        info("CRA - Attack")
        # "TX":108,
        # "AV":0,
        # "A":[{"L":{"U":[[636,64]],"T":[[614,2],[620,24]]},"R":{"U":[[636,51],[664,13]],"T":[[614,2],[620,34]]},
        #       "M":{"U":[[636,153],[6,39]],"T":[[614,2],[611,13],[620,34]]}},{"L":{"U":[[636,64]],"T":[]},
        #       "R":{"U":[[636,64]],"T":[]},"M":{"U":[[726,30],[75,50]],"T":[]}},{"L":{"U":[[636,64]],"T":[]},"R":{"U":[],"T":[]},"M":{"U":[[636,180]],"T":[]}}],
        # "TY":1012,
        # "LP":0,
        # "BPC":0,
        # "CD":65, <<<< only present for nomads (and berimond)
        # "KID":0,
        # "LID":6,
        # "HBW":1007,
        # "FC":0,
        # "ATT":0,
        # "SX":115,
        # "SY":1033

        # @formatter:off
        message = 'cra%1%{' + \
                  '"TX":' + str(self._destX) + ',' + \
                  '"AV":' + '0' + ',' + \
                  '"A":' + self._attack + "," + \
                  '"TY":' + str(self._destY) + ',' + \
                  '"LP":' + '0' + ',' \
                  '"BPC":' + '0' + ','
        if self._nomadOrBerimondTower:
            message += '"CD":65,'

        message += '"KID":' + str(self._kingdomID) + ',' + \
                   '"LID":' + str(self._commanderID) + ',' + \
                   '"HBW":' + str(self._speed) + ',' + \
                   '"FC":' + '0' + ',' + \
                   '"ATT":' + '0' + ',' + \
                   '"SX":' + str(self._srcX) + ',' + \
                   '"SY":' + str(self._srcY) + \
                   '}'

        msg = formatMessage(message)  # TODO one of these might be: show to alliance, when in context of an attack on a player
        # @formatter:on

        _log(">>>> CRA attack " + msg)
        processor.sendMessage(msg)
        response = processor.q_cra.get(True)
        _log("CRA response: " + response)

        rc = getError(response)
        if rc != 0:
            # CODE 313 Invalid attack: Invalid troop/tool count, ie: too many troops or tools in one wave on any wall or sent
            # defensive tools on an attack
            error("ERROR CODE " + str(rc))

            if rc == 5:
                error("Speed is probably wrong (stables might not be at the expected level)")
            if rc == 95:
                error("Cannot attack castle (probably burning)")
            if rc == 101:
                error("Not enough troops or tools")
            if rc == 256:
                error("Commander not available")
            if rc == 313:
                error("Invalid formation")
            return

        # CRA response' "AMM" element is the same as objects found in the 'M' array of a "
        # " incoming message.
        # Need to create an 'M' element, make it an array, and put the AAM object's value as only element in it
        decoded = decode2(response)
        try:
            if 'AAM' in decoded:
                # pretty_print(getMovements(), "(.BEFORE.)")
                decoded['M'] = []
                decoded['M'].append(decoded['AAM'])
                getMovements().append(decoded)
                # TODO THIS IS DEBUG to remove once validated that it is correct
                # pretty_print(getMovements(), "(.AFTER.)")
            else:
                error("++++++++++++++++++++++++ 'AAM' NOT FOUND")
        except:
            error("Error parsing CRA response")


# In order for this to buy in the right castle you must jump to it first (it is not part of this command)
class BuyToolsFromArmorer(Command):
    """
    kid: Kingdom id
    toolType: Tool type id
    toolCount: [1,100]
    """

    def __init__(self, kid, toolTypeID, toolCount=100):
        Command.__init__(self)
        if toolCount < 1 or toolCount > 100:
            raise ValueError("toolCount should be [1-100]")
        self.__kid = str(kid)
        self.__toolTypeID = str(toolTypeID)
        self.__toolCount = str(toolCount)
        # 28 is ladders
        # 32 is either wood mantle or ram
        # 36 is either wood mantle or ram

    def execute(self, processor):
        info("SBP - Buy Tools From Armorer")
        # %xt%EmpirefourkingdomsExGG_4%sbp%1%{"PC2":-1,"A":100,"TID":27,"AID":-1,"KID":0,"VP":-1,"BT":0,"PID":28}%
        processor.sendMessage(formatMessage('sbp%1%{"PC2":-1,'
                                            '"AMT":' + self.__toolCount + ',"TID":27' +  # Cannot explain why TID is 27 but it always was
                                            ',"AID":-1,' + '"KID":' + self.__kid + ',"VP":-1,"BT":0,' + '"PID":' + self.__toolTypeID + '}'))
        response = processor.q_sbp.get(True)
        decoded = decode2(response)
        rc = getError(response)
        if rc != 0:
            error("FAILED to buy tools from armorer, ERROR CODE " + str(rc))
            raise Exception("FAILED to buy tools from armorer, ERROR CODE " + str(rc))

        updateCoins(decoded['gcu']['C1'], decoded['gcu']['C2'])
        return decoded['gcu']['C1']


class ApplyTimeBoost(Command):
    def __init__(self, destX, destY, kingdomID, boostType):
        """MS6: 24h, MS5: 5h, MS4: 1h, MS3: 30m, MS2: 5m, MS1: 1m"""
        Command.__init__(self)
        self._destX = destX
        self._destY = destY
        self._kid = kingdomID
        self._boostType = boostType
        self.result = None
        self.tower = None

    @staticmethod
    def printableBoostName(value):
        if value == TIME_BOOST_TYPE_24H:
            return '24h'
        if value == TIME_BOOST_TYPE_5H:
            return '5h'
        if value == TIME_BOOST_TYPE_1H:
            return '1h'
        if value == TIME_BOOST_TYPE_30M:
            return '30m'
        if value == TIME_BOOST_TYPE_10M:
            return '10m'
        if value == TIME_BOOST_TYPE_5M:
            return '5m'
        if value == TIME_BOOST_TYPE_1M:
            return '1m'
        return "UNKNOWN TIME SKIP"

    def execute(self, processor):
        info("MSD - Time skip {}".format(ApplyTimeBoost.printableBoostName(self._boostType)))
        # %xt%EmpirefourkingdomsExGG_4%msd%1%{"Y":777,"MST":"MS5","KID":"0","X":98}%
        processor.sendMessage(formatMessage('msd%1%{'+
                                            '"Y":' + str(self._destY) +
                                            ',"MST":"' + str(self._boostType) + '"'
                                            ',"KID":"' + str(self._kid) + '"'
                                            ',"X":' + str(self._destX) + '}'))
        response = processor.q_msd.get(True)
        rc = getError(response)
        if rc == 0:
            decoded = decode2(response)
            self.result = decoded
            if 'msc' in decoded and 'MS' in decoded['msc']:
                getPlayer().timeSkips = decoded['msc']['MS']
            if 'AI' in decoded:
                self.tower = decoded['AI']


class GetGemsInfo(Command):

    def __init__(self):
        Command.__init__(self)
        self.result = None

    def execute(self, processor):
        info("GGM - Get Gems Info")
        processor.sendMessage(formatMessage('ggm%1%{}'))
        response = processor.q_ggm.get(True)
        decoded = decode2(response)
        self.result = decoded

        _log("------------------------------------------ " + 'GEMS' + " - START ------------------------------------------")
        pretty_print(decoded, "GEMS\n")
        _log("------------------------------------------ " + 'GEMS' + " - END   ------------------------------------------")


class GetCommandersAndCastellansInfo(Command):

    def __init__(self):
        Command.__init__(self)
        self.result = None

    def execute(self, processor):
        info("GLI - Get Commanders and Castellans Info")
        processor.sendMessage(formatMessage('gli%1%{}'))
        response = processor.q_gli.get(True)
        decoded = decode2(response)
        self.result = decoded

        _log("------------------------------------------ " + 'COMS & CASTS' + " - START ------------------------------------------")
        pretty_print(decoded, "COMS & CASTS\n")
        _log("------------------------------------------ " + 'COMS & CASTS' + " - END   ------------------------------------------")


class GetEquipmentInfo(Command):

    def __init__(self):
        Command.__init__(self)
        self.result = None
        self.equipment = None

    def execute(self, processor):
        info("GEI - Get equipment Info")
        processor.sendMessage(formatMessage('gei%1%{}'))
        response = processor.q_gei.get(True)
        decoded = decode2(response)
        self.result = decoded
        self.equipment = GetEquipmentInfo.parse_gei_response(decoded)

        _log("------------------------------------------ " + 'EQUIPMENT' + " - START ------------------------------------------")
        pretty_print(decoded, "EQUIPMENT\n")
        _log("------------------------------------------ " + 'EQUIPMENT' + " - END   ------------------------------------------")


# TODO do we need to be in main castle before calling this? Should probably just to avoid suspicion
class JumpToBladeCoast(Command):
    """
    """

    def __init__(self, mid):
        Command.__init__(self)
        self.__mid = mid
        self.result = None
        self.buildings = None

    def execute(self, processor):
        info("JEI - Get Blade Coast Info")
        # %xt%EmpirefourkingdomsExGG_4%jea%1%{"MID":22}%
        processor.sendMessage(formatMessage('jea%1%{' + '"MID":' + str(self.__mid) + '}'))
        response = processor.q_jaa.get(True)
        decoded = decode2(response)
        # Produces a lot of output!
        # pretty_print(decoded, "JCA response\n")

        _log("------------------------------------------ " + 'BLADE COAST' + " - START ------------------------------------------")
        self.result, self.buildings = self.parse_jaa_response(decoded)
        _log("------------------------------------------ " + 'BLADE COAST' + " - END   ------------------------------------------")
        # getPlayer().getCastleById(decoded['gca']['A'][3]).setBuildings(buildings)

    @staticmethod
    def parse_jaa_response(decoded):
        """
        Private implementation because there are many keys not present in the response for Blade Coast
        """
        playerData = {}

        playerData['food'] = int(decoded['grc']['F'])
        playerData['stone'] = int(decoded['grc']['S'])
        playerData['wood'] = int(decoded['grc']['W'])
        playerData['coal'] = int(decoded['grc']['C'])
        playerData['oil'] = int(decoded['grc']['O'])
        playerData['glass'] = int(decoded['grc']['G'])
        playerData['iron'] = int(decoded['grc']['I'])

        # float values with 1 decimal encoded as an ints
        playerData['foodProduction'] = math.floor(decoded['gpa']['DF'] / 10)
        playerData['foodConsumption'] = math.floor(decoded['gpa']['DFC'] / 10)
        playerData['stoneProduction'] = math.floor(decoded['gpa']['DS'] / 10)
        playerData['woodProduction'] = math.floor(decoded['gpa']['DW'] / 10)

        playerData['coalProduction'] = math.floor(decoded['gpa']['DC'] / 10)
        playerData['oilProduction'] = math.floor(decoded['gpa']['DO'] / 10)
        playerData['glassProduction'] = math.floor(decoded['gpa']['DG'] / 10)
        playerData['ironProduction'] = math.floor(decoded['gpa']['DI'] / 10)

        # Copy & remove known
        d2 = copy.deepcopy(decoded['gpa'])
        del d2['DF']
        del d2['DFC']
        del d2['DS']
        del d2['DW']
        del d2['DC']
        del d2['DO']
        del d2['DG']
        del d2['DI']
        playerData['gpa'] = d2

        playerData['aid'] = decoded['grc']['AID']
        allBuildings = decoded['gca']['BD']

        if LOG_TOOLS_TROOPS_BUILDING_IDS:
            for building in decoded['gca']['BD']:
                _log("BUILDING DETAILS type {}, id {}, coords[{}, {}], unknown1 {}, construction elapsed time {}, unknown3 {}, "
                     "damage {}%, unknown4 {}, efficiency {}%, unknown5 {}, unknown6 {}, unknown7 {}, PO {}".
                     format(building_to_string(building[0]).ljust(29, ' '), str(building[1]), str(building[2]),
                            str(building[3]),str(building[4]), str(building[5]), str(building[6]), str(100 - building[7]), str(building[8]),
                            str(building[9]), str(building[10]), str(building[11]), (building[12]), str(building[13])))

        info("Totals     [food={:d}, wood={:d}, stone={:d}, iron={:d}, glass={:d}, oil={:d}, coal={:d}]".format(playerData['food'], playerData['wood'],
                                                                                                                playerData['stone'], playerData['iron'],
                                                                                                                playerData['glass'], playerData['oil'], playerData['coal']))
        info("Production [food={:n}, wood={:n}, stone={:n}, iron={:n}, glass={:n}, oil={:n}, coal={:n}]".format(playerData['foodProduction'], playerData['woodProduction'],
                                                                                                                playerData['stoneProduction'], playerData['ironProduction'],
                                                                                                                playerData['glassProduction'], playerData['oilProduction'],
                                                                                                                playerData['coalProduction']))
        info("Consumption[food={:n}, net food={:n}]".format(playerData['foodConsumption'], playerData['foodProduction'] - playerData['foodConsumption']))
        return playerData, allBuildings


class GetBladeCoastInfo(Command):
    """
    """

    def __init__(self, mid, aid):
        Command.__init__(self)
        self.__mid = mid
        self.__aid = aid  # This comes from the JAA returned in response to the JEI sent when going to blade coast
        self.resultSJE = None
        self.resultGRC = None


    def execute(self, processor):
        info("TMP - Get Blade Coast Info")
        # %xt%EmpirefourkingdomsExGG_4%tmp%1%{"MID":22}%
        processor.sendMessage(formatMessage('tmp%1%{{"MID":{:d}}}'.format(self.__mid)))
        response = processor.q_tmp.get(True)
        rc = getError(response)
        if rc != 0:
            raise Exception("FAILED to get Blade Coast info, ERROR CODE " + str(rc))
        else:
            decoded = decode2(response)
            pretty_print(decoded, "%tmp%")
            self.resultSJE = decoded

        # There is no response to this (none that I have identified)
        # %xt%EmpirefourkingdomsExGG_4%sje%1%{"MID":22}%
        processor.sendMessage(formatMessage('sje%1%{{"MID":{:d}}}'.format(self.__mid)))

        # %xt%EmpirefourkingdomsExGG_4%grc%1%{"AID":-24,"MID":22,"KID":-1}%
        # %xt%grc%1%0%{"AID":-24,"W":10210.0,"S":8860.0,"F":17954.576,"C":0.0,"O":0.0,"G":0.0,"I":0.0,"KID":-1}%
        processor.sendMessage(formatMessage('grc%1%{{"AID":{:d},"MID":{:d},"KID":-1}}'.format(self.__aid, self.__mid)))
        response3 = processor.q_grc.get(True)
        rc = getError(response3)
        if rc != 0:
            raise Exception("FAILED to get Blade Coast info, ERROR CODE " + str(rc))
        else:
            decoded3 = decode2(response3)
            self.resultGRC = decoded3


class GetBladeInfoTargetData(Command):
    """
    """

    def __init__(self, mid, nid):
        Command.__init__(self)
        self.__mid = mid
        self.__nid = nid

    def execute(self, processor):
        info("TAI - Get Blade Coast Target Data")
        # %xt%EmpirefourkingdomsExGG_4%tai%1%{"MID":22,"NID":173}%
        processor.sendMessage(formatMessage('tai%1%{{"MID":{:d},"NID":{:d}}}'.format(self.__mid, self.__nid)))
        response = processor.q_tai.get(True)
        rc = getError(response)
        if rc != 0:
            raise Exception("FAILED to get Blade Coast Target info, ERROR CODE " + str(rc))
        else:
            decoded = decode2(response)


class AttackBladeCoast(Command):
    """
    """

    def __init__(self, mid, nid, attackFormation):
        Command.__init__(self)
        self.__mid = mid
        self.__nid = nid
        self.__attackFormation = attackFormation

    def execute(self, processor):
        info("THM - Attack Blade Coast")
        # %xt%EmpirefourkingdomsExGG_4%thm%1%{"BT":0,"A":[{"L":{"U":[[685,7]],"T":[]},"R":{"U":[[685,7]],"T":[]},"M":{"U":[[685,19]],"T":[]}}],
        # "BPC":0,"MID":22,"LID":0,"NID":167}%

        processor.sendMessage(formatMessage(('thm%1%{{"BT":0,"A": ' + self.__attackFormation + ',"BPC":0,"MID":{:d},"LID":0,"NID":{:d}}}').format(self.__mid, self.__nid)))
        response = processor.q_thm.get(True)
        rc = getError(response)
        if rc != 0:
            raise Exception("FAILED to attack Blade Coast, ERROR CODE " + str(rc))
        else:
            decoded = decode2(response)
