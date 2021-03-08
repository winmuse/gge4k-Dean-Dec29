import configparser
import os
import pprint
import random
import threading
import time
from time import localtime, strftime
import datetime
import json
import logging
import traceback
import sys
import math

INI_FILE_KEY_USERNAME = 'Auth.username'
INI_FILE_KEY_PASSWORD = 'Auth.password'
INI_FILE_KEY_SRV_HOST = 'Server.host'
INI_FILE_KEY_SRV_PORT = 'Server.port'
INI_FILE_KEY_DEVICE_ID = 'Auth.device_id'
INI_FILE_KEY_GAME_VERSION = 'Game.version'
INI_FILE_KEY_LOG_TO_FILE = 'Log.to_file'
INI_FILE_KEY_INFO_LOG_TO_CONSOLE = 'Log.info_to_console'

def readConfig(configFile):
    if not os.path.exists(configFile):
        raise IOError("Ini file does not exist " + os.path.abspath(configFile))
    if not os.path.isfile(configFile):
        raise IOError("Ini file specified is NOT a file " + os.path.abspath(configFile))
    config = configparser.ConfigParser()
    config.read(configFile)
    return _readConfig(config)


def _readConfig(config):
    configOpts = {}
    for section in config.sections():
        configOpts = dict(list(configOpts.items()) + list(_configSectionMap(config, section).items()))
        # configOpts = dict(configOpts.items() + _configSectionMap(config, section).items()) # python 2
    return configOpts


def _configSectionMap(config, section):
    options = config.options(section)
    dict1 = {}
    for option in options:
        key = section + '.' + option
        try:
            dict1[key] = config.get(section, option)
            if dict1[key] == -1:
                print("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[key] = None
    return dict1


def printConfig(ini):
    print ('-------------------------------------')
    print ('host=' + ini[INI_FILE_KEY_SRV_HOST])
    print ('port=' + str(ini[INI_FILE_KEY_SRV_PORT]))
    print ('username=' + ini[INI_FILE_KEY_USERNAME])
    print ('password=' + ini[INI_FILE_KEY_PASSWORD])
    print ('phoneID=' + ini[INI_FILE_KEY_DEVICE_ID])
    print ('gameVersion=' + ini[INI_FILE_KEY_GAME_VERSION])
    print ('-------------------------------------')


def sleepRandomTime(short=False):
    if short:
        v = random.random()
        if v < 0.50:
            v = 0.51
        time.sleep(v)
    else:
        time.sleep(random.randint(1, 2))


def calculateDistance(srcX, srcY, destX, destY):
    return math.sqrt((math.fabs(math.fabs(srcX) - math.fabs(destX)) ** 2) + (math.fabs(math.fabs(srcY) - math.fabs(destY)) ** 2))


def formatTimeSpan(span_in_seconds):
    hours, remainder = divmod(span_in_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return "{:0=2}:{:0=2}:{:0=2}".format(hours, minutes, seconds)


def printThreads():
    for th in threading.enumerate():
        print(th)
        try:
            traceback.print_stack(sys._current_frames()[th.ident])
        except e:
            print ('Thread removed while iterating, KeyError - reason "%s"' % str(e))
        print()


def decode2(msg):
    value = msg.split('%')[5]
    if value is not None and len(value) > 0:
        return json.loads(value)
    return None


def getError(msg):
    return int(msg.split('%')[4])


def decode(msg, prefix, terminator='%'):
    payload = msg.split(prefix, 1)[1]
    if terminator != None:
        payload = payload.split(terminator, 1)[0]
    return json.loads(payload)


DEBUG = True  # = False
logger = None


def printArgs(args):
    for arg, value in sorted(vars(args).items()):
        log("Argument {}={}".format(arg, value))


def console(msg):
    global logger
    if logger is None:
        print ("Logging NOT INITIALIZED YET defaulting to print")
        # TODO this is a temp hack since the we attempt to log before the logger is actually initialized
        print (time.strftime("%b %d %Y %H:%M:%S") + ' ' + msg)
    else:
        logger.info(msg)


def log(msg):
    if not DEBUG:
        return

    if logger is None:
        print ("Logging NOT INITIALIZED YET defaulting to print")
        # TODO this is a temp hack since the we attempt to log before the logger is actually initialized
        print (time.strftime("%b %d %Y %H:%M:%S") + ' ' + msg)
    else:
        logger.debug(msg)


def logMsgHeader(msg, data):
    if DEBUG:
        payload = data.split('%')
        if len(payload) > 5:
            header = ''.join(['%s%%' % (e) for e in payload[:5]])
            log(msg + " " + header)
        else:
            log("logMsgHeader unable to isolate header for message: " + data)


# def readConfig_(configFile):
#    config = ConfigParser.ConfigParser()
#    config.read(configFile)
#    return dict( list( configOpts.items() ) + list( configSectionMap(config, section) ) ) for section in config.sections()

def initLogging(ini):
    global logger

    if logger is not None:
        return

    if DEBUG:
        directory = 'logs'
        if not os.path.exists(directory):
            os.makedirs(directory)

        fh = None
        # File logging is enable by default and needs to be explicitly disabled
        if INI_FILE_KEY_LOG_TO_FILE not in ini or ini[INI_FILE_KEY_LOG_TO_FILE].lower() != 'false':
            filename = ini[INI_FILE_KEY_USERNAME].replace(' ', '_') + '_' + strftime("%Y-%m-%d_%H_%M_%S", localtime()) + '.log'
            # filename = os.path.join(os.ggetcwd(), directory, filename)
            fh = logging.FileHandler(filename, 'w')
            fh.setLevel(logging.DEBUG)
            fmt = logging.Formatter('%(asctime)s %(name)-12s: %(levelname)-8s %(message)s')
            fh.setFormatter(fmt)

        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        if INI_FILE_KEY_INFO_LOG_TO_CONSOLE in ini and ini[INI_FILE_KEY_INFO_LOG_TO_CONSOLE].lower() == 'false':
            ch.setLevel(logging.ERROR)
        else:
            ch.setLevel(logging.INFO)

        fmt = logging.Formatter("%(message)s")
        ch.setFormatter(fmt)

        logger = logging.getLogger()
        # Logger level takes precedence over handler level so if logger is set to CRITICAL nothing more verbose will ever make its way to the handlers
        logger.setLevel(logging.DEBUG)

        if fh is not None:
            logger.addHandler(fh)
        logger.addHandler(ch)
    else:
        logging.disable(logging.FATAL)
        logger = logging.getLogger()

    logger.debug("===Logging Initialized===")


def isNight():
    now = datetime.datetime.now()
    # night = now.hour > 1 and now.hour < 6
    night = now.hour > 2 and now.hour < 5
    return night


def isWeekend():
    now = datetime.datetime.now()
    d = now.weekday()
    return d >= 5 and d <= 6


# Helps define an Enum like class
def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)


def xstr(s):
    if s is None:
        return ''
    return str(s)

def removeAllBlanks(message):
    if message is not None:
        return message.replace(' ', '')
    return None

def encodeUnicode(possibleUnicode):
    if isinstance(possibleUnicode, unicode):
        possibleUnicode = unicode.encode(possibleUnicode, 'utf-8')
    return possibleUnicode

class UnicodeSafePrettyPrinter(pprint.PrettyPrinter):
    def pformat(self, object):
        if isinstance(object, unicode):
            return (object.encode('utf8'), True, False)
        return pprint.PrettyPrinter.pformat(self, object)

    def format(self, object, context, maxlevels, level):
        if isinstance(object, unicode):
            return (object.encode('utf8'), True, False)
        return pprint.PrettyPrinter.format(self, object, context, maxlevels, level)
