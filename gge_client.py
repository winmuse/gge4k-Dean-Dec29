#!/usr/bin/env python
# coding: latin-1
from threading import Timer
import sys
import time
import datetime
import random
import traceback
import argparse
import pprint
import json
from collections import deque

from gge_client_utils import NomadAttackFormationBuilder, BaronAttackFormationBuilder, BaronAttackFormationBuilder2
import gge_utils
from gge_utils import log, console, isNight, isWeekend, sleepRandomTime, calculateDistance, xstr, removeAllBlanks
import gge_commands
from gge_constants import *
from gge_commands import *
from gge_comm import Processor
from gge_model import has_enough_rss_to_build_tools, has_enough_coins_to_recruit_troops
from collections import OrderedDict
import gge_ice_attack_formation
import gge_sand_attack_formation
import gge_fire_attack_formation
import gge_green_attack_formation

# 10, 30, 90, 180, 360, 720, 1440 (last 2 costs rubies unless you have high premium level in which case only the last one costs rubies (or none do ... not sure about last one) )
# TODO move this to constant or commands
# Mapping time_in_minutes = value_used_in_tax_collector_message
TAX_COLLECTOR_TIMES = {10: 0, 30: 1, 90: 2, 180: 3, 360: 4, 720: 5, 1440: 6}

ALL_DEMONS = True
ELITE_KG = True

NOMAD_DEBUG = False

TARGET_TYPE_NOMAD = 1
TARGET_TYPE_RBC = 2


class Client(object):
    TROOPS_COSTING_COINS_TO_HEAL = [TROOP_TYPE_KINGSGUARD_BOW, TROOP_TYPE_KINGSGUARD_KNIGHT, TROOP_TYPE_KINGSGUARD_ROYAL_SENTINEL, TROOP_TYPE_KINGSGUARD_ROYAL_SCOUT, TROOP_TYPE_ELITE_KNIGHT, TROOP_TYPE_ELITE_CROSSBOWMAN, TROOP_TYPE_VET_SPEARMAN, TROOP_TYPE_VET_MACEMAN, TROOP_TYPE_VET_BOWMAN, TROOP_TYPE_VET_HALBERDIER, TROOP_TYPE_VET_TWO_HANDED_SWORDSMAN, TROOP_TYPE_VET_LONGBOWMAN, TROOP_TYPE_VET_HEAVY_CROSSBOWMAN, TROOP_TYPE_VET_CROSSBOWMAN, TROOP_TYPE_SWORDSMAN, TROOP_TYPE_SPEARMAN,
                                    TROOP_TYPE_MACEMAN, TROOP_TYPE_HALBERDIER, TROOP_TYPE_TWO_HANDED_SWORDSMAN, TROOP_TYPE_ARCHER, TROOP_TYPE_CROSSBOWMAN, TROOP_TYPE_BOWMAN, TROOP_TYPE_HEAVY_CROSSBOWMAN, TROOP_TYPE_LONGBOWMAN, TROOP_TYPE_IMPERIAL_GUARDSMAN, TROOP_TYPE_IMPERIAL_BOWMAN,
                                    TROOP_TYPE_SPEAR_WOMAN, TROOP_TYPE_BERSERKER]

    def __init__(self):
        # @formatter:off
        self._profile  = {'recruitTroops':        {'op': False, 'main': False, 'ice': True,  'sand': True,  'fire': False},
                          'recruitDefenseTroops': {'op': False, 'main': False, 'ice': False, 'sand': False, 'fire': False},
                          'recruitOffenseTroops': {'op': False, 'main': False, 'ice': True,  'sand': True,  'fire': False},
                          'rangeOffenseMax':      {'op': 0,     'main': 0,     'ice': 320,   'sand': 550,   'fire': 0},
                          'meleeOffenseMax':      {'op': 0,     'main': 0,     'ice': 315,   'sand': 0,     'fire': 0},
                          'rangeDefenseMax':      {'op': 0,     'main': 0,     'ice': 0,     'sand': 0,     'fire': 0},
                          'meleeDefenseMax':      {'op': 0,     'main': 0,     'ice': 0,     'sand': 0,     'fire': 0},
                          'buildTools':           {'op': False, 'main': False, 'ice': True,  'sand': True,  'fire': False} }
        # @formatter:on

        # TODO could have 1 per castle would be more generic
        self.iceToolsRotation = -1
        self.sandToolsRotation = -1
        self.fireToolsRotation = -1
        self.greenToolsRotation = -1
        self.args = None  # Command line arguments
        self.p = None
        self.t = None
        self.done = False
        self.pp = pprint.PrettyPrinter(indent=3)
        self.inCastle = False
        self._nomads = False
        self._nomadAttackRangeTroops = None
        self._nomadAttackMeleeTroops = None
        self._rbcAttackRangeTroops = None
        self._rbcAttackMeleeTroops = None

    def terminate(self):
        log("TERMINATING")
        self.done = True
        if self.t is not None:
            self.t.cancel()
        if self.p is not None:
            self.p.stop()

    def read(self):
        while not self.done:
            line = sys.stdin.readline().lower().rstrip('\n')
            if line == "exit" or line == "x" or line == "quit" or line == "q":
                break

    def startTimer(self):

        if self.args.loop is None:
            return

        if self.args.collect_tax is not None:
            tax = int(self.args.collect_tax)
            loop = int(self.args.loop)
            if loop == -1 or tax < loop:
                delay = tax
            else:
                delay = loop
        else:
            delay = int(self.args.loop)
            if delay == -1:
                delay = 10

        if delay == 1440:
            delay = random.randint(1443 * 60 + 10, 1460 * 60 + 10)
        elif delay == 720:
            delay = random.randint(722 * 60 + 10, 735 * 60 + 10)
        elif delay == 360:
            delay = random.randint(362 * 60 + 10, 370 * 60 + 10)
        elif delay == 180:
            delay = random.randint(181 * 60 + 10, 185 * 60 + 10)
        elif delay == 90:
            delay = random.randint(90 * 60 + 10, 95 * 60 + 10)
        elif delay == 30:
            delay = random.randint(30 * 60 + 10, 32 * 60 + 10)
        elif delay == 10:
            delay = random.randint(10 * 60 + 10, 11 * 60 + 5)
        else:
            delay = random.randint(delay * 60, int(delay * 60 * 1.05))

        console("Waiting for {} minutes {} seconds, next execution at {}".format(str(delay / 60), str(delay % 60), (datetime.datetime.now() + datetime.timedelta(seconds=delay)).isoformat(sep=' ')))

        self.t = Timer(delay, self.runscript)
        self.t.start()

    def resetTimer(self):
        if self.t is not None:
            self.t.cancel()
        self.startTimer()

    def runDelayed(self, cmd, short=False):
        sleepRandomTime(short)
        self.p.execute(cmd)
        return cmd

    def runNoDelay(self, cmd):
        self.p.execute(cmd)
        return cmd

    def doSendRssToOneTarget(self, src, target, rss, speed=-1):
        log("doSendRssToOneTarget IN")
        food = wood = stone = iron = coal = oil = glass = 0
        if 'stone' in rss:
            stone = rss['stone']
        if 'wood' in rss:
            wood = rss['wood']
        if 'food' in rss:
            food = rss['food']
        if 'iron' in rss:
            iron = rss['iron']
        if 'coal' in rss:
            coal = rss['coal']
        if 'oil' in rss:
            oil = rss['oil']
        if 'glass' in rss:
            glass = rss['glass']

        console('-' * 35)
        msg = "jumping to '{}'".format(src._name.encode('utf-8') if isinstance(src._name, unicode) else src._name)
        log(msg)
        console(msg)

        if src.isOp():
            cmd = JumpToOp(src.x, src.y)
        elif src.isGreenMain() or src.isIceMain() or src.isSandMain() or src.isFireMain():
            cmd = JumpToCastle(src.kingdomId, src.id)
        else:
            console("BUG unknown source castle type!!!")
            return

        self.runDelayed(cmd)
        result = cmd._result

        # print str(result)
        print ("WANNA Send: food={:d}, wood={:d}, stone={:d}, iron={:d}, coal={:d}, oil={:d}, glass={:d} at speed={:d}".format(food, wood, stone, iron, coal, oil, glass, speed))

        if food > result['food']:
            food = result['food']
            console("HAD TO CAP FOOD TO " + str(food))

        if wood > result['wood']:
            wood = result['wood']
            console("HAD TO CAP WOOD TO " + str(wood))

        if stone > result['stone']:
            stone = result['stone']
            console("HAD TO CAP STONE TO " + str(stone))

        if iron > result['iron']:
            iron = result['iron']
            console("HAD TO CAP iron TO " + str(iron))

        if coal > result['coal']:
            coal = result['coal']
            console("HAD TO CAP coal TO " + str(coal))

        if oil > result['oil']:
            oil = result['oil']
            console("HAD TO CAP oil TO " + str(oil))

        if glass > result['glass']:
            glass = result['glass']
            console("HAD TO CAP glass TO " + str(glass))

        if not (stone > 0 or wood > 0 or food > 0 or iron > 0 or coal > 0 or oil > 0 or glass> 0):
            for n in range(0, 10):
                console("You forgot to specify a quantity for source " + src.getEncodedName() + " NOT SENDING!")
            return

        if not self.areBarrowsTravelingToOrFrom(src.id, src.getEncodedName()):
            console("Sending: food={:d}, wood={:d}, stone={:d}, iron={:d}, coal={:d}, oil={:d}, glass={:d} at speed={:d}".format(food, wood, stone, iron, coal, oil, glass, speed))
            self.runDelayed(SendResources2(src._kingdomID, src._id, target['x'], target['y'], food, wood, stone, iron, coal, oil, glass, speed))
        else:
            console("NOT SENDING")
            console('-' * 35)

    def isAttackTravelingTo(self, kid, targetX, targetY):
        log("isAttackTravelingTo kid={:d} targetX={:d}, targetY={:d}: ".format(kid,targetX, targetY))

        movements = getMovements()
        for movement in movements:
            for item in movement['M']:
                # Match X & Y of the target + there is an UM key at the same level as the M key then it seems to be an army
                if 'UM' in item and str(item['M']['KID']) == str(kid) and str(item['M']['TA'][1]) == str(targetX) and str(item['M']['TA'][2]) == str(targetY):
                    log("FOUND attack travelling to {:d},{:d}".format(targetX, targetY))
                    return True

        log("NO attack travelling to kid={:d} targetX={:d}, targetY={:d}: ".format(kid,targetX, targetY))
        return False

    def areBarrowsTravelingToOrFrom(self, srcId, name):
        log("areBarrowsTravelingToOrFrom srcId: " + str(srcId) + ' (' + name + ')')

        movements = getMovements()
        for movement in movements:
            # console(pretty_print(movement))
            for item in movement['M']:
                # TODO this may break with an key does not exist if you have troops moving but no barrows as there won't be any 'M' elements under the primary 'M' element.
                # Castle() class converts id to string (srdId) that's why we have to do a string comparison here
                log(">>>> barrows SA LEN {}".format(len(item['M']['SA'])))
                log(">>>> barrows TA LEN {}".format(len(item['M']['TA'])))
                # log(">>>> barrows SA castle id is " + str(item['M']['SA'][3]))
                # log(">>>> barrows TA castle id is " + str(item['M']['TA'][3]))

                if len(item['M']['SA']) > 3:
                    log(">>>> barrows SA castle id is " + str(item['M']['SA'][3]))
                else:
                    # Army returning from Samurai (and most probably other castles)
                    for a in range(0,12):
                        log("Army returning from SAM or ???")
                    pretty_print(item['M']['SA'], ">>>> barrows SA castle id is ")
                    continue

                if str(item['M']['SA'][3]) == str(srcId):
                    # If there is an MM key at the same level as the M key then is seems to be market barrows
                    # However if it is a UM key it seems to be an army
                    if 'MM' in item and item['M']['D'] == 0: # 0 means outgoing, so source is me and is outgoing means my barrows not someone else's
                        log(">>>> barrows from " + str(srcId))
                        return True
                    else:
                        log(">>>> something traveling from this castle but i think it is an army")


                # TODO this doesn't quite work as it turns out we see all traveling barrows or other movements, not too sure
                # yet (was testing on HT), but if there is something coming at your castle (barrow or maybe even attack
                # this will mistakenly assume it is his barrow coming back) ... real solution is barrow capacity at source
                if str(item['M']['TA'][3]) == str(srcId):
                    if 'MM' in item and item['M']['D'] == 1: # 1 means returning, so target is me and is returning means my barrows not someone else's
                        log(">>>> barrows returning to " + str(srcId))
                        return True
                    else:
                        log(">>>> something traveling to this castle but i think it is an army")

        log("NO barrows travelling from/to " + str(srcId) + " it IS available to send")
        return False


    def runscript(self):
        # time.sleep(random.randint(10, 12))  # time.sleep(random.randint(25, 40))
        print ("\n" + datetime.datetime.now().strftime('%a %B %d %H:%M:%S'))
        # print '{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())

        ini = gge_utils.readConfig(self.args.inifile)
        gge_utils.initLogging(ini)
        gge_utils.printArgs(self.args)
        gge_utils.printConfig(ini)
        self.p = Processor(ini)
        try:
            self.p.start()
            self.p.execute(createLoginCommand(ini))
            self.printTimeSkipsCoinsRubies()
            self.runDelayed(JumpToCastle())
            self.inCastle = True
            self.runDelayed(GameStartCommands())

            if self.args.collect_tax is not None:
                self.processTaxes()
            if self.args.heal_troops:
                self.healTroops()
            if self.args.build_tools or self.args.recruit_troops or self.args.recruit_green:
                self.buildToolsAndRecruitTroops(self.args.build_tools, self.args.recruit_troops, self.args.recruit_green)
                # Not for now
                # if self.args.recruit_troops:
                #   self.doHelpAll()
            if self.args.buy_tools:
                self.buyToolsFromArmorer()
            if self.args.send_rss:
                print ("No longer available, see send-rss-new or use old gge_tax_collector script")

            # def printEconomy(self, printToolsTroops=True, mainOnly=False):
            if self.args.print_main_economy:
                self.printEconomy(False, True)
            elif self.args.print_economy:
                self.printEconomy(False)
            elif self.args.print_full_economy:
                self.printEconomy()

            if self.args.print_info:
                self.printCastleInfo()
                # No real use for this!
                self.printWorldInfo()

            if self.args.attack_barons:
                self.attackBarons(self.args.buy_tools_for_baron)
            elif self.args.attack_baron is not None:
                self.attackBarons(self.args.buy_tools_for_baron, self.args.attack_baron)

            if self.args.spy_barons:
                self.spyBarons()

            if self.args.send_rss_new:
                self.sendRssToPlayer()

            if self.args.help_all:
                self.doHelpAll()
            if self.args.attack_player:
                self.attackPlayer()
            if self.args.list_barons:
                self.listBarons()
            if self.args.attack_nomads:
                self.spyAndAttackNomads()
            if self.args.attack_berimond:
                self.spyAndAttackBerimond()
            if self.args.recruit_berimond:
                self.recruitTroopsInBerimond()
            if self.args.print_alliance_coordinates is not None: # Contains the name of the alliance
                self.printAllianceCoordinates(self.args.print_alliance_coordinates, self.args.include_distance_to_me, self.args.rvs_only)
            if self.args.station_troops:
                self.stationTroops()
            if self.args.print_samurai_rankings is not None:  # List of alliance names
                self.printSamuraiRankings(self.args.print_samurai_rankings)
            if self.args.farm:
                self.attackFarm()
            if self.args.print_gems:
                self.printGems()
            if self.args.blade_coast:
                self.attackInBladeCoast()
            if self.args.leave_alliance:
                self.leaveAlliance()
            if self.args.apply_alliance is not None: # List: containing alliance name to apply to
                self.applyToAlliance(self.args.apply_alliance[0])
        except KeyboardInterrupt:
            raise
        except:
            # console("Caught EXCEPTION")
            log("" + traceback.format_exc())
            # traceback.print_exc(file=sys.stderr)

        try:
            self.p.stop()
        except:
            # console("Caught exception in stop()")
            log("Caught exception in stop() " + traceback.format_exc())
            # traceback.print_exc(file=sys.stderr)

        self.p = None

        self.resetTimer()
        log("<<<< runscript() OUT")

    def printTimeSkipsCoinsRubies(self):
        # timeSkips = getPlayer().timeSkips
        # console("Time skips=[1m={:,} - 5m={:,} - 10m={:d} - 30m={:d} - 1h={:d} - 5h={:d} - 24h={:d}]".format(timeSkips[0], timeSkips[1], timeSkips[2], timeSkips[3], timeSkips[4], timeSkips[5], timeSkips[6]))
        coins, rubies = getCoins()
        console("coins={:,} - rubies={:,}".format(coins, rubies))
        console("Feast[type={}, remaining={}]".format(feast_to_string(getPlayer().getFeastType()), gge_utils.formatTimeSpan(getPlayer().getFeastTimeRemaining())))

    def stationTroops(self):
        kid = KINGDOM_GREEN
        while True:
            cname, cid = self.findFirstFreeCommander()

            if cname is not None:
                sourceX, sourceY, targetX, targetY = 1151, 421, 1153, 422
                player = getPlayer()

                sent = self.doStationTroops(kid, player.getCastle(kid), sourceX, sourceY, targetX, targetY, cid)

                if not sent:
                    break

                player = getPlayer()
                player.commanders.pop(cname, None)
                sleepRandomTime()
                sleepRandomTime()
            else:
                print ("Ran out of commanders")
                break

    # sourceX and sourceY can be different from sourceCastle's coords if you are transferring troops from
    # a KT to the main castle ... you need the sourceCastle to determine the speed of the stables
    def doStationTroops(self, kid, sourceCastle, sourceX, sourceY, targetX, targetY, cid):

        cmd = self.runDelayed(StationTroopsGetTargetInfo(kid, sourceX, sourceY, targetX, targetY))
        formation = []
        selectedTroopType = -1
        freeSlotCount = 6
        for e in cmd.result['gui']['I']:
            ttype = e[0]
            totalCount = e[1]

            # TODO pick an eligible troop type
            # TODO if this is a KT or an RV you need to validate that there are troops left
            if is_troop(ttype):
                # if is_troop_faster(ttype, selectedTroopType):
                #     selectedTroopType = ttype
                selectedTroopType = ttype
            elif is_tool(ttype):
                for i in range(0, freeSlotCount):
                    count = totalCount
                    if count > 150:
                        count = 150
                    formation.append([ttype, count])
                    freeSlotCount -= 1
                    totalCount -= count
                    if totalCount <= 0:
                        break
                if freeSlotCount == 0:
                    break

        # Only send if we have tools to transfer
        if len(formation) > 0 and selectedTroopType != -1:
            formation.insert(0, [selectedTroopType, 1])

            if len(formation) > 7:
                raise Exception("Troop/Tools slots max is 7, specified {:d} slots".format(len(formation)))

            formation = removeAllBlanks(str(formation))
            speed = sourceCastle.getMaxCoinSpeed()
            self.runDelayed(MoveTroopsToCastle(kid, formation, speed, sourceX, sourceY, targetX, targetY, cid))

            return True
        return False

    def attackFortress(self, buyTools):
        pass
        # # Vig attacking sand fortress (not that there a too many troop types in this)
        # #%xt%EmpirefourkingdomsExGG_4%abi%1%{"SY":769,"TY":750,"SX":515,"KID":1,"TX":516}%
        # #%xt%EmpirefourkingdomsExGG_4%pin%1%{}%
        # #%xt%EmpirefourkingdomsExGG_4%pin%1%{}%
        # #%xt%EmpirefourkingdomsExGG_4%cra%1%{"TX":516,"A":[{"L":{"U":[[606,1]],"T":[]},"R":{"U":[[606,1]],"T":[]},"M":{"U":[[636,139]],"T":[[620,30]]}},{"L":{"U":[[606,1]],"T":[]},"R":{"U":[[606,1]],"T":[]},"M":{"U":[[691,44],[636,95]],"T":[]}},{"L":{"U":[[606,1]],"T":[]},"R":{"U":[[606,1]],"T":[]},"M":{"U":[[630,9],[690,52],[636,32]],"T":[]}},{"L":{"U":[[636,47]],"T":[[620,20]]},"R":{"U":[[636,47]],"T":[[620,20]]},"M":{"U":[[636,139]],"T":[]}}],"BPC":0,"SX":515,"ATT":0,"SY":769,"TY":750,"FC":0,"KID":1,"LID":0,"HBW":1007,"AV":0,"LP":0}%
        # #%xt%EmpirefourkingdomsExGG_4%cra%1%{"TX":516,"A":[{"L":{"U":[[636,1]],"T":[]},"R":{"U":[[636,1]],"T":[]},"M":{"U":[[636,139]],"T":[[620,30]]}},{"L":{"U":[[636,1]],"T":[]},"R":{"U":[[636,1]],"T":[]},"M":{"U":[[636,1]],"T":[]}},{"L":{"U":[[636,1]],"T":[]},"R":{"U":[[636,1]],"T":[]},"M":{"U":[[636,139]],"T":[]}},{"L":{"U":[[636,47]],"T":[[620,20]]},"R":{"U":[[636,47]],"T":[[620,20]]},"M":{"U":[[636,139]],"T":[]}}],"BPC":0,"SX":515,"ATT":0,"SY":769,"TY":750,"FC":0,"KID":1,"LID":0,"HBW":1007,"AV":0,"LP":0}%
        #
        # player = getPlayer()
        # # North of Vig
        # endX = 516
        # endY = 750
        # # West of Vig
        # #endX = 497
        # #endY = 770
        # # West of Vig
        # #endX = 536
        # #endY = 770
        # onFire = True # This is determined via GAA i think
        #
        # if not onFire:
        #   self.runDelayed(GetFortressInfo(KINGDOM_SANDS, player._sandCastle._x, player._sandCastle._y, endX, endY))
        #   self.runDelayed(Pin())
        #   self.runDelayed(Pin())
        #   self.runDelayed(AttackCommand())

    def processTaxes(self):
        tax = self.runDelayed(TaxInfo())
        if tax.amount != 0:
            self.runDelayed(CollectTaxes())
        self.runDelayed(SendTaxCollector(TAX_COLLECTOR_TIMES[self.args.collect_tax]))
        # runDelayed(GUI())

    def buildToolsAndRecruitTroops(self, build_tools, recruit_troops, recruit_green, heal_troops=True):
        log("buildToolsAndRecruitTroops IN")
        player = getPlayer()

        if recruit_green:
            # Quick hack to reuse rest but only recruit in green
            recruit_troops = True
            castles = player._greenCastles[:]
        else:
            castles = player._castles[:]

        # random.shuffle(castles)

        # TODO apply a curring technique as the loop is the same for this as for build troops as well as for print castle info
        for castle in castles:
            # Avoid the jump if we're not going to do anything there (depends on player's config & parms passed to script)
            if not (heal_troops or (build_tools and self.isBuildToolsInCastle(castle)) or ((recruit_troops or recruit_green) and self.isRecruitTroopsInCastle(castle))):
                continue

            # Skip berimond, could be done but need has to be done another way
            if castle.isBerimond():
                continue

            console('-' * 80)
            console("jumping to {} '{}' ".format(('OP' if castle.isOp() else 'Castle'), castle.getEncodedName()))

            if castle.isOp():
                cmd = JumpToOp(castle._x, castle._y)
            else:
                cmd = JumpToCastle(castle._kingdomID, castle._id)

            self.runDelayed(cmd)
            time.sleep(random.randint(1, 2))  # Fake some processing time after jump
            if build_tools and self.isBuildToolsInCastle(castle):
                self.buildTools(cmd, castle)
            if recruit_troops and self.isRecruitTroopsInCastle(castle):
                self.recruitTroops(cmd, castle)

            # print "heal_troops: " + str(heal_troops) + " key present: " + str('injuredTroops' in cmd._result) + " len: " + str(len(cmd._result['injuredTroops']))
            # if heal_troops and 'injuredTroops' in cmd._result and len(cmd._result['injuredTroops']) > 0:
            #     self.doHealTroops(cmd, castle)

        log("buildToolsAndRecruitTroops OUT")

    def quickBuyAllToolsFromArmorer(self, castle, toolTypeToQtyDict):
        if castle.isBerimond():
            cmd = JumpToBerimond(castle._x, castle._y)
        elif castle.isOp():
            cmd = JumpToOp(castle._x, castle._y)
        else:
            cmd = JumpToCastle(castle._kingdomID, castle._id)
        self.runDelayed(cmd)

        ok = True
        for toolType, qty in toolTypeToQtyDict.iteritems():
            ok = self.quickBuyToolsFromArmorer(castle, toolType, qty)
            if not ok:
                break
        return ok

    def quickBuyToolsFromArmorer(self, castle, toolType, qty):
        log("quickBuyToolsFromArmorer IN, buy {:d} {}".format(qty, tools_and_troops_to_string(toolType)))

        kid = castle._kingdomID

        if toolType == TOOL_TYPE_LADDER:
            armorerToolType = ARMORER_TOOL_PURCHASE_TYPE_LADDER
            costPerUnit = ARMORER_TOOL_PURCHASE_TYPE_LADDER_PRICE
        elif toolType == TOOL_TYPE_BATTERING_RAM:
            armorerToolType = ARMORER_TOOL_PURCHASE_TYPE_BATTERING_RAM
            costPerUnit = ARMORER_TOOL_PURCHASE_TYPE_BATTERING_RAM_PRICE
        elif toolType == TOOL_TYPE_MANTLET:
            armorerToolType = ARMORER_TOOL_PURCHASE_TYPE_MANTLET
            costPerUnit = ARMORER_TOOL_PURCHASE_TYPE_MANTLET_PRICE
        else:
            console("CANNOT BUY unsupported tool type {}".format(tools_and_troops_to_string(toolType)))
            return False

        coins, rubies = getCoins()

        while qty > 0:
            if qty < 100:
                toolCount = qty
            else:
                toolCount = 100

            if coins > costPerUnit * toolCount:
                coins = self.runNoDelay(BuyToolsFromArmorer(kid, armorerToolType, toolCount))
            else:
                console("NOT enough coins to buy from armorer")
                return False

            log("quickBuyToolsFromArmorer bought {:d} {}".format(toolCount, tools_and_troops_to_string(toolType)))
            time.sleep(0.1)
            qty -= toolCount

        log("quickBuyToolsFromArmorer OUT")
        return True

    def buyToolsFromArmorer(self):
        log("buyToolsFromArmorer IN")
        player = getPlayer()

        castle = player._greenCastle
        if castle.isOp():
            cmd = JumpToOp(castle._x, castle._y)
        else:
            cmd = JumpToCastle(castle._kingdomID, castle._id)
        self.runDelayed(cmd)

        kid = castle._kingdomID
        toolType = ARMORER_TOOL_PURCHASE_TYPE_LADDER

        toolCount = 100
        for x in range(50):
            # if has_enough_coins_to_buy_tools(toolType, toolCount):
            cmd = self.runDelayed(BuyToolsFromArmorer(kid, toolType, toolCount))

    def buildTools(self, cmd, castle):
        # TODO this is specific to wood mantles at the moment
        if cmd._result['siegeWorkshop'] < BUILDING_SIEGE_WORKSHOP_LEVEL_2:
            console("Cannot build tools. No siege workshop or insufficient level {}".format(str(cmd._result['siegeWorkshop'])))
            return

        # TODO need siege/defensive workshop level handling depending on the tool type to recruit --> Needs a mapping in gge_constants
        # TODO need rss sufficiency checks --> Needs a function in gge_constants or better yet if we could get that from the server would be best
        # TODO add defensive tool distinction + workshop check
        # TODO put ratios (I want min, 200 ladder, 100 rams)
        #
        # result = cmd.result
        # if result['toolSlots'] > 0:
        #   if has_enough_rss_to_build_tools(TOOL_TYPE_MANTLET, 5, result):
        #     runDelayed(BuildTools(TOOL_TYPE_MANTLET, 5))
        #   else:
        #     print "Cannot build Tools not enough RSS"
        # else:
        #   print "Cannot build tools, no free slots"

        # TODO use inventory to see current qty of each element to figure how which to build next
        currentInventoryCmd = GUI()
        self.runDelayed(currentInventoryCmd)
        mantleCount = cmd.getToolOrTroopCount(TOOL_TYPE_MANTLET)
        ladderCount = cmd.getToolOrTroopCount(TOOL_TYPE_LADDER)
        ramCount = cmd.getToolOrTroopCount(TOOL_TYPE_BATTERING_RAM)

        toolState = cmd._result
        if toolState['toolSlots'] > 0:
            while toolState['toolSlots'] > 0:
                self.iceToolsRotation += 1
                self.sandToolsRotation += 1
                self.fireToolsRotation += 1
                self.greenToolsRotation += 1

                if castle._kingdomID == KINGDOM_ICE:
                    tool = self.getToolTypeToBuildInIce(castle, self.iceToolsRotation, mantleCount, ladderCount, ramCount)
                elif castle._kingdomID == KINGDOM_SANDS:
                    tool = self.getToolTypeToBuildInSands(castle, self.sandToolsRotation, mantleCount, ladderCount, ramCount)
                elif castle._kingdomID == KINGDOM_FIRE:
                    tool = self.getToolTypeToBuildInFire(castle, self.fireToolsRotation, mantleCount, ladderCount, ramCount)
                else:
                    tool = self.getToolTypeToBuildInGreen(castle, self.greenToolsRotation, mantleCount, ladderCount, ramCount)

                if tool == -1:
                    console("Instructed not to build tools for {}".format(kingdom_to_string(castle._kingdomID)))
                    break
                if not has_enough_rss_to_build_tools(tool, 5, toolState):
                    console("Cannot build Tools not enough RSS")
                    break

                cmd = self.runDelayed(BuildTools(tool, 5), True)
                toolState = cmd._result
        else:
            console("Cannot build tools, no free slots")

        log("buildTools OUT")

    def getToolTypeToBuildInIce(self, castle, toolsRotation, mantleCount, ladderCount, ramCount):
        if ramCount < 40:
            tool = TOOL_TYPE_BATTERING_RAM
        else:
            if int(toolsRotation) % 3 == 0:
                tool = TOOL_TYPE_MANTLET
            elif int(toolsRotation) % 2 == 0:
                tool = TOOL_TYPE_BATTERING_RAM
            else:
                tool = TOOL_TYPE_LADDER
        return tool

    def getToolTypeToBuildInSands(self, castle, toolsRotation, mantleCount, ladderCount, ramCount):
        if ladderCount < 36:
            tool = TOOL_TYPE_LADDER
        elif ramCount < 18:
            tool = TOOL_TYPE_BATTERING_RAM
        elif mantleCount < 150:
            tool = TOOL_TYPE_MANTLET
        elif ladderCount < 100:
            tool = TOOL_TYPE_LADDER
        elif int(toolsRotation) % 3 == 0:
            tool = TOOL_TYPE_MANTLET
        elif int(toolsRotation) % 2 == 0:
            tool = TOOL_TYPE_LADDER
        else:
            tool = TOOL_TYPE_BATTERING_RAM
        return tool

    def getToolTypeToBuildInFire(self, castle, toolsRotation, mantleCount, ladderCount, ramCount):
        if mantleCount < 40:  # ensures enough for 1 dragon hit
            tool = TOOL_TYPE_MANTLET
        elif ladderCount < 15:  # ensures enough for 1 dragon hit
            tool = TOOL_TYPE_LADDER
        elif mantleCount < 160:
            tool = TOOL_TYPE_MANTLET
        elif ladderCount < 75:
            tool = TOOL_TYPE_LADDER
        elif int(toolsRotation) % 3 == 0:
            tool = TOOL_TYPE_LADDER
        else:
            tool = TOOL_TYPE_MANTLET
        return tool

    def getToolTypeToBuildInGreen(self, castle, toolsRotation, mantleCount, ladderCount, ramCount):
        if int(round(time.time())) % 2 == 0:
            tool = TOOL_TYPE_LADDER
        elif random.randint(1, 3) % 2 == 0:  # 2 out of 3 times build mantle
            tool = TOOL_TYPE_BATTERING_RAM
        else:
            tool = TOOL_TYPE_MANTLET
        tool = TOOL_TYPE_MANTLET
        return tool

    @staticmethod
    def getCastleType(castle):
        if castle.isOp():
            return 'op'
        elif castle.isGreenMain():
            return 'main'
        elif castle.isIceMain():
            return 'ice'
        elif castle.isSandMain():
            return 'sand'
        elif castle.isFireMain():
            return 'fire'
        elif castle.isBerimond():
            return 'berimond'
        raise ValueError("UNKNOWN castle type")

    def getProfile(self):
        return self._profile

    def isRecruitTroopsInCastle(self, castle):
        return self.getProfile()['recruitTroops'][self.getCastleType(castle)]

    def isBuildToolsInCastle(self, castle):
        return self.getProfile()['buildTools'][self.getCastleType(castle)]

    def getRangeAttackerMax(self, castle):
        return self.getProfile()['rangeOffenseMax'][self.getCastleType(castle)]

    def getMeleeAttackerMax(self, castle):
        return self.getProfile()['meleeOffenseMax'][self.getCastleType(castle)]

    # Burners
    def getArcherMin(self, castle):
        if castle.isIceMain() or castle.isSandMain() or castle.isFireMain():
            return 15
        return 0

    def isRecruitDefensiveTroopsInCastle(self, castle):
        return self.getProfile()['recruitDefenseTroops'][self.getCastleType(castle)]

    def isRecruitOffensiveTroopsInCastle(self, castle):
        return self.getProfile()['recruitOffenseTroops'][self.getCastleType(castle)]

    def getRangeDefenderMax(self, castle):
        return self.getProfile()['rangeDefenseMax'][self.getCastleType(castle)]

    def getMeleeDefenderMax(self, castle):
        return self.getProfile()['meleeDefenseMax'][self.getCastleType(castle)]

    def getNumberOfTroopsPerSlot(self, castle, ttype=None):
        return 5

    def getMeleeDefenseType(self, castle):
        return TROOP_TYPE_KINGSGUARD_ROYAL_SENTINEL

    def getRangeDefenseType(self, castle):
        return TROOP_TYPE_KINGSGUARD_ROYAL_SCOUT

    def getMeleeOffenseType(self, castle):
        return TROOP_TYPE_KINGSGUARD_KNIGHT

    def getRangeOffenseType(self, castle):
        return TROOP_TYPE_KINGSGUARD_BOW

    def removeRubyCostingTroopsFromHospital(self, cmd):
        log("removeRubyCostingTroopsFromHospital IN")
        injuredTroops = cmd._result['injuredTroops']
        # print "LIST OF HEALABLE TROOPS >>>>>>>>>>>>>>>>>>>>>>>>>>>>>> [" + ','.join([str(i) for i in Client.TROOPS_COSTING_COINS_TO_HEAL]) + "]"
        for troopType in injuredTroops.keys():
            if troopType not in Client.TROOPS_COSTING_COINS_TO_HEAL:
                count = injuredTroops[troopType]
                print (tools_and_troops_to_string(troopType) + " (" + str(troopType) + ") costs rubies to heal! REMOVING " + str(count) + " " + tools_and_troops_to_string(troopType) + " from HOSPITAL!")
                cmd = self.runDelayed(RemoveTroopsFromHospital(troopType, count))
                del injuredTroops[troopType]

        # The response contains whats left to heal but not the free slots since it has nothing to do with the call
        # We would need to consolidate troops left to heal & slots remaining in the model not take it directly from the commands

        log("removeRubyCostingTroopsFromHospital OUT")
        # return cmd

    def healTroops(self):
        log("healTroops IN")
        player = getPlayer()

        castles = player._castles[:]

        # random.shuffle(castles)

        # TODO apply a curring technique as the loop is the same for this as for build troops as well as for print castle info
        for castle in castles:
            console('-' * 80)
            console("jumping to {} '{}' ".format(('OP' if castle.isOp() else 'Castle'), castle.getEncodedName()))

            if castle.isOp():
                cmd = JumpToOp(castle._x, castle._y)
            else:
                cmd = JumpToCastle(castle._kingdomID, castle._id)

            self.runDelayed(cmd)

            # time.sleep(random.randint(6, 9))  # Fake some processing time after jump
            time.sleep(random.randint(1, 2))  # Fake some processing time after jump

            if 'injuredTroops' in cmd._result and len(cmd._result['injuredTroops']) > 0:
                self.doHealTroops(cmd, castle)

        log("healTroops OUT")


    def doHealTroops(self, cmd, castle):
        log("doHealTroops IN")

        # if cmd._result['hospital'] < BUILDING_HOSPITAL_1:
        #     console("Cannot heal tools. No hospital or insufficient level {}".format(str(cmd._result['hospital'])))
        #     return

        self.removeRubyCostingTroopsFromHospital(cmd)
        # freeSlots = cmd.getFreeSlots()
        # injuredTroops = cmd.getInjuredTroops()

        castleState = cmd._result
        freeSlots = castleState['hospitalSlots']
        injuredTroops = castleState['injuredTroops']

        if len(injuredTroops) == 0:
            console("No troops to heal")
            return

        if freeSlots == 0:
            console("Cannot heal troops, no free slots")
            return

        help = self.isAskForHelp()

        while freeSlots > 0:
            count = 0
            troopType = -1  # removes warning
            for troopType in injuredTroops.keys():
                count = injuredTroops[troopType]

            if count == 0:
                break

            # TODO Determine this based on level of hospital
            if count > 5:
                count = 5

            cmd = self.runDelayed(HealTroops(troopType, count, help), short=True)

            # freeSlots = cmd.getFreeSlots()
            # injuredTroops = cmd.getInjuredTroops()

            castleState = cmd._result
            injuredTroops = castleState['injuredTroops']
            freeSlots = castleState['hospitalSlots']

        log("doHealTroops OUT")

    def recruitTroops(self, cmd, castle):
        if cmd._result['barracks'] < BUILDING_BARRACKS_LEVEL_5:
            console("Cannot build tools. No barracks or insufficient level {}".format(str(cmd._result['barracks'])))
            return

        castleState = cmd._result

        # TODO use inventory to see current qty of each element to figure which to build next
        # currentInventoryCmd = self.runDelayed(GUI())
        # archerCount = currentInventoryCmd._result['tool' + str(TROOP_TYPE_ARCHER)]

        archerCount = cmd.getToolOrTroopCount(TROOP_TYPE_ARCHER)
        meleeDefenseCount = cmd.getToolOrTroopCount(self.getMeleeDefenseType(castle))  # Def melee
        rangeDefenseCount = cmd.getToolOrTroopCount(self.getRangeDefenseType(castle))  # Def range
        rangeOffenseCount = cmd.getToolOrTroopCount(self.getRangeOffenseType(castle))  # Off range
        meleeOffenseCount = cmd.getToolOrTroopCount(self.getMeleeOffenseType(castle))  # Off melee

        help = self.isAskForHelp()

        console("Troop Counts defense[melee={:d}, range={:d}], offense[knights={:d}, bow={:d}], archers={:d}".format(meleeDefenseCount, rangeDefenseCount, meleeOffenseCount, rangeOffenseCount, archerCount))

        # TODO Should look at food levels & food prod, to determine what to recruit but 2 issues with that
        # 1- reported food (production - consumption) values don't match what the game reports
        # 2- sometimes you want to be in the negative would require some level of tolerance for castles where barons are hit
        meleeDefenseMax = self.getMeleeDefenderMax(castle)
        rangeDefenseMax = self.getRangeDefenderMax(castle)
        meleeOffenseMax = self.getMeleeAttackerMax(castle)
        rangeOffenseMax = self.getRangeAttackerMax(castle)
        archerMax = self.getArcherMin(castle)

        if castleState['troopSlots'] > 0:
            while castleState['troopSlots'] > 0:
                if not (archerCount < archerMax or meleeDefenseCount < meleeDefenseMax or rangeDefenseCount < rangeDefenseMax or rangeOffenseCount < rangeOffenseMax or meleeOffenseCount < meleeOffenseMax):
                    console("REACHED TROOP QUOTAS NOT RECRUITING meleeDefenseCount={:d}, rangeDefenseCount={:d}, rangeOffenseCount={:d}, meleeOffenseCount={:d}".format(meleeDefenseCount, rangeDefenseCount, rangeOffenseCount, meleeOffenseCount))
                    break

                if self.isRecruitOffensiveTroopsInCastle(castle) and archerCount < archerMax:
                    troopType = TROOP_TYPE_ARCHER
                elif self.isRecruitDefensiveTroopsInCastle(castle) and (meleeDefenseCount < 150 < meleeDefenseMax or rangeDefenseCount < 150 < rangeDefenseMax):
                    troopType = self.getDefenseTypeToRecruit(castle, rangeDefenseCount, rangeDefenseMax, meleeDefenseCount, meleeDefenseMax)
                elif self.isRecruitOffensiveTroopsInCastle(castle) and (meleeOffenseCount < meleeOffenseMax or rangeOffenseCount < rangeOffenseMax):
                    troopType = self.getOffenseTypeToRecruit(castle, rangeOffenseCount, rangeOffenseMax, meleeOffenseCount, meleeOffenseMax)
                elif self.isRecruitDefensiveTroopsInCastle(castle) and (meleeDefenseCount < meleeDefenseMax or rangeDefenseCount < rangeDefenseMax):
                    troopType = self.getDefenseTypeToRecruit(castle, rangeDefenseCount, rangeDefenseMax, meleeDefenseCount, meleeDefenseMax)
                else:
                    console("NOT RECRUITING!")
                    break

                troopCount = self.getNumberOfTroopsPerSlot(castle, troopType)
                cmd = self.runDelayed(BuildTroops(troopType, troopCount, help), short=True)
                castleState = cmd.result
        else:
            console("Cannot recruit troops, no free slots")

        log("recruitTroops OUT")

    def getOffenseTypeToRecruit(self, castle, rangeOffenseCount, rangeOffenseMax, meleeOffenseCount, meleeOffenseMax):
        if rangeOffenseCount < rangeOffenseMax and meleeOffenseCount < meleeOffenseMax:
            if rangeOffenseCount > meleeOffenseCount:
                troopType = self.getMeleeOffenseType(castle)
            else:
                troopType = self.getRangeOffenseType(castle)
        elif meleeOffenseCount < meleeOffenseMax:
            troopType = self.getMeleeOffenseType(castle)
        else:
            troopType = self.getRangeOffenseType(castle)
        return troopType

    def getDefenseTypeToRecruit(self, castle, rangeDefenseCount, rangeDefenseMax, meleeDefenseCount, meleeDefenseMax):
        if rangeDefenseCount < rangeDefenseMax and meleeDefenseCount < meleeDefenseMax:
            if rangeDefenseCount > meleeDefenseCount:
                troopType = self.getMeleeDefenseType(castle)
            else:
                troopType = self.getRangeDefenseType(castle)
        elif meleeDefenseCount > rangeDefenseCount:
            troopType = self.getRangeDefenseType(castle)
        else:
            troopType = self.getMeleeDefenseType(castle)
        return troopType

    def isAskForHelp(self):
        return self.args.ask_for_help

    def sendRssToPlayer(self):
        # Implements in sub-class
        pass

    def doSendRssToPlayer(self, player, kid, greenSrcCastleName, targetPlayerName, greenTargetCastleName, rss, speed):
        sourceCastle = player.getCastle(kid, greenSrcCastleName)

        playerUID, x, y = self.lookupTarget(targetPlayerName, kid, greenTargetCastleName)
        console("Located target player={:d} coords=[{:d},{:d}]".format(playerUID, x, y))

        allCastlesOnMap = self.jumpToWorld(sourceCastle, kid)
        if allCastlesOnMap is not None and len(allCastlesOnMap) > 0:
            self.doSendRssToOneTarget(sourceCastle, {'x': x, 'y': y}, rss, speed)

    def attackPlayer(self):
        log("attackPlayer IN")
        player = getPlayer()
        speed = SPEED_LVL_3_STABLE_HIGH_RUBY_BOOST

        # Kingdom to attack in
        kid = KINGDOM_ICE
        # Use these 2 only if you want to attack in green
        # Target castle name (exact spelling)
        greenTargetCastleName = None
        # The castle/op you are attacking from
        greenSrcCastleName = None

        leftFlankType = None
        frontType = None
        rightFlankType = None

        sourceCastle = player.getCastle(kid, greenSrcCastleName)
        commanderName = "Your commander name"
        targetPlayerName = 'Target player name exact spelling and casing!'

        formation = self.getHumanTargetAttackFormation(leftFlankType, frontType, rightFlankType)
        self.doAttackPlayer(speed, sourceCastle, kid, commanderName, targetPlayerName, formation, greenTargetCastleName)

    def doAttackPlayer(self, speed, sourceCastle, kid, commanderName, playerName, formation, greenTargetCastleName=None):
        # TODO FIXME Will crash on unicode string
        log("doAttackPlayer IN, commanderName={}, playerName={}, kid={}, greenTargetCastleName={}, speed={}, sourceCastle={}".format(gge_utils.encodeUnicode(commanderName), gge_utils.encodeUnicode(playerName), str(kid), gge_utils.encodeUnicode(greenTargetCastleName), str(speed), str(sourceCastle)))

        playerUID, x, y = self.lookupTarget(playerName, kid, greenTargetCastleName)
        console("Located target player={:d} coords=[{:d},{:d}]".format(playerUID, x, y))

        # TODO this is optional in game and should be here too!
        allCastlesOnMap = self.jumpToWorld(sourceCastle, kid)
        if allCastlesOnMap is not None and len(allCastlesOnMap) > 0:
            commanderID = self.resolveCommander(commanderName)

            if commanderID != -1:
                targetDataCommand = self.runDelayed(GetPlayerTargetData(sourceCastle._x, sourceCastle._y, x, y, kid))
                totals = self.calculate_tool_counts(formation)
                totalsOk = self.checkTotals(totals, targetDataCommand.result)
                if totalsOk:
                    console("Troop and Tool counts are sufficient to attack!")

                if formation and totalsOk:
                    log("doAttack format={}".format(str(formation)))

                    self.printTroopToolTotalsInAttack(totals)
                    self.runDelayed(Pin())
                    self.runDelayed(Pin())
                    print ("\n" + datetime.datetime.now().strftime('%a %B %d %H:%M:%S'))
                    if not self.args.dry_run:
                        self.runDelayed(AttackCommand(kid, formation, sourceCastle._x, sourceCastle._y, x, y, commanderID, speed))
                        print ("\n" + datetime.datetime.now().strftime('%a %B %d %H:%M:%S'))
                    else:
                        console("DRY RUN ONLY!!!")
                else:
                    console("FAILED to SEND ATTACK, formation found {}, totals {}".format(str(formation is not None), str(totalsOk)))

    def printAllianceCoordinates(self, alliances, relativeToMe = False, rvsOnly = False):
        for allianceName in alliances:
            console("=" * 40)
            console(allianceName)
            console("=" * 40)
            cmd = self.runDelayed(GetAllianceID(allianceName))

            alliancePID = 0
            for alliance in cmd.result['L']:
                if alliance[2][1].lower() == allianceName.lower():
                   alliancePID = alliance[2][0]

            cmd2 = self.runDelayed(GetAlliancePlayers(alliancePID))

            if relativeToMe:
                sortedPlayers = self.sortRVList(getPlayer(), cmd2.result['A']['M'])
                for player in sortedPlayers:
                    if not rvsOnly:
                        for castle in player['AP']:
                            # Filter out Berimond and Storm Island (len=1 or len=5)
                            if len(castle) > 5:
                                print (">>>>>>>>>>>>>>>>>>>>>>>>" + player['N'] + "," + allianceName + "," + kingdom_to_string(castle[0]) + "," + self.lookupCastleType(castle[4]) + "," + str(castle[2]) + "," + str(castle[3]) + ", distance={:2.1f}".format(castle[len(castle)-1]))
                    for rv in player['VP']:
                        # Does not provide the RV type!
                        msg = player['N'] + "," + allianceName + "," + kingdom_to_string(rv[0]) + ",RV," + str(rv[2]) + "," + str(rv[3]) + ", distance={:2.1f}".format(rv[len(rv)-1])
                        if rv[len(rv)-1] <= 20:
                            msg = msg + " VERY_CLOSE"
                        elif rv[len(rv)-1] <= 50:
                            msg = msg + " CLOSE"
                        elif rv[len(rv)-1] <= 85:
                            msg = msg + " PROXIMITY"
                        print (msg)
            else:
                for player in cmd2.result['A']['M']:
                    if isinstance(player['N'], unicode):
                        player['N'] = unicode.encode(player['N'], 'utf-8')
                    if not rvsOnly:
                        for castle in player['AP']:
                            # Filter out Berimond or Storm Island (the one with len=1)
                            if len(castle) > 4:
                                print (player['N'] + "," + allianceName + "," + kingdom_to_string(castle[0]) + "," + self.lookupCastleType(castle[4]) + "," + str(castle[2]) + "," + str(castle[3]))
                            elif len(castle) == 1:
                                print ("FOUND 1\n"*15)
                    for rv in player['VP']:
                        print (player['N'] + "," + allianceName + "," + kingdom_to_string(rv[0]) + ",RV," + str(rv[2]) + "," + str(rv[3]))

    def printSamuraiRankings(self, allianceNames):
            playersPerAlliance = self._printSamuraiRankings(allianceNames)
            for allianceName, players in playersPerAlliance.iteritems():
                print ("----------- " + allianceName +" -----------")
                import locale
                locale.setlocale(locale.LC_ALL, 'en_US')
                for p in players:
                    print ("#{:4d} {: >15} {: >11}".format(p['rank'],p['name'],locale.format("%d", p['score'], grouping=True)))

    def _printSamuraiRankings(self, allianceNames):
        # Open Samurai individual ranking dialog dispatches this
        # %xt%EmpirefourkingdomsExGG_4%hgh%1%{"LT":500,"LID":1,"SV":"-1"}%
        #
        # Jump to top page
        # %xt%EmpirefourkingdomsExGG_4%hgh%1%{"LT":500,"LID":7,"SV":"1"}%
        #
        # Next page
        # %xt%EmpirefourkingdomsExGG_4%hgh%1%{"LT":500,"LID":7,"SV":"7"}%
        #
        # Next page
        # %xt%EmpirefourkingdomsExGG_4%hgh%1%{"LT":500,"LID":7,"SV":"11"}%
        #
        # For some reason it goes to one then asks for 7 then it asks for 11 (so +6 then +4 and it continues +4 onward)

        log("printSamuraiRankings IN")
        results = {}
        cmd = self.runDelayed(GetSamuraiEventRankings())
        lid = cmd.resultLID

        allianceNamesLowcase = []

        for allianceName in allianceNames:
            allianceName = allianceName.lower()
            if isinstance(allianceName, unicode):
                allianceName = unicode.encode(allianceName, 'utf-8')
            allianceNamesLowcase.append(allianceName)

        index = 1
        cmd = self.runDelayed(GetSamuraiEventRankings(lid, str(index)), True)
        i = 1

        try:
            # while index < 50:
            while index < 3001:
                print ("#" + str(i))
                i += 1

                if cmd.result is not None:
                    for player in cmd.result['L']:
                        # Skip players without an alliance
                        if not 'AN' in player[2]:
                            continue

                        playerAllianceName = player[2]['AN'].lower()
                        if isinstance(playerAllianceName, unicode):
                            playerAllianceName = unicode.encode(playerAllianceName, 'utf-8')

                        for allianceName in allianceNamesLowcase:
                            log("comparing: " + playerAllianceName + " to " + allianceName)
                            if playerAllianceName == allianceName:
                                if not allianceName in results:
                                    players = []
                                    results[allianceName] = players
                                else:
                                    players = results[allianceName]

                                rank = player[0]
                                score = player[1]
                                playerNameS = player[2]['N']
                                if isinstance(playerNameS, unicode):
                                    playerNameS = unicode.encode(playerNameS, 'utf-8')

                                # Don't insert duplicates (game returns entries a couple of ranks higher than the requested rank index, so duplicates are returned)
                                found = False
                                for e in players:
                                    if e['rank'] == rank:
                                        found = True

                                if not found:
                                    players.append({'rank': rank, "name": playerNameS, "score": score})

                    # Mimic game behaviour: goes to 1 then asks for 7 then asks for 11 (so +6 then +4 and it continues +4 onward)
                    if index == 1:
                        index += 6
                    else:
                        index += 4
                    cmd = self.runDelayed(GetSamuraiEventRankings(lid, str(index)), True)
                else:
                    break
        except:
            pass

        log("printSamuraiRankings OUT player count={:d}".format(len(results)))
        return results

    def sortRVList(self, me, players):
        for player in players:
            if isinstance(player['N'], unicode):
                player['N'] = unicode.encode(player['N'], 'utf-8')
            for c in player['AP']:
                castle = me.getCastle(c[0])
                if castle:
                    c.append(calculateDistance(castle._x, castle._y, c[2], c[3]))
                else:
                    log("DEBUG did not find castle in kid: " + str(c[0]))
            for rv in player['VP']:
                castle = me.getCastle(rv[0])
                if castle:
                    rv.append(calculateDistance(castle._x, castle._y, rv[2], rv[3]))
                else:
                    # rv.append(-1)
                    # debug
                    log("DEBUG did not find RV in kid: " + str(rv[0]))

        sortedPlayers = sorted(players, cmp=Client.sortAlphabetically)

        # TODO fix this ie crashes
        # for player in players:
            # for c in player['AP']:
            #     sorted(c,cmp=Client.sortByDistance)
            # for rv in player['VP']:
            #     sorted(rv,cmp=Client.sortByDistance)

        return sortedPlayers

    @staticmethod
    def sortAlphabetically(item1, item2):
        if item1['N'] < item2['N']:
            return -1
        elif item1['N'] > item2['N']:
            return 1
        return 0

    # Use this one in the future
    def sortAlphabeticallyCaseInsensitive(item1, item2):
        if item1['N'].lower() < item2['N'].lower():
            return -1
        elif item1['N'].lower() > item2['N'].lower():
            return 1
        return 0

    @staticmethod
    def sortByDistance(item1, item2):
        '''Sort by distance (simple numerical comparison of last element in each item (which is an array)'''
        if item1[len(item1) -1] < item2[len(item2) -1]:
            return -1
        elif item1[len(item1) -1] > item2[len(item2) -1]:
            return 1
        return 0

    # TODO replace with better solution and move to gge_constants
    def lookupCastleType(self, num):
        if num == 1:
            return "Main"
        elif num == 4:
            return "OP"
        elif num == 12:
            return "Castle"
        else:
            return "Castle" + str(num)

    def lookupTarget(self, playerName, kid, greenCastleName=None):
        # log("lookupTarget IN, playerName={}, kid={} castle={}".format(playerName, str(kid), greenCastleName))
        # TODO FIXME Will crash on unicode string
        # log("lookupTarget IN, playerName={}, kid={}".format(playerName, str(kid)))

        # Open Rankings dialog dispatches this
        # %xt%EmpirefourkingdomsExGG_4%hgh%1%{"LT":5,"SV":"-1","LID":1}%
        #
        # Search for target player by name
        # %xt%EmpirefourkingdomsExGG_4%hgh%1%{"LT":5,"SV":"newport","LID":6}%
        #
        # List his castles
        # %xt%EmpirefourkingdomsExGG_4%gdi%1%{"PID":347270}%
        #
        # Jump to world of the castle you selected
        # %xt%EmpirefourkingdomsExGG_4%wgd%1%{"KID":1}%
        #
        # Get target info
        # %xt%EmpirefourkingdomsExGG_4%aci%1%{"SX":598,"TY":712,"KID":1,"SY":493,"TX":509}%
        #

        # Lookup player
        # Find castle XY for target world
        playerUID = None
        x = 0
        y = 0

        self.runDelayed(GetRankings())
        cmd = self.runDelayed(GetRankings(playerName))

        if cmd.result is not None:
            playerName = playerName.lower()
            for alliance in cmd.result['L']:
                log("comparing: " + alliance[2]['N'] + " to " + playerName)
                if alliance[2]['N'].lower() == playerName:
                    playerUID = alliance[2]['OID']
                    playerNameS = alliance[2]['N']
                    if isinstance(playerNameS, unicode):
                        playerNameS = unicode.encode(playerNameS, 'utf-8')
                    console("FOUND '{}' OID: {:d}".format(playerNameS, playerUID))
                    break

        if playerUID is not None:
            cmd = self.runDelayed(GetPlayerCastleList(playerUID))
            for kingdom in cmd.result['gcl']['C']:
                if kingdom['KID'] == kid:
                    log("Found KID {:d}".format(kid))
                    for castle in kingdom['AI']:
                        if (greenCastleName is not None and greenCastleName.lower() == castle['AI'][10].lower()) or greenCastleName is None:
                            if isinstance(castle['AI'][10], unicode):
                                log("Found Castle {}".format(unicode.encode(castle['AI'][10], 'utf-8')))
                            else:
                                log("Found Castle {}".format(castle['AI'][10]))
                            x = castle['AI'][1]
                            y = castle['AI'][2]
                            break
                    break
        else:
            print ("DIDN'T FIND THE PLAYER YOU PROBABLY MISSPELLED HIS NAME!!!")
            raise Exception('Player not found ' + playerName)

        if x == 0 and y == 0:
            print ("DIDN'T FIND THE CASTLE YOU PROBABLY MISSPELLED THE NAME!!!")
            raise Exception('Castle not found ' + str(greenCastleName))


        log("lookupTarget OUT playerUID={:d} x={:d}, y={:d}".format(playerUID, x, y))
        return playerUID, x, y

    # TODO refactor this with other routine to put command resolution in a subroutine
    def resolveCommander(self, cname):
        log("resolveCommander IN, looking for commander name: " + cname)

        player = getPlayer()
        if cname in player.commanders:
            cid = player.commanders[cname]
            if self.isCommanderAvailable(cname, cid):
                log("resolveCommander OUT, commanderId={:d}".format(cid))
                return cid
            else:
                console("Commander '{}' NOT available to attack".format(cname))
        else:
            console("Commander '{}' NOT FOUND (fix your shit)".format(cname))

        log("resolveCommander OUT, commander not found")
        return -1

    def getHumanTargetAttackFormation(self, leftFlankType, frontType, rightFlankType):
        """
        For now this is only good for level 5 walls (level 70 player) due to troop and tool counts used.
        """

        log("getHumanTargetAttackFormation IN, left={}, front={}, right={}".format(str(leftFlankType), str(frontType), str(rightFlankType)))
        left = self.getHumanTargetFlankFormation(leftFlankType)
        front = self.getHumanTargetFrontFormation(frontType)
        right = self.getHumanTargetFlankFormation(rightFlankType)
        formation = self.buildFormationMessage(left, front, right)

        log("getHumanTargetAttackFormation OUT")
        return formation

    def getHumanTargetFrontFormation(self, frontType):
        rangeTroopType = TROOP_TYPE_KINGSGUARD_BOW
        meleeTroopType = TROOP_TYPE_KINGSGUARD_KNIGHT
        if ELITE_KG:
            rangeTroopType = TROOP_TYPE_ELITE_CROSSBOWMAN
            meleeTroopType = TROOP_TYPE_ELITE_KNIGHT

        if ALL_DEMONS:
            rangeTroopType = TROOP_TYPE_DEATHLY_HORROR
            meleeTroopType = TROOP_TYPE_DEMON_HORROR

        troopCount = 231
        troopCount = 212

        # @formatter:off
        front = [{"U": [[rangeTroopType, troopCount]], "T":[[TOOL_TYPE_BELFRY, 19], [TOOL_TYPE_HEAVY_RAM, 19], [TOOL_TYPE_BOULDERS, 12]]},
                 {"U": [[meleeTroopType, troopCount]], "T":[[TOOL_TYPE_BELFRY, 8],  [TOOL_TYPE_HEAVY_RAM, 12], [TOOL_TYPE_SHIELD_WALL, 30]]},
                 {"U": [[meleeTroopType, troopCount]], "T":[[TOOL_TYPE_BELFRY, 19], [TOOL_TYPE_HEAVY_RAM, 19], [TOOL_TYPE_BOULDERS, 12]]},
                 {"U": [[meleeTroopType, troopCount]], "T":[[TOOL_TYPE_BELFRY, 19], [TOOL_TYPE_HEAVY_RAM, 19], [TOOL_TYPE_BOULDERS, 12]]},
                 {"U": [[meleeTroopType, troopCount]], "T":[[TOOL_TYPE_GLORY_BANNER, 50]]}]
        # @formatter:on

        return front

    def getHumanTargetFlankFormation(self, formationType):
        rangeTroopType = TROOP_TYPE_KINGSGUARD_BOW
        meleeTroopType = TROOP_TYPE_KINGSGUARD_KNIGHT
        if ELITE_KG:
            rangeTroopType = TROOP_TYPE_ELITE_CROSSBOWMAN
            meleeTroopType = TROOP_TYPE_ELITE_KNIGHT
        if ALL_DEMONS:
            rangeTroopType = TROOP_TYPE_DEATHLY_HORROR
            meleeTroopType = TROOP_TYPE_DEMON_HORROR

        flankTroopCount = 102

        # @formatter:off
        flank = [{"U": [[rangeTroopType, flankTroopCount]], "T":[[TOOL_TYPE_BELFRY,   23], [TOOL_TYPE_BOULDERS, 17]]},
                 {"U": [[rangeTroopType, flankTroopCount]], "T":[[TOOL_TYPE_BELFRY,   23], [TOOL_TYPE_BOULDERS, 17]]},
                 {"U": [[rangeTroopType, flankTroopCount]], "T":[[TOOL_TYPE_BOULDERS, 8], [TOOL_TYPE_SHIELD_WALL, 32]]},
                 {"U": [[rangeTroopType, flankTroopCount]], "T":[[TOOL_TYPE_BOULDERS, 9], [TOOL_TYPE_SHIELD_WALL, 31]]},
                 {"U": [[rangeTroopType, flankTroopCount]], "T":[[TOOL_TYPE_BELFRY,   20], [TOOL_TYPE_SHIELD_WALL, 20]]}
                 ]
        # @formatter:on
        return flank

    @staticmethod
    def buildFormationMessage(left, front, right):
        log("buildFormationMessage IN, left={}, front={}, right={}".format(str(left), str(front), str(right)))

        waves = []
        for x in range(len(left)):
            # Respect exact attribute order as the original message sent by the game, see pcaps, order is L,R,M standard dict does not guarantee an order.
            wave = OrderedDict()
            wave["L"] = left[x]
            wave["R"] = right[x]
            wave["M"] = front[x]
            waves.append(wave)
        message = json.dumps(waves)
        # No white spaces in messages so remove all of them from this
        message = removeAllBlanks(message)

        log("buildFormationMessage OUT, message=" + message)
        return message

    def jumpToWorld(self, castle, kid):
        if castle is not None:
            log("jumping to {}".format(kingdom_to_string(kid)))
            cmd = self.runDelayed(JumpToWorld(kid))
            return cmd.allCastlesOnMap # return cmd.result
        return None

    def listBarons(self):
        log("listBarons IN")
        player = getPlayer()
        self.printDebug_For_AttackBaronsInGreen(player)
        log("listBarons OUT")


    def useRangeDemonsForNomads(self):
        """
        If range demons can be used to attack a nomad camp
        """
        return True

    def useDemonsForBarons(self):
        """
        If demons can be used to attack a rbc
        """
        return True

    # TODO DEPRECATED
    def getBaronTroopExclusionList(self, kid, sourceCastle):
        """
        By default allow all troops to be used to attack barons

        :param kid:
        :param sourceCastle:
        :return:
        """
        return []

    # TODO DEPRECATED
    def getTroopsExcludedFromBeingBurners(self, kid, sourceCastle):
        """
        By default prevent all demons from being used as burners on barons

        :param kid:
        :param sourceCastle:
        :return:
        """
        return [TROOP_TYPE_DEATHLY_HORROR, TROOP_TYPE_VET_DEATHLY_HORROR, TROOP_TYPE_DEMON_HORROR, TROOP_TYPE_VET_DEMON_HORROR]

    def getTroopsToUseAsBurners(self, sourceCastle):
        """
        --By default don't define any explicit troop types to be used as burners--
        By default allow all troop types levels to be used as burners

        :param sourceCastle:
        :return:
        """
        return [TROOP_TYPE_SWORDSMAN, TROOP_TYPE_SPEARMAN, TROOP_TYPE_MACEMAN, TROOP_TYPE_TWO_HANDED_SWORDSMAN, TROOP_TYPE_ARCHER, TROOP_TYPE_CROSSBOWMAN, TROOP_TYPE_BOWMAN, TROOP_TYPE_HEAVY_CROSSBOWMAN]

    def isAttackTroopBurnerOfLastResort(self):
        """
        By default allow attackers to be used as burners in case no burners are available
        :return:
        """
        return True

    def mustFillAllWavesForBaronAttack(self):
        """
        By default do not force all waves to be filled
        :return:
        """
        return False

    def getTroopsToUseAsAttackersForBaron(self, sourceCastle):
        """
        By default all offensive melee and range troops can be used to attack a baron.
        :param sourceCastle:
        :return:
        """

        # The methods called here calls other methods which allow conditioning of which types are really part of the resulting list
        return list(self.getBaronAttackMeleeTroops()) + self.getBaronAttackRangeTroops()

    @staticmethod
    def filterAndSortNomadList(allCastlesOnMap):
        cp = []
        # TODO make this using a filter like it should be in python
        for t in allCastlesOnMap:
            if t[0] == CASTLE_TYPE_NOMAD:
                # Correct GG stupidity
                if t[5] < 0:
                    t[5] = 0
                cp.append(t)

        return sorted(cp, cmp=Client.sortByTimeRemainingAndLevel)

    @staticmethod
    def sortByTimeRemainingAndLevel(item1, item2):
        if item1[5] < item2[5]:
            return -1
        elif item1[5] > item2[5]:
            return 1

        if item1[4] < item2[4]:
            return -1
        elif item1[4] > item2[4]:
            return 1

        return 0

    def spyAndAttackNomads(self):
        log("spyAndAttackNomads IN")
        player = getPlayer()
        cmd = self.runDelayed(JumpToWorld(KINGDOM_GREEN))
        greenCastles = deque(player.getGreenCastles())

        # This also sets to 0 negative time till attackable values
        nomads = self.filterAndSortNomadList(cmd.allCastlesOnMap)

        attackable = 0
        for nomadCamp in nomads:
            if nomadCamp[5] == 0:
                attackable += 1

        # All Nomads are returned in this command
        for nomadCamp in nomads:
            level = 81 + nomadCamp[4]

            seconds = nomadCamp[5]
            minutes = seconds / 60
            hours = minutes / 60
            minutes -= hours * 60
            seconds = seconds - minutes * 60 - hours * 60 * 60
            console('-' * 80)
            console("Found NOMAD at: X={:d}, Y={:d}, Time since spy report={:d}, Level={:d}, {:d}h{:d}m{:d}s till attackable, No idea={:d}, Always -601={:d}".format(nomadCamp[1], nomadCamp[2], nomadCamp[3], level, hours, minutes, seconds, nomadCamp[6], nomadCamp[7]))
            console('-' * 80)
            pretty_print(nomadCamp, "NOMAD")

            if nomadCamp[5] != 0:
                if not self.args.use_time_skips:
                    console("Nomad is NOT attackable")
                    continue

                self.applyTimeSkip(nomadCamp[1], nomadCamp[2], KINGDOM_GREEN, hours, minutes, seconds)

            if self.isAttackTravelingTo(KINGDOM_GREEN, nomadCamp[1], nomadCamp[2]):
                console("Attack already travelling to {:d}, {:d}".format(nomadCamp[1], nomadCamp[2]))
                continue

            console("Nomad is attackable")

            # TODO use these to do a 1st pass and see what could be sent if we failed to send but could have had we had enough tools, then buy tools and try again
            sentAttack = False
            considerBuyingTools = False
            needsSpyReport = False

            for sourceCastle in greenCastles:
                castleName = sourceCastle.getEncodedName()

                commanderName, commanderID = self.getCommanderForNomadAttack(sourceCastle, nomadCamp)
                if commanderName is not None:
                    console("-----------> commander => " + commanderName + ", castleName => " + ('None' if castleName is None else castleName))
                else:
                    console("No commander specified")

                targetDataCommand = self.runDelayed(GetTargetData(sourceCastle._x, sourceCastle._y, nomadCamp[1], nomadCamp[2], KINGDOM_GREEN))

                if 'S' in targetDataCommand.result:
                    console("Target has already been spied on")
                    pretty_print(targetDataCommand.result['S'], 'NOMAD DEFENSE')

                    if commanderName is not None:
                        commander = player.getCommanderByName(commanderName)
                        if commander:
                            wallNegation = int(commander.getEquipmentBonus(EQ_BONUS_COMMANDER_WALL_PROTECTION_OF_ENEMY))
                            gateNegation = int(commander.getEquipmentBonus(EQ_BONUS_COMMANDER_GATE_PROTECTION_OF_ENEMY))
                        else:
                            print ("CANNOT FIND specified commander {} (name matching is case sensitive)".format(commanderName))
                            return

                        if NOMAD_DEBUG:
                            print ("Wall negation {:d} gate negation {:d}".format(int(wallNegation), int(gateNegation)))

                        formation, totals = self.getNomadAttackFormation(sourceCastle, level, targetDataCommand.result, targetDataCommand.result['S'], commanderName, gateNegation, wallNegation)
                        if formation is None:
                            print ("Could not build formation")
                            # print "=" * 40
                            continue

                        if NOMAD_DEBUG:
                            print (formation.replace('{"L', '\n{"L'))
                            print ("=" * 40)

                        missing, troopsMissing, toolsMissing = self.newCheckTotals(totals, targetDataCommand.result)

                        # Buy all missing tools (we know we have the troops to attack otherwise the formation would not have been built)
                        if toolsMissing:
                            considerBuyingTools = True
                            missingTools = {k:v for k,v in missing.iteritems() if is_tool(k)}
                            if self.quickBuyAllToolsFromArmorer(sourceCastle, missingTools):
                                for k in missing.keys():
                                    del missing[k]
                            # Jump outside of castle (quick buy forced a jump within a castle) ... might not be mandatory not sure
                            self.runDelayed(JumpToWorld(KINGDOM_GREEN))

                        if len(missing) == 0:
                            console("Troop and Tool counts are sufficient to attack!")
                            if not self.args.dry_run:
                                self.runDelayed(Pin())
                                self.runDelayed(Pin())
                                speed = sourceCastle.getMaxCoinSpeed()
                                self.runDelayed(AttackCommand(KINGDOM_GREEN, formation, sourceCastle._x, sourceCastle._y, nomadCamp[1], nomadCamp[2], commanderID, speed, True))
                                sentAttack = True
                                break
                    else:
                        console("No commander specified")
                        break  # No commanders are available so stop looping
                else:
                    console("NO spy report found, attempting to send Spies!")
                    self.doSpyBaron(sourceCastle, nomadCamp[1], nomadCamp[2], KINGDOM_GREEN, sourceCastle.getMaxCoinSpeed())
                    needsSpyReport = True

            # Cycle through castles (first to last and around again)
            greenCastles.append(greenCastles.popleft())

        log("spyAndAttackNomads OUT")

    def getNomadAttackFormation(self, sourceCastle, level, adiResponse, S_key, commanderName, gateNegation=0, wallNegation=0):
        message, flankCount, middleCount = self.doGetNomadAttackFormation(S_key, commanderName, gateNegation, wallNegation)
        message = self.fillNomadAttackWithAvailableTroops(sourceCastle, level, adiResponse, message, flankCount, middleCount)
        totals = self.calculate_tool_counts(message)
        return message, totals

    def fillNomadAttackWithAvailableTroops(self, sourceCastle, level, adiResponse, message, flankCount, middleCount):
        log("fillNomadAttackWithAvailableTroops IN")

        struct = json.loads(message)
        rangeTroops = {key: value for (key, value) in adiResponse['gui']['I'] if self.is_range_troop(key)}
        meleeTroops = {key: value for (key, value) in adiResponse['gui']['I'] if self.is_melee_troop(key)}

        pretty_print(rangeTroops, 'rangeTroops')
        pretty_print(meleeTroops, 'meleeTroops')

        for item in adiResponse['gui']['I']:
            if self.is_range_troop(item[0]):
                rangeTroops[item[0]] = item[1]
                log("Range troops {:d}, name {} current count {:d}".format(item[0], tools_and_troops_to_string(item[0]), item[1]))
            elif self.is_melee_troop(item[0]):
                meleeTroops[item[0]] = item[1]
                log("Range troops {:d}, name {} current count {:d}".format(item[0], tools_and_troops_to_string(item[0]), item[1]))
            else:
                log("Non classified tool/troops {:d}, name {} current count {:d}".format(item[0], tools_and_troops_to_string(item[0]), item[1]))

        builder = NomadAttackFormationBuilder(struct, rangeTroops, meleeTroops, flankCount, middleCount)
        struct = builder.buildFormation()
        pretty_print(struct, "BUILDER RETURNED")

        if self.useKhanChests(level):
            chestCount = 0
            for item in adiResponse['gui']['I']:
                if item[0] == TOOL_TYPE_KHAN_CHEST:
                    chestCount = item[1]
                    break
            # if TOOL_TYPE_KHAN_CHEST in adiResponse['gui']['I']:
            #     chestCount = adiResponse['gui']['I'][TOOL_TYPE_KHAN_CHEST]

            self.fillWithKhanChests(struct, chestCount)
            pretty_print(struct, "AFTER KHAN CHESTS")
        elif self.isUseKhanForMidas(level):
            self.useKhanForMidas(struct, level, adiResponse)

        message = self.correctWallOrderInWave(struct)
        log("fillNomadAttackWithAvailableTroops OUT, message=" + xstr(message))
        return message

    def getKhanChestCountsForMidas(self):
        return {81:10, 82:9, 83:9, 84:8, 85:6, 86:5, 87:4, 88:3, 89:3, 90:2}

    def useKhanForMidas(self, struct, level, adiResponse):
        chestCount = 0
        for item in adiResponse['gui']['I']:
            if item[0] == TOOL_TYPE_KHAN_CHEST:
                chestCount = item[1]
                break

        requiredChestCount = self.getKhanChestCountsForMidas()[level]
        if chestCount >= requiredChestCount:
            self.fillWithKhanChests(struct, requiredChestCount)

    def correctWallOrderInWave(self, struct):
        if struct is not None:
            newWaves = []
            for wave in struct:
                newWave = OrderedDict()
                newWave["L"] = wave['L']
                newWave["R"] = wave['R']
                newWave["M"] = wave['M']
                newWaves.append(newWave)

            message = json.dumps(newWaves)
            return removeAllBlanks(message)
        return None

    def isUseKhanForMidas(self, level):
        return self.args.use_khan_chests_for_midas or False

    def useKhanChests(self, level):
        if level == 90:
            return self.args.use_khan_chests

    def fillWithKhanChests(self, struct, chestCount):
        if struct is None:
            return
        # for idx, wave in enumerate(struct, 1):
        for idx, wave in enumerate(struct):
            log("fillWithKhanChests wave IDX {:d} remaining chest count {:d}".format(idx, chestCount))
            if idx > 0:
                if chestCount < 40:
                    toUse = chestCount
                else:
                    toUse = 40

                if toUse > 0:
                    wave['L']['T'].append([1, toUse])
                    chestCount -= toUse

                if chestCount < 40:
                    toUse = chestCount
                else:
                    toUse = 40

                if toUse > 0:
                    wave['R']['T'].append([1, toUse])
                    chestCount -= toUse

                if chestCount < 50:
                    toUse = chestCount
                else:
                    toUse = 50

                if toUse > 0:
                    wave['M']['T'].append([1, toUse])
                    chestCount -= toUse

    # TODO move this to an util class ... maybe even put this in the attack command

    def doGetNomadAttackFormation(self, S_key, commanderName, gateNegation=0, wallNegation=0):
        index = 0
        tools = []
        for flank in S_key:
            pretty_print(flank, 'flank')
            rams = 0
            ladders = 0
            shields = 0

            bombCount = 0
            arrowCount = 0
            rangeDefender = 0
            meleeDefender = 0
            for defender in flank: # defender is troop or tool
                pretty_print(defender, 'defender')
                if NOMAD_DEBUG:
                    print ("Flank {} {}={:d}".format(Client.flankNameFromIndex(index), tools_and_troops_to_string(defender[0]), defender[1]))
                if defender[0] == TOOL_TYPE_BODKIN_ARROWHEADS:
                    arrowCount = arrowCount + 1
                elif defender[0] == TOOL_TYPE_LIME_POWDER_BOMB:
                    bombCount = bombCount + 1
                elif defender[0] == TROOP_TYPE_SPEAR_THROWER:
                    rangeDefender = rangeDefender + defender[1]
                elif defender[0] == TROOP_TYPE_LANCE:
                    meleeDefender = meleeDefender + defender[1]
                else:
                    print ("TOOL OR TROOP TYPE {:d} {}".format(defender[0], tools_and_troops_to_string(defender[0])))


            if index < 3:
                if NOMAD_DEBUG:
                    print ("-" * 40)
                    print ("Flank {} arrow count={:d}, lime bomb={:d}, range defense={:d}, melee defense={:d}".format(Client.flankNameFromIndex(index), arrowCount, bombCount, rangeDefender, meleeDefender))
                    print ("-" * 40)

                if arrowCount == 0:    # 119% range boost
                    shields = 24
                elif arrowCount == 1:  # 169% range boost
                    shields = 34
                elif arrowCount == 2:  # 219% range boost
                    shields = 40
                elif arrowCount == 3:  # 269% range boost
                    shields = 40
                else:
                    pass

                # print ">>>>>>>>>>> SHIELDS " + str(shields)

                # Don't send shields if less than 10 range defenders
                if rangeDefender < 10:
                    shields = 0
                elif rangeDefender <= 15: # Only send 24 shields max if between 10 and 15 range troops
                    if shields > 24:
                        shields = 24

                if index == 1:  # Front
                    rams = 12
                    rams = rams - (gateNegation / 10)
                    remainder = gateNegation ^ 10
                    # TODO if there is room for one more ram and the remainder of (gateNegation/10) is not 0 then add a ram

                    # If shields and rams would be more than max allowed then always Make room for rams
                    if shields + rams > 50:  # if shields > 34:
                        if NOMAD_DEBUG:
                            print ("shields + rams > 50 --> {:d} reducing shields to {:d}".format(shields + rams, 50 - rams))
                        shields = shields - rams
                        shields = 50 - rams
                    ladders = 50 - shields - rams

                    if ladders > (13 - wallNegation / 10):
                        ladders = (13 - wallNegation / 10)

                    if rams + shields + ladders < 50 and remainder > 0:
                        if NOMAD_DEBUG:
                            print ("Incrementing rams by one tool total={:d} remainder={}".format((rams + shields + ladders), str(remainder)))
                        rams = rams + 1

                    # Don't let ladder count remain negative
                    if ladders < 0:
                        ladders = 0
                elif index == 0 or index == 2:
                    ladders = 40 - shields
                    if ladders > 13:  # Max it at 13
                        ladders = 13

                    if ladders > (13 - wallNegation / 10):
                        ladders = (13 - wallNegation / 10)

                # index 3 and 4 are always empty

                if index == 1:  # Front
                    if NOMAD_DEBUG:
                        print ("Would use {:d} ladders, {:d} shields, {:d} rams on front".format(ladders, shields, rams))
                    if rams + shields + ladders > 50:
                        print ("BUG TOO MANY TOOLS ON FRONT\n" * 30)
                elif index == 0 or index == 2:
                    flankName = "Left"
                    if index == 2:
                        flankName = "Right"
                    if NOMAD_DEBUG:
                        print ("Would use {:d} ladders, {:d} shields {} flank".format(ladders, shields, flankName))
                    if shields + ladders > 40:
                        print ("BUG TOO MANY TOOLS ON " + flankName + "\n" * 30)
                if NOMAD_DEBUG:
                    print ("=" * 40)

            first = True
            toolsOnFlank = ""
            if ladders > 0:
                if not first:
                    toolsOnFlank = toolsOnFlank + ","
                toolsOnFlank = toolsOnFlank + "[{:d},{:d}]".format(TOOL_TYPE_LADDER, ladders)
                first = False
            if shields > 0:
                if not first:
                    toolsOnFlank = toolsOnFlank + ","
                toolsOnFlank = toolsOnFlank + "[{:d},{:d}]".format(TOOL_TYPE_MANTLET, shields)
                first = False
            if rams > 0:
                if not first:
                    toolsOnFlank = toolsOnFlank + ","
                toolsOnFlank = toolsOnFlank + "[{:d},{:d}]".format(TOOL_TYPE_BATTERING_RAM, rams)
            tools.append(toolsOnFlank)

            index += 1

        rangeOffense = TROOP_TYPE_ELITE_CROSSBOWMAN
        flankCount = self.getFlankTroopCountForCommander(commanderName)
        middleCount = self.getFrontTroopCountForCommander(commanderName)

        values = {'leftTroops':rangeOffense, 'middleTroops':rangeOffense, 'rightTroops':rangeOffense, 'leftTools':tools[0],
                  'middleTools':tools[1], 'rightTools':tools[2], 'flankCount':flankCount, 'middleCount':middleCount}

        firstWave = '{{"L":{{"U":[[{leftTroops!s},{flankCount!s}]],"T":[{leftTools}]}},' \
                      '"R":{{"U":[[{rightTroops!s},{flankCount!s}]],"T":[{rightTools}]}},' \
                      '"M":{{"U":[[{middleTroops!s},{middleCount!s}]],"T":[{middleTools}]}}}},'.format(**values)

        lootingWaves = '{"L":{"U":[],"T":[]},"R":{"U":[],"T":[]},"M":{"U":[],"T":[]}},' \
                       '{"L":{"U":[],"T":[]},"R":{"U":[],"T":[]},"M":{"U":[],"T":[]}},' \
                       '{"L":{"U":[],"T":[]},"R":{"U":[],"T":[]},"M":{"U":[],"T":[]}}'

        message = '[' + firstWave + lootingWaves + ']'
        return message, flankCount, middleCount

    def applyTimeSkip(self, destX, destY, kingdomID, hours, minutes, seconds):
        console("Time to skip {:d}:{:d}:{:d}".format(hours, minutes, seconds))
        # log("Time to skip {:d}:{:d}:{:d}".format(hours, minutes, seconds))

        timeSkips = getPlayer().timeSkips
        console("Time skips=[1m={:d}, 5m={:d}, 10m={:d}, 30m={:d}, 1h={:d}, 5h={:d}, 24h={:d}]".format(timeSkips[0], timeSkips[1], timeSkips[2], timeSkips[3], timeSkips[4], timeSkips[5], timeSkips[6]))

        if hours >= 5 or (hours == 4 and minutes >= 30):
            lessThan5H = (hours == 4)

            # Start using 1h skips when 5h skips falls below 80 and there is 10 more 1h skips than 5h skips
            if timeSkips[5] < 80 and timeSkips[4] - timeSkips[5] > 10:
                boostType = TIME_BOOST_TYPE_1H
                for x in range(0, hours):
                    self.runDelayed(ApplyTimeBoost(destX, destY, kingdomID, boostType))
                    timeSkips[4] -= 1
                    hours -= 1

                # IF 4h30 or more but less than 5h then we've cleared the entire span
                if lessThan5H:
                    return
            else:
                boostType = TIME_BOOST_TYPE_5H
                self.runDelayed(ApplyTimeBoost(destX, destY, kingdomID, boostType))
                timeSkips[5] -= 1
                hours -= 5

        if hours >= 1 and hours <= 4:
            boostType = TIME_BOOST_TYPE_1H
            for x in range(0, hours):
                self.runDelayed(ApplyTimeBoost(destX, destY, kingdomID, boostType))
                timeSkips[4] -= 1
                hours -= 1

        remainder = minutes
        if minutes >= 50:
            boostType = TIME_BOOST_TYPE_1H
            self.runDelayed(ApplyTimeBoost(destX, destY, kingdomID, boostType))
            timeSkips[4] -= 1
            remainder -= 60
            return

        elif minutes >= 30:
            boostType = TIME_BOOST_TYPE_30M
            self.runDelayed(ApplyTimeBoost(destX, destY, kingdomID, boostType))
            remainder -= 30
            timeSkips[3] -= 1

        if remainder >= 10:
            boostType = TIME_BOOST_TYPE_10M
            for x in range(0, int(remainder / 10)):
                self.runDelayed(ApplyTimeBoost(destX, destY, kingdomID, boostType))
                timeSkips[2] -= 1
                remainder -= 10

        if remainder >= 5:
            boostType = TIME_BOOST_TYPE_5M
            for x in range(0, int(remainder / 5)):
                self.runDelayed(ApplyTimeBoost(destX, destY, kingdomID, boostType))
                timeSkips[1] -= 1
                remainder -= 5

        if remainder >= 1:
            boostType = TIME_BOOST_TYPE_1M
            for x in range(0, int(remainder / 1)):
                timeSkips[0] -= 1
                self.runDelayed(ApplyTimeBoost(destX, destY, kingdomID, boostType))
                remainder -= 5

        if seconds > 0:
            boostType = TIME_BOOST_TYPE_1M
            self.runDelayed(ApplyTimeBoost(destX, destY, kingdomID, boostType))

    @staticmethod
    def flankNameFromIndex(index):
        if index == 0:
            return "Left"
        if index == 1:
            return "Front"
        if index == 2:
            return "Right"
        if index == 3:
            return "Keep"
        return "UNKNOWN FLANK"


    # TODO this is a hack, we should be able to deduce the amount of troops that can be put on the flanks or in front based on the
    # target, player level and commander equipment and gems ... but this wont be the case any time soon so we do it manually
    def getFlankTroopCountForCommander(self, commanderName):
        return 64

    def getFrontTroopCountForCommander(self, commanderName):
        return 156

    def doSpyBaron(self, sourceCastle, targetX, targetY, kid, speed, isBerimond=False):
        """
        Assumes timeTillNextAttack is 0, must verified by caller prior
        """
        log("doSpyBaron IN, kid={}, speed={}".format(str(kid), str(speed)))

        srcCastleID = sourceCastle._id

        # print " is level {:d} in skipLevel size={}".format(level, str(skipLevel), skipLevel)
        cmd = self.runDelayed(CheckAvailableSpies(targetX, targetY, kid))
        if cmd.availableSpies > 0:
            if not isBerimond:
                # SendSpies
                cmd = self.runDelayed(SendSpies(targetX, targetY, kid, srcCastleID, cmd.availableSpies, 100, speed))
            else:
                cmd = self.runDelayed(SendSpiesBerimond(targetX, targetY, srcCastleID, cmd.availableSpies, 100))
            pretty_print(cmd)
        else:
            console("NO spies available!")

        log("doSpyBaron OUT")

    def attackBarons(self, buyTools, kingdoms=('Ice', 'Fire', 'Sands')):
        kingdoms = [s.lower() for s in kingdoms]

        player = getPlayer()
        if  kingdom_to_string(KINGDOM_GREEN).lower() in kingdoms:
            self.attackBaronsInGreen(player, buyTools)
        if  kingdom_to_string(KINGDOM_ICE).lower() in kingdoms:
            self.attackBaron(player._iceCastle, KINGDOM_ICE, buyTools)
        if  kingdom_to_string(KINGDOM_SANDS).lower() in kingdoms:
            self.attackBaron(player._sandCastle, KINGDOM_SANDS, buyTools)
        if  kingdom_to_string(KINGDOM_FIRE).lower() in kingdoms:
            self.attackBaron(player._fireCastle, KINGDOM_FIRE, buyTools)

    def attackBaronsInGreen(self, player, buyTools):
        print (">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> attackBaronsInGreen IN")
        self.printDebug_For_AttackBaronsInGreen(player)
        print (">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> get player")
        player = getPlayer()
        mc = player.getCastle(KINGDOM_GREEN)
        sourceCastle = mc
        print (">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> call attack baron with green")
        self.attackBaron(sourceCastle, KINGDOM_GREEN, buyTools)
        print (">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> attackBaronsInGreen OUT")


    TILE_SIZE = 6  # Assume a 6x6 square tile

    def printDebug_For_AttackBaronsInGreen(self, player):

        print ("***************************************** attackBaronsInGreen")
        cmd = self.runDelayed(JumpToWorld(KINGDOM_GREEN))
        # All Nomads are returned in this command
        for elem in cmd.allCastlesOnMap:
            if elem[0] == CASTLE_TYPE_MONUMENT:
                console(">>>>>>>>>>>>>>>> found monument at: {:d},{:d}".format(elem[1], elem[2]))
            elif elem[0] == CASTLE_TYPE_FORTRESS:
                console(">>>>>>>>>>>>>>>> found fortress at: {:d},{:d}".format(elem[1], elem[2]))
                pretty_print(elem)
            elif elem[0] == CASTLE_TYPE_RBC:
                console(">>>>>>>>>>>>>>>> found barron at: {:d},{:d}".format(elem[1], elem[2]))
                pretty_print(elem)
            elif elem[0] == CASTLE_TYPE_FOREIGN_LEGION:
                console(">>>>>>>>>>>>>>>> found FL at: {:d},{:d}".format(elem[1], elem[2]))
                pretty_print(elem)
            elif elem[0] == CASTLE_TYPE_NOMAD:
                console(">>>>>>>>>>>>>>>> found NOMAD at: {:d},{:d}".format(elem[1], elem[2]))
                pretty_print(elem)
            elif elem[0] == CASTLE_TYPE_HUMAN_MAIN:
                console(">>>>>>>>>>>>>>>> found HUMAN MAIN at: {:d},{:d}".format(elem[1], elem[2]))
                pretty_print(elem)
            elif elem[0] == CASTLE_TYPE_HUMAN_OP:
                console(">>>>>>>>>>>>>>>> found HUMAN MAIN at: {:d},{:d}".format(elem[1], elem[2]))
            elif elem[0] == CASTLE_TYPE_ROBBER_BARON_KING:
                console(">>>>>>>>>>>>>>>> found ROBBER BARRON KING at: {:d},{:d}".format(elem[1], elem[2]))
                pretty_print(elem)
            else:
                console(">>>>>>>>>>>>>>>> found UNKNOWN TYPE {:d} at: {:d},{:d}".format(elem[0], elem[1], elem[2]))
                pretty_print(elem)

        if False:
            for greenCastle in player.getGreenCastles():
                # If you land on an area where there is a nomad it'll show up ... ABOVE IS BETTER ^^^^^^^^^^^^^^^^^^^^^
                print ("***************************************** c")
                x = greenCastle._x
                y = greenCastle._y
                endX = x + self.TILE_SIZE
                endY = y + self.TILE_SIZE
                cmd = GetMap(KINGDOM_GREEN, x, y, endX, endY)
                self.runNoDelay(cmd)
                pretty_print(cmd.result)

                # for elem in cmd.allEntries:
                for elem in cmd.result:
                    if elem[0] == CASTLE_TYPE_MONUMENT:
                        console(">>>>>>>>>>>>>>>> found monument at: {:d},{:d}".format(elem[1], elem[2]))
                    elif elem[0] == CASTLE_TYPE_FORTRESS:
                        console(">>>>>>>>>>>>>>>> found fortress at: {:d},{:d}".format(elem[1], elem[2]))
                        pretty_print(elem)
                    elif elem[0] == CASTLE_TYPE_RBC:
                        console(">>>>>>>>>>>>>>>> found barron at: {:d},{:d}".format(elem[1], elem[2]))
                        pretty_print(elem)
                    elif elem[0] == CASTLE_TYPE_FOREIGN_LEGION:
                        console(">>>>>>>>>>>>>>>> found FL at: {:d},{:d}".format(elem[1], elem[2]))
                        pretty_print(elem)
                    elif elem[0] == CASTLE_TYPE_NOMAD:
                        console(">>>>>>>>>>>>>>>> found NOMAD at: {:d},{:d}".format(elem[1], elem[2]))
                        pretty_print(elem)
                    elif elem[0] == CASTLE_TYPE_HUMAN_MAIN:
                        console(">>>>>>>>>>>>>>>> found HUMAN MAIN at: {:d},{:d}".format(elem[1], elem[2]))
                        pretty_print(elem)
                    elif elem[0] == CASTLE_TYPE_HUMAN_OP:
                        console(">>>>>>>>>>>>>>>> found HUMAN MAIN at: {:d},{:d}".format(elem[1], elem[2]))
                        pretty_print(elem)
                    elif elem[0] == CASTLE_TYPE_ROBBER_BARON_KING:
                        console(">>>>>>>>>>>>>>>> found ROBBER BARRON KING at: {:d},{:d}".format(elem[1], elem[2]))
                        pretty_print(elem)
                    else:
                        console(">>>>>>>>>>>>>>>> found UNKNOWN TYPE {:d} at: {:d},{:d}".format(elem[0], elem[1], elem[2]))
                        pretty_print(elem)

    def attackBaron(self, sourceCastle, kid, buyTools):
        allCastlesOnMap = self.jumpToWorld(sourceCastle, kid)
        time.sleep(random.randint(5, 8)) # add artificial lag to simulate app
        if allCastlesOnMap is not None and len(allCastlesOnMap) > 0:
            self.doAttackBaron(sourceCastle, kid, allCastlesOnMap, sourceCastle.getMaxCoinSpeed(), buyTools)

    def doAttackBaron(self, sourceCastle, kid, allCastlesOnMap, speed, buyTools=False):
        log("doAttackBaron IN, kid={}, speed={}".format(str(kid), str(speed)))

        foundTarget = False
        targetDataCommand = None
        troopsExcludedFromBaronAttack = self.getBaronTroopExclusionList(kid, sourceCastle)
        troopsExcludedFromBeingBurners = self.getTroopsExcludedFromBeingBurners(kid, sourceCastle)
        troopsToUseAsAttackers = self.getTroopsToUseAsAttackersForBaron(sourceCastle)
        troopsToUseAsBurners = self.getTroopsToUseAsBurners(sourceCastle)

        sortedPayload = self.sortBaronList(allCastlesOnMap, sourceCastle, not self.args.favor_low_level_barons)
        self.printBaronList(sortedPayload, sourceCastle)
        skipLevel = []  # Used to avoid resolving a commander for a specific level more than once when the first attempt failed

        for tower in sortedPayload:
            level = int(tower[4])
            # print " is level {:d} in skipLevel size={}".format(level, str(skipLevel), skipLevel)
            if int(tower[5]) <= 0 and level not in skipLevel:
                distance = tower[len(tower) -1]
                if int(distance) >= 30:
                    console("Baron at {:d},{:d} is too far to attack (distance {: >4.1f})".format(tower[1], tower[2], distance))
                    continue

                if self.isAttackTravelingTo(kid, tower[1], tower[2]):
                    console("Attack already travelling to {:d},{:d} (level {:d})".format(tower[1], tower[2], level))
                    continue

                foundTarget = True
                commanderName, commanderID = self.getCommanderForAttack(sourceCastle, kid, tower)
                if commanderName is None:
                    console("No commander configured or available for RBC level {:d}".format(level))
                    skipLevel.append(level)
                    continue

                formationTemplate = self.getFormationForBaronAttack(kid, commanderID, commanderName, level)
                if formationTemplate is None:
                    console("No attack formation configured for RBC level {:d}".format(level))
                    skipLevel.append(level)
                    continue
                else:
                    console("Attack formation found for RBC level {:d}".format(level))

                # Only fetch it once otherwise we'll run into the usual network issues,
                # we don't really need to call this more than once unless we wanted to sed
                # more than 1 attack in the same land from the same castle
                if targetDataCommand is None:
                    # Target data response also contains what is available at the castle, this is the part we're most interested in.
                    # We don't automate based on spy reports but it would be possible since an existing spy report would be referenced in the Target data response
                    # OR is it that the response would contain the defensive formation present t the castle <<< This is how nomads work
                    targetDataCommand = self.runDelayed(GetTargetData(sourceCastle._x, sourceCastle._y, tower[1], tower[2], kid))


                # formation = self.fillBaronAttackWithAvailableTroops(targetDataCommand.result, troopsExcludedFromBaronAttack, troopsExcludedFromBeingBurners, troopsToUseAsBurners, formationTemplate)
                useAttackTroopAsBurnerOfLastResort = self.isAttackTroopBurnerOfLastResort()
                mustFillAllWaves = self.mustFillAllWavesForBaronAttack()
                formation = self.fillBaronAttackWithAvailableTroops2(targetDataCommand.result, troopsToUseAsAttackers, troopsToUseAsBurners, useAttackTroopAsBurnerOfLastResort, mustFillAllWaves, formationTemplate)
                if formation is None:
                    console("Troop or tool totals are INSUFFICIENT for level {}".format(str(level)))
                    skipLevel.append(level)
                    continue

                totals = self.calculate_tool_counts(formation)
                missing, troopsMissing, toolsMissing = self.newCheckTotals(totals, targetDataCommand.result)

                if buyTools:
                    # Buy all missing tools (only if there are enough troops)
                    if toolsMissing and not troopsMissing:
                        missingTools = {k: v for k, v in missing.iteritems() if is_tool(k)}
                        if self.quickBuyAllToolsFromArmorer(sourceCastle, missingTools):
                            for k in missing.keys():
                                del missing[k]
                        # Jump outside of castle (quick buy forced a jump within a castle) ... might not be mandatory not sure
                        self.runDelayed(JumpToWorld(kid))

                if len(missing) > 0:
                    console("Troop or tool totals are INSUFFICIENT for level {}".format(str(level)))
                    skipLevel.append(level)
                    continue

                console("Attacking barron level {:d} at [{:d},{:d}] with commander '{}'".format(level, tower[1], tower[2], commanderName))
                log("doAttack format={}".format(str(formation)))
                self.printTroopToolTotalsInAttack(totals)
                self.runDelayed(Pin())
                self.runDelayed(Pin())
                if not self.args.dry_run:
                    self.runDelayed(AttackCommand(kid, formation, sourceCastle._x, sourceCastle._y, tower[1], tower[2], commanderID, speed))
                else:
                    console("DRY RUN ONLY!!!")
                break

        if not foundTarget:
            console("Did not find a suitable target to attack")

        log("doAttackBaron OUT")

    def fillBaronAttackWithAvailableTroops(self, adiResponse, troopsExcludedFromBaronAttack, troopsExcludedFromBeingBurners, troopsToUseAsBurners, formationTemplate):
        """
        Option 1: Use a base list which is good for both burners and attackers and provide 2 exclusion lists to see where to exclude the troop type from
        troopsExcludedFromBaronAttack:   Excluded from attack but not burners
        troopsExcludedFromBeingBurners:  Excluded from burners but not attack
        To entirely exclude a troop type it needs to be part of both lists

        Options 2: Use a base list which is good for both burners and attackers and provide a attacker exclusion list and one explicit burner list
        troopsExcludedFromBaronAttack:   Excluded from attack and burners except if explicitly listed as a burner
        troopsToUseAsBurners: Eligible to be used as a burner no matter if it is excluded from being an attacker or not

        So if in
        Attacker=Yes, Burner=No   --> Attacker only
        Attacker=No,  Burner=No   --> Not used
        Attacker=Yes, Burner=Yes  --> Attacker and burner
        Attacker=No,  Burner=Yes  --> Burner only
        Extended possibility:
        Attacker=Yes, Burner=None --> Attacker and burner
        Attacker=No,  Burner=None --> Not used

        Option 3:
        Explicit list of attackers
        Explicit list of burners

        Option 4 (shitty one IMPLEMENTED HERE!)
        Base list
        List of troops that cannot be part of either attacker or burner (this makes the entire pool of available troops)
        List of troops that cannot be used as burners (so only attackers)
        DRAWBACK: This strategy does not allow you to send burners that are not attackers as well

        :param adiResponse:
        :param troopsExcludedFromBaronAttack: Black list of troops that cannot be sent to attack barons (but could be used as burners depending on combination)
        :param troopsExcludedFromBeingBurners: Optional Black list of troop types for burners (this is mutually exclusive with troopsToUseAsBurners)
        :param troopsToUseAsBurners: Optional White list of troop types for burners (this is mutually exclusive with troopsExcludedFromBeingBurners)
        :param formationTemplate:
        :return:
        """
        log("fillBaronAttackWithAvailableTroops IN")

        # rangeTroops = {key: value for (key, value) in adiResponse['gui']['I'] if self.is_range_troop(key, TARGET_TYPE_RBC)}
        # meleeTroops = {key: value for (key, value) in adiResponse['gui']['I'] if self.is_melee_troop(key, TARGET_TYPE_RBC)}
        rangeTroops = {}
        meleeTroops = {}
        burners = {}

        pretty_print(rangeTroops, 'rangeTroops')
        pretty_print(meleeTroops, 'meleeTroops')

        for item in adiResponse['gui']['I']:
            # if item[0] in troopsToUseAsBurners:
            #     burners[item[0]] = item[1]
            if item[0] in troopsExcludedFromBaronAttack:
                log("Removing {:d}, name {} from eligible attack troops".format(item[0], tools_and_troops_to_string(item[0])))
                continue
            if self.is_range_troop(item[0]):
                rangeTroops[item[0]] = item[1]
                log("Range troops {:d}, name {} current count {:d}".format(item[0], tools_and_troops_to_string(item[0]), item[1]))
            elif self.is_melee_troop(item[0]):
                meleeTroops[item[0]] = item[1]
                log("Melee troops {:d}, name {} current count {:d}".format(item[0], tools_and_troops_to_string(item[0]), item[1]))
            else:
                if not is_tool(item[0]):
                    log("Non classified or excluded from attack {:d}, name {} current count {:d}".format(item[0], tools_and_troops_to_string(item[0]), item[1]))

        struct = json.loads(formationTemplate)
        # builder = BaronAttackFormationBuilder(struct, rangeTroops, meleeTroops, troopsExcludedFromBeingBurners, burners)
        builder = BaronAttackFormationBuilder(struct, rangeTroops, meleeTroops, troopsExcludedFromBeingBurners)
        struct = builder.buildFormation()
        pretty_print(struct, "BUILDER RETURNED")
        formation = self.correctWallOrderInWave(struct)

        log("fillBaronAttackWithAvailableTroops OUT, message=" + xstr(formation))
        return formation

    def fillBaronAttackWithAvailableTroops2(self, adiResponse, troopsToUseAsAttackers, troopsToUseAsBurners, useAttackTroopAsBurnerOfLastResort, mustFillAllWaves, formationTemplate):
        """
        :param adiResponse:
        :param troopsToUseAsAttackers: Explicit list of attackers
        :param troopsToUseAsBurners: Explicit list of burners
        :param formationTemplate:
        :return:
        """
        log("fillBaronAttackWithAvailableTroops IN")

        struct = json.loads(formationTemplate)
        rangeTroops = {key: value for (key, value) in adiResponse['gui']['I'] if self.is_range_troop(key, TARGET_TYPE_RBC)}
        meleeTroops = {key: value for (key, value) in adiResponse['gui']['I'] if self.is_melee_troop(key, TARGET_TYPE_RBC)}
        burners = {key: value for (key, value) in adiResponse['gui']['I'] if key in troopsToUseAsBurners}

        pretty_print(rangeTroops, 'rangeTroops')
        pretty_print(meleeTroops, 'meleeTroops')
        pretty_print(burners, 'burners')

        for item in adiResponse['gui']['I']:
            if item[0] in troopsToUseAsBurners:
                burners[item[0]] = item[1]
                log("Burner {:d}, name {} current count {:d}".format(item[0], tools_and_troops_to_string(item[0]), item[1]))
            if item[0] in troopsToUseAsAttackers:
                if self.is_range_troop(item[0]):
                    rangeTroops[item[0]] = item[1]
                    log("Range troops {:d}, name {} current count {:d}".format(item[0], tools_and_troops_to_string(item[0]), item[1]))
                elif self.is_melee_troop(item[0]):
                    meleeTroops[item[0]] = item[1]
                    log("Melee troops {:d}, name {} current count {:d}".format(item[0], tools_and_troops_to_string(item[0]), item[1]))
            else:
                if not is_tool(item[0]):
                    log("Non classified or excluded from attack {:d}, name {} current count {:d}".format(item[0], tools_and_troops_to_string(item[0]), item[1]))

        builder = BaronAttackFormationBuilder2(struct, rangeTroops, meleeTroops, burners, useAttackTroopAsBurnerOfLastResort, mustFillAllWaves)
        struct = builder.buildFormation()
        pretty_print(struct, "BUILDER RETURNED")
        formation = self.correctWallOrderInWave(struct)

        log("fillBaronAttackWithAvailableTroops OUT, message=" + xstr(formation))
        return formation

    def is_range_troop(self, troopType, targetType=TARGET_TYPE_NOMAD):
        if targetType == TARGET_TYPE_NOMAD:
            types = self.getNomadAttackRangeTroops()
        elif targetType == TARGET_TYPE_RBC:
            types = self.getBaronAttackRangeTroops()
        else:
            raise Exception("No valid type specified")
        return troopType in types

    def is_melee_troop(self, troopType, targetType=TARGET_TYPE_NOMAD):
        if targetType == TARGET_TYPE_NOMAD:
            types = self.getNomadAttackMeleeTroops()
        elif targetType == TARGET_TYPE_RBC:
            types = self.getBaronAttackMeleeTroops()
        else:
            raise Exception("No valid type specified")
        return troopType in types

    @classmethod
    def getRangeTroopListNoDemons(cls):
        return [TROOP_TYPE_KINGSGUARD_BOW, TROOP_TYPE_ELITE_CROSSBOWMAN,
                TROOP_TYPE_VET_CROSSBOWMAN, TROOP_TYPE_VET_HEAVY_CROSSBOWMAN,
                TROOP_TYPE_VET_SLINGSHOT, TROOP_TYPE_SLINGSHOT,
                TROOP_TYPE_TRAVELING_CROSSBOWMAN,
                TROOP_TYPE_RENEGADE_NORSEMAN_BOWMAN,
                TROOP_TYPE_RENEGADE_DESERT_BOWMAN,
                TROOP_TYPE_RENEGADE_CULTIST_BOWMAN,
                TROOP_TYPE_RENEGADE_ARROW_THROWER,
                TROOP_TYPE_IMPERIAL_BOWMAN,
                TROOP_TYPE_FROST_BOWMAN,
                TROOP_TYPE_MASTER_FROST_BOWMAN]

    @classmethod
    def getMeleeTroopListNoDemons(cls):
        return [TROOP_TYPE_ELITE_KNIGHT, TROOP_TYPE_KINGSGUARD_KNIGHT, TROOP_TYPE_VET_MACEMAN, TROOP_TYPE_VET_TWO_HANDED_SWORDSMAN,
                TROOP_TYPE_TRAVELING_KNIGHT,
                TROOP_TYPE_MARAUDER, TROOP_TYPE_VET_MARAUDER,
                TROOP_TYPE_SABER_CLEAVER, TROOP_TYPE_VET_SABER_CLEAVER,
                TROOP_TYPE_RENEGADE_NORSEMAN_WARRIOR,
                TROOP_TYPE_RENEGADE_SABER_WARRIOR,
                TROOP_TYPE_RENEGADE_CULTIST_WARRIOR,
                TROOP_TYPE_RENEGADE_SAI_WARRIOR,
                TROOP_TYPE_PYROMANIAC, TROOP_TYPE_VET_PYROMANIAC,
                TROOP_TYPE_IMPERIAL_GUARDSMAN,
                TROOP_TYPE_BONE_HUNTRESS,
                TROOP_TYPE_MASTER_FROST_BOWMAN]

    def getNomadAttackRangeTroops(self):
        if self._nomadAttackRangeTroops is None:
            self._nomadAttackRangeTroops = self.initNomadAttackRangeTroops()
        return self._nomadAttackRangeTroops

    def initNomadAttackRangeTroops(self):
        types = self.getRangeTroopListNoDemons()
        if self.useRangeDemonsForNomads():
            types = types + [TROOP_TYPE_DEATHLY_HORROR, TROOP_TYPE_VET_DEATHLY_HORROR]
        return types

    def getNomadAttackMeleeTroops(self):
        if self._nomadAttackMeleeTroops is None:
            self._nomadAttackMeleeTroops = self.initNomadAttackMeleeTroops()
        return self._nomadAttackMeleeTroops

    def initNomadAttackMeleeTroops(self):
        return self.getMeleeTroopListNoDemons() + [TROOP_TYPE_DEMON_HORROR, TROOP_TYPE_VET_DEMON_HORROR]

    def getBaronAttackRangeTroops(self):
        if self._rbcAttackRangeTroops is None:
            self._rbcAttackRangeTroops = self.initBaronAttackRangeTroops()
        return self._rbcAttackRangeTroops

    def initBaronAttackRangeTroops(self):
        types = self.getRangeTroopListNoDemons()
        if self.useDemonsForBarons():
            types = types + [TROOP_TYPE_DEATHLY_HORROR, TROOP_TYPE_VET_DEATHLY_HORROR]
        return types

    def getBaronAttackMeleeTroops(self):
        if self._rbcAttackMeleeTroops is None:
            self._rbcAttackMeleeTroops = self.initBaronAttackMeleeTroops()
        return self._rbcAttackMeleeTroops

    def initBaronAttackMeleeTroops(self):
        types = self.getMeleeTroopListNoDemons()
        if self.useDemonsForBarons():
            types = types + [TROOP_TYPE_DEMON_HORROR, TROOP_TYPE_VET_DEMON_HORROR]
        return types

    def spyBarons(self, kingdoms=('Ice', 'Fire', 'Sands')):
        kingdoms = [s.lower() for s in kingdoms]

        player = getPlayer()
        if  kingdom_to_string(KINGDOM_GREEN).lower() in kingdoms:
            print ("Spy baron in green not supported yet")
        if  kingdom_to_string(KINGDOM_ICE).lower() in kingdoms:
            self.spyBaron(player._iceCastle, KINGDOM_ICE)
        if  kingdom_to_string(KINGDOM_SANDS).lower() in kingdoms:
            self.spyBaron(player._sandCastle, KINGDOM_SANDS)
        if  kingdom_to_string(KINGDOM_FIRE).lower() in kingdoms:
            self.spyBaron(player._fireCastle, KINGDOM_FIRE)

    def spyBaron(self, sourceCastle, kid):
        allCastlesOnMap = self.jumpToWorld(sourceCastle, kid)
        time.sleep(random.randint(5, 8)) # add artificial lag to simulate app
        if allCastlesOnMap is not None and len(allCastlesOnMap) > 0:
            self.doSpyBaronOld(sourceCastle, kid, allCastlesOnMap, sourceCastle.getMaxCoinSpeed())
        console("\n\n")

    def doSpyBaronOld(self, sourceCastle, kid, allCastlesOnMap, speed):
        log("doSpyBaronOld IN, kid={}, speed={}".format(str(kid), str(speed)))
        pretty_print(allCastlesOnMap)

        # player = getPlayer()
        # maxedBaronLevel = max_baron_level(kid)
        #
        # foundTarget = False
        # targetDataCommand = None

        sortedCastles = self.sortBaronList(allCastlesOnMap, sourceCastle, not self.args.favor_low_level_barons)
        self.printBaronList(sortedCastles, sourceCastle)
        skipLevel = []  # Used to avoid resolving a commander for a specific level more than once when the first attempt failed
        for tower in sortedCastles:
            # [2, X, Y, spy_report_id, level, time_till_attackable, kingdom_id]
            enemyType = int(tower[0])
            targetX = int(tower[1])
            targetY = int(tower[2])
            time_since_spy_report = tower[3] # = int(tower[3])
            level = int(tower[4])
            timeTillNextAttack = int(tower[5])
            srcCastleID = sourceCastle._id

            # print " is level {:d} in skipLevel size={}".format(level, str(skipLevel), skipLevel)
            if timeTillNextAttack <= 0 and (enemyType == CASTLE_TYPE_SAMURAI or enemyType == CASTLE_TYPE_FOREIGN_LEGION or enemyType == CASTLE_TYPE_NOMAD or (enemyType == CASTLE_TYPE_RBC and level not in skipLevel)):
                foundTarget = True
                commanderName, commanderID = self.getCommanderForAttack(sourceCastle, kid, tower)
                print ("commanderName is " + str(commanderName))
                if commanderName is None:
                    console("No commander configured or available for level {:d}".format(level))
                    skipLevel.append(level)
                    continue
                formation, totals = self.getBaronAttackFormation(kid, commanderID, commanderName, level)
                if formation is None:
                    print ("formation is None for level " + str(level))
                    if time_since_spy_report == -1:
                        # spy
                        cmd = self.runDelayed(CheckAvailableSpies(targetX, targetY, kid))
                        if cmd.availableSpies > 0:
                            # SendSpies
                            cmd = self.runDelayed(SendSpies(targetX, targetY, kid, srcCastleID, cmd.availableSpies, 100, SPEED_LVL_1_STABLE_COIN_BOOST))
                            pretty_print(cmd)
                    else:
                        # TODO how do you distinguish between a real spy report and a small id... perhaps the
                        print ("Level " + str(level) + " already has spy report {:d}".format(time_since_spy_report))

                        # This is not a report id so you can't get it like that just seems if you spied recently you'll have the defender formation inside the GetTargetData response

                        # if time_since_spy_report <= 25000:
                        #     cmd = self.runDelayed(ReadSpyReport(time_since_spy_report))

                        targetDataCommand = self.runDelayed(GetTargetData(sourceCastle._x, sourceCastle._y, tower[1], tower[2], kid))
                        pretty_print(targetDataCommand.result, "GetTargetData for spy tests")
                    skipLevel.append(level)
                else:
                    console("Attack formation found for RBC level {:d}".format(level))

        log("doSpyBaronOld OUT")

    @staticmethod
    def sortBaronList(allCastlesOnMap, sourceCastle, favorHighBarons=True):
        """
        When high level barons are favored (DEFAULT), sort by descending level then by distance (useful to loot more rss).
        When low level barons are favored, sort by ascending level then by distance (useful to upgrade more barons)

        :param allCastlesOnMap:
        :param sourceCastle:
        :param favorHighBarons: Favor high level barons by default
        :return: Sorted list of RBCs
        """

        # Calculate distances
        for tower in allCastlesOnMap:
            tower.append(calculateDistance(sourceCastle._x, sourceCastle._y, tower[1], tower[2]))

        if favorHighBarons:
            sortedCastles = sorted(allCastlesOnMap, cmp=Client.sortByDescendingLevelAndDistance)
        else:
            sortedCastles = sorted(allCastlesOnMap, cmp=Client.sortByAscendingLevelAndDistance)

        return sortedCastles

    @staticmethod
    def sortByAscendingLevelAndDistance(item1, item2):
        if item1[4] < item2[4]:
            return -1
        elif item1[4] > item2[4]:
            return 1

        if item1[len(item1) -1] < item2[len(item2) -1]:
            return -1
        elif item1[len(item1) -1] > item2[len(item2) -1]:
            return 1

        return 0

    @staticmethod
    def sortByDescendingLevelAndDistance(item1, item2):
        if item2[4] < item1[4]:
            return -1
        elif item2[4] > item1[4]:
            return 1

        if item1[len(item1) -1] < item2[len(item2) -1]:
            return -1
        elif item1[len(item1) -1] > item2[len(item2) -1]:
            return 1

        return 0

    @staticmethod
    def printBaronList(sortedPayload, sourceCastle):
        """
        Assumes distance has been precalculated and is the last element in the array
        :param sortedPayload:
        :param sourceCastle: No longer required, was used to calculate distance but that should be done before calling this.
        :return:
        """
        console(("-" * 21) + " Nearby barons " + ("-" * 21))
        for tower in sortedPayload:
            if len(tower) > 6:
                console("kid={:d} level={: <3d} distance={: >4.1f} x={}, y={} timeTillAttackable={:d}".format(tower[6], tower[4], tower[len(tower) - 1], str(tower[1]), str(tower[2]), 0 if tower[5] < 0 else tower[5]))
            else:
                console("SKIPPED ENTRY!!!!")
        console(("-" * 21) + " Nearby barons " + ("-" * 21))
        console(("-" * 57) + " \n")

    def getCommanderForBerimondAttack(self, sourceCastle):
        # By default use standard commander resolution algorithm
        return self.getCommanderForAttack(sourceCastle, KINGDOM_BERIMOND, None, False, False)

    def getCommanderForNomadAttack(self, sourceCastle, tower):
        # By default use standard commander resolution algorithm
        return self.getCommanderForAttack(sourceCastle, KINGDOM_GREEN, tower, False, True)

    def getCommanderForAttack(self, sourceCastle, kid, tower, isFortress=False, isNomad=False):
        # TODO for nomads we should try to automatically find the best Range+Wall commander available, not just take the first available one
        return self.findFirstFreeCommander()

    def findFirstFreeCommander(self, excluded=()):
        player = getPlayer()
        for cname, cid in player.commanders.iteritems():
            if cname in excluded:
                continue
            if self.isCommanderAvailable(cname, cid):
                return cname, cid
        return None, None

    def isCommanderAvailable(self, commanderName, commanderID):
        log("isCommanderAvailable commander '{}', id={}".format(commanderName, str(commanderID)))

        movements = getMovements()
        for movement in movements:
            # console(pretty_print(movement))
            for item in movement['M']:
                if 'UM' in item and 'L' in item['UM'] and 'VIS' in item['UM']['L']:
                    # if 'UM' in item and 'L' in item['UM'] and 'N' in item['UM']['L']: # Got key not found on 'N'
                    name = 'None'
                    if 'N' in item['UM']['L']:
                        try:
                            name = str(item['UM']['L']['N'])
                        # TODO handle commander names in unicode
                        # This list seems to contain other people's travelling commanders, if one of them uses unicode
                        # chars it causes the comparison here to blow up. For now just skip it when it blows up because I know it isn't mine.
                        except UnicodeEncodeError:
                            if isinstance(item['UM']['L']['N'], unicode):
                                # For debug only
                                log("UNICODE Commander name'{}'".format(unicode.encode(item['UM']['L']['N'], 'utf-8')))

                                uCommanderName = unicode(commanderName, 'utf-8')
                                if item['UM']['L']['N'] == uCommanderName:
                                    log(u"Commander '{}', id={} IS ALREADY TRAVELING".format(uCommanderName, str(item['UM']['L']['VIS'])))
                                    return False
                            continue

                    # log("Comparing to traveling commander '{}', id={}".format(name, str(item['UM']['L']['VIS'])))
                    # Ids don't always match and sometimes they match some other commander, names do (but happens sometimes ... guess some type of record, doesn't support names and it crashes)
                    # if str(item['UM']['L']['VIS']) == str(commanderID) or name == commanderName:
                    if name == commanderName:
                        log("Commander '{}', id={} IS ALREADY TRAVELING".format(name, str(item['UM']['L']['VIS'])))
                        return False

        log("Commander seems available for use")
        return True

    def getFormationForBaronAttack(self, kid, commanderID, commanderName, level, isFortress=False, sourceCastleInGreen=None):
        log("getFormationForBaronAttack IN, kid={:d} level={:d} commanderID={:d} commanderName={} isFortress={}".format(kid, level, commanderID, commanderName, isFortress))
        message = None
        if kid == KINGDOM_FIRE:
            message = self.getFireBaronAttackFormation(commanderID, level, isFortress)
        elif kid == KINGDOM_SANDS:
            message = self.getSandBaronAttackFormation(commanderID, level, isFortress)
        elif kid == KINGDOM_ICE:
            message = self.getIceBaronAttackFormation(commanderID, level, isFortress)
        elif kid == KINGDOM_GREEN:
            message = self.getGreenBaronAttackFormation(commanderID, level, sourceCastleInGreen)
        else:
            console("Formation Not implemented yet!")

        return removeAllBlanks(message)

    # Can be overridden by subclass to provide different formations
    #
    #
    def getFireBaronAttackFormation(self, commanderID, level, isFortress):
        return gge_fire_attack_formation.get_formation_for_fire_baron_attack(commanderID, level, isFortress)

    def getSandBaronAttackFormation(self, commanderID, level, isFortress):
        return gge_sand_attack_formation.getFormationForSandBaronAttack(commanderID, level, isFortress)

    def getIceBaronAttackFormation(self, commanderID, level, isFortress):
        return gge_ice_attack_formation.getFormationForIceBaronAttack(commanderID, level, isFortress)

    def getGreenBaronAttackFormation(self, commanderID, level, sourceCastleInGreen):
        return gge_green_attack_formation.get_formation_for_green_baron_attack(commanderID, level, sourceCastleInGreen)

    def getFortressAttackFormation(self, kid, commanderID, commanderName):
        return self.getBaronAttackFormation(kid, commanderID, commanderName, -1, True)

    def getBaronAttackFormation(self, kid, commanderID, commanderName, level, isFortress=False):
        log("getBaronAttackFormation IN, kid={:d} level={:d} commanderID={:d} commanderName={} isFortress={}".format(kid, level, commanderID, commanderName, isFortress))
        message = self.getFormationForBaronAttack(kid, commanderID, commanderName, level, isFortress)
        message = removeAllBlanks(message)  # This ensures subclasses don't need to worry about formatting
        totals = self.calculate_tool_counts(message)
        log("getBaronAttackFormation OUT")
        return message, totals

    def calculate_tool_counts(self, message):
        totals = None
        if message:
            totals = {}
            struct = json.loads(message)
            for wave in struct:
                self.calculate_counts_for_flank(wave['L'], totals)
                pretty_print(totals, "TOTALS LEFT")
                # if TOOL_TYPE_BATTERING_RAM in totals:
                #     raise Exception('Invalid formation: RAMs found on a LEFT FLANK!')
                self.calculate_counts_for_flank(wave['R'], totals)
                pretty_print(totals, "TOTALS LEFT and RIGHT")
                # if TOOL_TYPE_BATTERING_RAM in totals:
                #     raise Exception('Invalid formation: RAMs found on a RIGHT FLANK!')
                self.calculate_counts_for_flank(wave['M'], totals)

        return totals

    def getCommanderIfAvailable(self, candidates):
        player = getPlayer()
        for cname in candidates:
            if cname in player.commanders:
                cid = player.commanders[cname]
                if self.isCommanderAvailable(cname, cid):
                    return cname, cid
                else:
                    log("Commander {} NOT available to attack".format(cname))
            else:
                console("USER ERROR: Command name '{}' DOES NOT EXIST".format(cname))
        return None, None

    def calculate_counts_for_flank(self, flank, totals):
        self.do_calculate_counts_for_flank(flank, totals, 'U')  # Troops
        self.do_calculate_counts_for_flank(flank, totals, 'T')  # Tools

    def do_calculate_counts_for_flank(self, flank, totals, key):
        for troops in flank[key]:
            if len(troops) == 0:  # Allow for empty wave
                continue
            ttype = troops[0]
            tcount = troops[1]
            if ttype in totals:
                totals[ttype] = totals[ttype] + tcount
            else:
                totals[ttype] = tcount


    def attackInBladeCoast(self):
        log("attackInBladeCoast IN")
        # player = getPlayer()
        bc = getBladeCoast()

        # When I jump to blade coast ir does not send this!!!
        # cmd = self.runDelayed(JumpToBladeCoast(bc.getBladeCoastID()))
        # aid = cmd.result['aid']
        # pretty_print(aid, "BLADE COAST AID")

        # %xt%EmpirefourkingdomsExGG_4%mpe%1%{"MID":-1}%
        # %xt%EmpirefourkingdomsExGG_4%mpe%1%{"MID":1}%
        # %xt%EmpirefourkingdomsExGG_4%mpe%1%{"MID":4}%
        # %xt%EmpirefourkingdomsExGG_4%pin%1%{}%
        # %xt%EmpirefourkingdomsExGG_4%tmp%1%{"MID":22}%
        # %xt%EmpirefourkingdomsExGG_4%sje%1%{"MID":22}%
        # %xt%EmpirefourkingdomsExGG_4%grc%1%{"AID":-24,"MID":22,"KID":-1}%

        # mid = bc['TM'][0]['MID']
        mid = bc.getBladeCoastID()
        if mid != 22:
            raise Exception("DID NOT PARSE RIGHT THING")
        # pretty_print(aid, "BLADE COAST AID")

        cmd = self.runDelayed(GetBladeCoastInfo(bc.getBladeCoastID(), -24))
        # console("kid={:d} level={: <3d} distance={: >4.1f} x={}, y={} timeTillAttackable={:d}".format(tower[6], tower[4], tower[len(tower) - 1], str(tower[1]), str(tower[2]), 0 if tower[5] < 0 else tower[5]))
        log("attackInBladeCoast OUT")


    def checkTotals(self, needs, adiResponse):
        log("checkTotals IN " + pp.pformat(needs))
        ok = True
        for k in needs.keys():
            requiredCount = needs[k]
            found = False

            log("Looking for [Troop/Tool {: >3d}, name {}] requires {:d}".format(k, tools_and_troops_to_string(k), requiredCount))
            for item in adiResponse['gui']['I']:
                if item[0] == k:
                    found = True
                    if requiredCount <= item[1]:
                        log("Troop/Tool {: >3d}, name {} requires {:d}, current count {:d} IS OK".format(item[0], tools_and_troops_to_string(item[0]), requiredCount, item[1]))
                    else:
                        console("INSUFFICIENT TOOLS/TROOPS ==> {} {:d}/{:d} missing {:d}".format(tools_and_troops_to_string(item[0]), item[1], requiredCount, requiredCount - item[1]))
                        ok = False
                    break
            if not found:
                ok = False
                # console("Troop or Tool ID {}, name {} requires {} NOT FOUND in inventory, ".format(str(k).rjust(3, ' '), tools_and_troops_to_string(k), str(requiredCount)))
                console("INSUFFICIENT TOOLS/TROOPS ==> {} NONE FOUND IN INVENTORY requires {:d}".format(tools_and_troops_to_string(k), requiredCount))

        # TODO green
        #    for x, op in enumerate(player._ops):
        #      # In theory it does not require an explicit jump to green prior
        #      log("jumping to OP '{0}' ".format(op.getEncodedName()))
        #      self.runDelayed(JumpToOp(op._x, op._y ))
        #
        #    log("jumping to Green ({0}: {1})".format(player._greenCastle.getEncodedName(), player._greenCastle._id))
        #    self.runDelayed(createJumpToGreen(player._greenCastle._id))

        log("checkTotals OUT, ok=" + str(ok))
        return ok

    def printTroopToolTotalsInAttack(self, totals):
        if self.args.print_attack_content:
            for toolTroopType in totals.keys():
                count = totals[toolTroopType]
                console("[Troop/Tool {: >3d}, name {}] count {:d}".format(toolTroopType, tools_and_troops_to_string(toolTroopType), count))

    def newCheckTotals(self, needs, adiResponse):
        """

        :param needs:
        :param adiResponse:
        :return: List of missing ids, Boolean if troops are missing, Boolean if tools are missing
        """
        log("checkTotals IN " + pp.pformat(needs))
        toolsMissing = False
        troopsMissing = False
        missing = {}
        for k in needs.keys():
            requiredCount = needs[k]
            found = False

            log("Looking for [Troop/Tool {: >3d}, name {}] requires {:d}".format(k, tools_and_troops_to_string(k), requiredCount))
            for item in adiResponse['gui']['I']:
                if item[0] == k:
                    found = True
                    if requiredCount <= item[1]:
                        log("Troop/Tool {: >3d}, name {} requires {:d}, current count {:d} IS OK".format(item[0], tools_and_troops_to_string(item[0]), requiredCount, item[1]))
                    else:
                        console("INSUFFICIENT TOOLS/TROOPS ==> {} {:d}/{:d} missing {:d}".format(tools_and_troops_to_string(item[0]), item[1], requiredCount, requiredCount - item[1]))
                        toolsMissing |= is_tool(k)
                        troopsMissing |= is_troop(k)
                        missing[k] = requiredCount - item[1]
                    break
            if not found:
                toolsMissing |= is_tool(k)
                troopsMissing |= is_troop(k)
                missing[k] = requiredCount
                # console("Troop or Tool ID {}, name {} requires {} NOT FOUND in inventory, ".format(str(k).rjust(3, ' '), tools_and_troops_to_string(k), str(requiredCount)))
                console("INSUFFICIENT TOOLS/TROOPS ==> {} NONE FOUND IN INVENTORY requires {:d}".format(tools_and_troops_to_string(k), requiredCount))

        # Having 3 return values deals with situation when there is a new unmapped id
        log("checkTotals OUT, missing={} toolsMissing={} troopsMissing={}".format(str(missing),str(toolsMissing),str(troopsMissing)))
        return missing, troopsMissing, toolsMissing

    def doHelpAll(self):
        gge_utils.log("doHelpAll IN")
        if not self.inCastle:
            player = getPlayer()
            gge_utils.log("jumping to Green ({0}: {1})".format(player._greenCastle.getEncodedName(), player._greenCastle._id))
            self.runDelayed(createJumpToGreen(player._greenCastle._id))
        self.runDelayed(HelpAll())

    # TODO find how to determine if more slots can be collected without sending blindly and getting an error (or having rubies consumed)
    def collectDailyBonus(self):
        pass
        # bonus = getBonus()
        # collected = 0
        # for b in bonus:
        #     if b:
        #         collected += 1
        #
        # if collected < 3:
        #     x = 0
        #     for b in bonus:
        #         if not b:
        #             self.runDelayed(DailyBonusCommand(x))
        #         x += 1
        #         collected += 1
        #         if collected == 3:
        #             break

    def printEconomy(self, printToolsTroops=True, mainOnly=False):
        log("printEconomy IN")
        player = getPlayer()
        self.runDelayed(GetEconomy(player._playerID))
        for c in player._castles:
            if mainOnly and not c.isGreenMain():
                continue

            # pretty_print(c._economicData)
            economicData = c.getEconomicData()
            console('-' * 80)
            console("{} in {}".format(c.getEncodedName(), kingdom_to_string(c._kingdomID)))
            console("Totals     {{'food':{:d}, 'wood':{:d}, 'stone':{:d}, 'iron':{:d}, 'glass':{:d}, 'oil':{:d}, 'coal':{:d}}}".format(economicData['food'], economicData['wood'], economicData['stone'], economicData['iron'], economicData['glass'], economicData['oil'], economicData['coal']))
            console("Production [food={:n}, wood={:n}, stone={:n}, iron={:n}, glass={:n}, oil={:n}, coal={:n}]".format(economicData['foodProduction'], economicData['woodProduction'], economicData['stoneProduction'], economicData['ironProduction'], economicData['glassProduction'], economicData['oilProduction'], economicData['coalProduction']))
            console("Consumption[food={:n}, net food={:n}]".format(economicData['foodConsumption'], economicData['foodProduction'] - economicData['foodConsumption']))
            console('=' * 80)

            if printToolsTroops:
                troops = [(tools_and_troops_to_string(key.split('tool')[1]), economicData[key]) for key in economicData.keys() if key.startswith('tool') and is_troop(key.split('tool')[1])]
                troops = sorted(troops)
                for key, value in troops:
                    console("{:<25}={}".format(key, value))

                tools = [(tools_and_troops_to_string(key.split('tool')[1]), economicData[key]) for key in economicData.keys() if key.startswith('tool') and is_tool(key.split('tool')[1])]
                tools = sorted(tools)
                for key, value in tools:
                    console("{:<25}={}".format(key, value))

                unknowns = [(tools_and_troops_to_string(key.split('tool')[1]), economicData[key]) for key in economicData.keys() if key.startswith('tool') and not is_known(key.split('tool')[1])]
                unknowns = sorted(unknowns)
                for key, value in unknowns:
                    console("{:<25}={}".format(key, value))

                    # toolsOrTroops = [(tools_and_troops_to_string(key.split('tool')[1]),economicData[key]) for key in economicData.keys() if key.startswith('tool') ]
                    # toolsOrTroops = sorted(toolsOrTroops)
                    # for key, value in toolsOrTroops:
                    #   console("{:<25}={}".format(key, value))

    def printCastleInfo(self):
        log("printCastleInfo IN")
        player = getPlayer()

        # TODO if you're gonna offer factory methods why force player info here instead of accessing the model inside the factory methods in commands.py ... besides for visiting other peoples castles?

        log("jumping to Green ({0}: {1})".format(player._greenCastle.getEncodedName(), player._greenCastle._id))
        self.runDelayed(createJumpToGreen(player._greenCastle._id))

        for x, op in enumerate(player._ops):
            # In theory it does not require an explicite jump to green prior
            log("jumping to OP '{0}' ".format(op.getEncodedName()))
            self.runDelayed(JumpToOp(op._x, op._y))

        if player._iceCastle is not None:
            log("jumping to Ice ({0}: {1})".format(player._iceCastle.getEncodedName(), player._iceCastle._id))
            self.runDelayed(createJumpToIce(player._iceCastle._id))

        if player._sandCastle is not None:
            log("jumping to Sand ({0}: {1})".format(player._sandCastle.getEncodedName(), player._sandCastle._id))
            self.runDelayed(createJumpToSands(player._sandCastle._id))

        if player._fireCastle is not None:
            log("jumping to Fire ({0}: {1})".format(player._fireCastle.getEncodedName(), player._fireCastle._id))
            self.runDelayed(createJumpToFire(player._fireCastle._id))

        if player._castleBerimond is not None:
            log("jumping to Berimond ({0}: {1})".format(player._castleBerimond.getEncodedName(), player._castleBerimond._id))
            self.runDelayed(JumpToBerimond(player._castleBerimond._x,player._castleBerimond._y))

        log("printCastleInfo OUT")

    def printWorldInfo(self):
        log("printWorldInfo IN")
        player = getPlayer()

        if player._iceCastle is not None:
            self.runDelayed(JumpToWorld(KINGDOM_ICE))
        if player._sandCastle is not None:
            self.runDelayed(JumpToWorld(KINGDOM_SANDS))
        if player._fireCastle is not None:
            self.runDelayed(JumpToWorld(KINGDOM_FIRE))
        self.runDelayed(JumpToWorld(KINGDOM_GREEN))
        log("printWorldInfo OUT")

    def recruitTroopsInBerimond(self):
        troopType = TROOP_TYPE_MARKSMAN

        player = getPlayer()
        sourceCastle = player.getCastle(KINGDOM_BERIMOND)
        cmd = self.runDelayed(JumpToBerimond(sourceCastle._x, sourceCastle._y))

        buildings = sourceCastle.getBuildings()
        if buildings['siegeWorkshop'] < BUILDING_SIEGE_WORKSHOP_LEVEL_2:
            console("Cannot build tools. No siege workshop or insufficient level {}".format(str(cmd._result['siegeWorkshop'])))
            return

        # Safety net (barracks level checking per troop type would be better)
        if buildings['training-grounds'] == -1:
            print ("No training grounds found")
            return

        qty = 5
        if buildings['training-grounds'] ==  BUILDING_BERIMOND_TRAINING_GROUNDS_LEVEL_2:
            qty = 7
        elif buildings['training-grounds'] ==  BUILDING_BERIMOND_TRAINING_GROUNDS_LEVEL_3:
            qty = 10
        elif buildings['training-grounds'] ==  BUILDING_BERIMOND_TRAINING_GROUNDS_LEVEL_4:
            qty = 15
        elif buildings['training-grounds'] ==  BUILDING_BERIMOND_TRAINING_GROUNDS_LEVEL_5:
            qty = 20

        castleState = cmd._result
        help = False # TODO cant remember if help is applicable in berimond

        if castleState['troopSlots'] > 0:
            while castleState['troopSlots'] > 0:
                cmd = self.runDelayed(BuildBerimondTroops(troopType, qty, help), short=True)
                castleState = cmd.result
        else:
            console("Cannot recruit troops, no free slots")

        # if playerData['troopSlots'] > 0:
        #     message = GG_HEADER + 'bup%1%{"SK":15,"WID":' + str(troopType) + ',"AMT":' + str(qty) + ',"PWR":0,"LID":3}' + GG_TAIL
        #     sendMessage(message)
        #     data = q_bup.get()
        #     rc = gge_utils.getError(data)
        #     if rc == 0:
        #         data = data.split('%')[5]
        #         decoded = json.loads(data)
        #         playerData['troopSlots'] = 0
        #         # print str(decoded)
        #         lastRequestId = 0
        #         for x, item in enumerate(decoded['spl']['PIDL']):
        #             status = item[0]
        #             print "Troop recruitment slot #{} id={}, troop count={}".format(str(x), str(item[0]), str(item[1]))
        #             if status == -1:
        #                 playerData['troopSlots'] = playerData['troopSlots'] + 1
        #             elif item[6] > 0:
        #                 lastRequestId = item[6]
        #         playerData['gold'] = decoded['gcu']['C1']
        #         print "Built troops, slots remaining: " + str(playerData['troopSlots']) + " Gold remaining: " + str(playerData['gold'])
        #         # askForHelp(lastRequestId)
        #         return True
        #     else:
        #         if rc == 88:
        #             print "Cannot recruit, max troops reached or will be passed if a full slot is filled!"
        #         else:
        #             print "Got error code " + str(rc)
        # else:
        #     print "No troop slots available"



        # if castleState['troopSlots'] > 0:
        #     while castleState['troopSlots'] > 0:
        #         if not (archerCount < archerMax or meleeDefenseCount < meleeDefenseMax or rangeDefenseCount < rangeDefenseMax or rangeOffenseCount < rangeOffenseMax or meleeOffenseCount < meleeOffenseMax):
        #             console("REACHED TROOP QUOTAS NOT RECRUITING meleeDefenseCount={:d}, rangeDefenseCount={:d}, rangeOffenseCount={:d}, meleeOffenseCount={:d}".format(meleeDefenseCount, rangeDefenseCount, rangeOffenseCount, meleeOffenseCount))
        #             break
        #
        #         if self.isRecruitOffensiveTroopsInCastle(castle) and archerCount < archerMax:
        #             troopType = TROOP_TYPE_ARCHER
        #         elif self.isRecruitDefensiveTroopsInCastle(castle) and (meleeDefenseCount < meleeDefenseMax < 150 or rangeDefenseCount < rangeDefenseMax < 150):
        #             troopType = self.getDefenseTypeToRecruit(castle, rangeDefenseCount, rangeDefenseMax, meleeDefenseCount, meleeDefenseMax)
        #         elif self.isRecruitOffensiveTroopsInCastle(castle) and (meleeOffenseCount < meleeOffenseMax or rangeOffenseCount < rangeOffenseMax):
        #             troopType = self.getOffenseTypeToRecruit(castle, rangeOffenseCount, rangeOffenseMax, meleeOffenseCount, meleeOffenseMax)
        #         elif self.isRecruitDefensiveTroopsInCastle(castle) and (meleeDefenseCount < meleeDefenseMax or rangeDefenseCount < rangeDefenseMax):
        #             troopType = self.getDefenseTypeToRecruit(castle, rangeDefenseCount, rangeDefenseMax, meleeDefenseCount, meleeDefenseMax)
        #         else:
        #             console("NOT RECRUITING!")
        #             break
        #
        #         troopCount = self.getNumberOfTroopsPerSlot(castle, troopType)
        #         cmd = self.runDelayed(BuildTroops(troopType, troopCount, help), short=True)
        #         castleState = cmd.result
        # else:
        #     console("Cannot recruit troops, no free slots")

        return False

    def spyAndAttackBerimond(self):
        log("spyAndAttackBerimond IN")

        player = getPlayer()
        sourceCastle = player.getCastle(KINGDOM_BERIMOND)
        cmd = self.runDelayed(JumpToBerimond(sourceCastle._x, sourceCastle._y))

        # %xt%fnt%1%0%{"X":1425,"Y":45,"gaa":{"KID":10,"uap":{"KID":10,"NS":-1,"PMS":-1,"PMT":0},"OI":[],"AI":[[17,1425,45,-410,0,[],-1,55,3724,56]]}}%
        berimondTowerCmd = self.runDelayed(FindNextTowerInBerimond())

        console("Found tower at: X={:d}, Y={:d}, Time since spy report={:d}, Level={:d}, {:d}h{:d}m{:d}s till attackable, No idea={:d}, Always -601={:d}".format(berimondTowerCmd['X'],
                 berimondTowerCmd['Y'], berimondTowerCmd['gaa']['AI']))
        console('-' * 80)
        pretty_print(berimondTowerCmd, "BERIMOND")

        if self.isAttackTravelingTo(KINGDOM_BERIMOND, berimondTowerCmd['X'], berimondTowerCmd['Y']):
            console("Attack already travelling to {:d},{:d}".format(berimondTowerCmd['X'], berimondTowerCmd['Y']))
            return

        print ("TODO make one for berimond")
        commanderName, commanderID = self.getCommanderForBerimondAttack(sourceCastle)
        if commanderName is None:
            console("No commander specified")
            return

        # Loop to handle: spying (retrying in case of spy failure) and finally attack
        while True:
            # Funny bit is Berimond uses same message as when looking up a human target (not like a nomads or rbc)
            targetDataCommand = self.runDelayed(GetPlayerTargetData(sourceCastle._x, sourceCastle._y, berimondTowerCmd['X'], berimondTowerCmd['Y'], KINGDOM_BERIMOND))
            if 'S' not in targetDataCommand.result:
                console("NO spy report found, attempting to send Spies!")
                self.doSpyBaron(sourceCastle, berimondTowerCmd['X'], berimondTowerCmd['Y'], KINGDOM_GREEN, sourceCastle.getMaxCoinSpeed(), True)
                continue

            console("Target has already been spied on")
            pretty_print(targetDataCommand.result['S'], 'NOMAD DEFENSE')

            commander = player.getCommanderByName(commanderName)
            if commander is None:
                print ("CANNOT FIND specified commander {} (name matching is case sensitive)".format(commanderName))
                break

            wallNegation = int(commander.getEquipmentBonus(EQ_BONUS_COMMANDER_WALL_PROTECTION_OF_ENEMY))
            gateNegation = int(commander.getEquipmentBonus(EQ_BONUS_COMMANDER_GATE_PROTECTION_OF_ENEMY))

            if NOMAD_DEBUG:
                print ("Wall negation {:d} gate negation {:d}".format(int(wallNegation), int(gateNegation)))

            formation, totals = self.getBerimondAttackFormation(targetDataCommand.result, targetDataCommand.result['S'], commanderName, gateNegation, wallNegation)
            if formation is None:
                print ("Could not build formation")
                break

            if NOMAD_DEBUG:
                print (formation.replace('{"L', '\n{"L'))
                print ("=" * 40)

            missing, troopsMissing, toolsMissing = self.newCheckTotals(totals, targetDataCommand.result)

            # Buy all missing tools (we know we have the troops to attack otherwise the formation would not have been built)
            if toolsMissing:
                missingTools = {k: v for k, v in missing.iteritems() if is_tool(k)}
                if self.quickBuyAllToolsFromArmorer(sourceCastle, missingTools):
                    for k in missing.keys():
                        del missing[k]
                        # There doesn't doesn't seem to be a concept of outside/inside the camp in Berimond.
                        # The game just requests map tiles when it wants to render the map outside the camp

            if len(missing) == 0:
                console("Troop and Tool counts are sufficient to attack!")
                self.printTroopToolTotalsInAttack(totals)

                if not self.args.dry_run:
                    self.runDelayed(Pin())
                    self.runDelayed(Pin())
                    speed = SPEED_LVL_BERIMOND_COIN_BOOST  # This won't work as is: speed = sourceCastle.getMaxCoinSpeed()
                    self.runDelayed(AttackCommand(KINGDOM_BERIMOND, formation, sourceCastle._x, sourceCastle._y, berimondTowerCmd['X'], berimondTowerCmd['Y'], commanderID, speed, True))

        log("spyAndAttackBerimond OUT")

    def getBerimondAttackFormation(self, level, adiResponse, S_key, commanderName, gateNegation=0, wallNegation=0):
        message, flankCount, middleCount = self.doGetBerimondAttackFormation(S_key, commanderName, gateNegation, wallNegation)
        message = self.fillBerimondAttackWithAvailableTroops(level, adiResponse, message, flankCount, middleCount)
        totals = self.calculate_tool_counts(message)
        return message, totals

    def doGetBerimondAttackFormation(self, S_key, commanderName, gateNegation=0, wallNegation=0):
        print ("THIS IS A COPY OF NOMADS, it has not been adapted for berimond yet")
        index = 0
        tools = []
        for flank in S_key:
            pretty_print(flank, 'flank')
            rams = 0
            ladders = 0
            shields = 0

            bombCount = 0
            arrowCount = 0
            rangeDefender = 0
            meleeDefender = 0
            for defender in flank: # defender is troop or tool
                pretty_print(defender, 'defender')
                if NOMAD_DEBUG:
                    print ("Flank {} {}={:d}".format(Client.flankNameFromIndex(index), tools_and_troops_to_string(defender[0]), defender[1]))
                if defender[0] == TOOL_TYPE_BODKIN_ARROWHEADS:
                    arrowCount = arrowCount + 1
                elif defender[0] == TOOL_TYPE_LIME_POWDER_BOMB:
                    bombCount = bombCount + 1
                elif defender[0] == TROOP_TYPE_SPEAR_THROWER:
                    rangeDefender = rangeDefender + defender[1]
                elif defender[0] == TROOP_TYPE_LANCE:
                    meleeDefender = meleeDefender + defender[1]
                else:
                    print ("TOOL OR TROOP TYPE {:d} {}".format(defender[0], tools_and_troops_to_string(defender[0])))


            if index < 3:
                if NOMAD_DEBUG:
                    print ("-" * 40)
                    print ("Flank {} arrow count={:d}, lime bomb={:d}, range defense={:d}, melee defense={:d}".format(Client.flankNameFromIndex(index), arrowCount, bombCount, rangeDefender, meleeDefender))
                    print ("-" * 40)

                if arrowCount == 0:    # 119% range boost
                    shields = 24
                elif arrowCount == 1:  # 169% range boost
                    shields = 34
                elif arrowCount == 2:  # 219% range boost
                    shields = 40
                elif arrowCount == 3:  # 269% range boost
                    shields = 40
                else:
                    pass

                # print (">>>>>>>>>>> SHIELDS " + str(shields))

                # Don't send shields if less than 10 range defenders
                if rangeDefender < 10:
                    shields = 0
                elif rangeDefender <= 15: # Only send 24 shields max if between 10 and 15 range troops
                    if shields > 24:
                        shields = 24

                if index == 1: # Front
                    rams = 12
                    rams = rams - (gateNegation/10)
                    remainder  = gateNegation^10
                    # TODO if there is room for one more ram and the remainder of (gateNegation/10) is not 0 then add a ram

                    # If shields and rams would be more than max allowed then always Make room for rams
                    if shields + rams > 50: # if shields > 34:
                        if NOMAD_DEBUG:
                            print ("shields + rams > 50 --> {:d} reducing shields to {:d}".format(shields + rams, 50 - rams))
                        shields = shields - rams
                        shields = 50 - rams
                    ladders = 50 - shields - rams

                    if ladders > (13 - wallNegation/10):
                        ladders = (13 - wallNegation/10)

                    if rams + shields + ladders < 50 and remainder > 0:
                        if NOMAD_DEBUG:
                            print ("Incrementing rams by one tool total={:d} remainder={}".format((rams + shields + ladders),str(remainder)))
                        rams = rams + 1

                    # Don't let ladder remain negative
                    if ladders < 0:
                        ladders = 0
                elif index == 0 or index == 2:
                    ladders = 40 - shields
                    if ladders > 13: # Max it at 13
                        ladders = 13

                    if ladders > (13 - wallNegation/10):
                        ladders = (13 - wallNegation/10)

                # index 3 and 4 are always empty

                if index == 1:  # Front
                    if NOMAD_DEBUG:
                        print ("Would use {:d} ladders, {:d} shields, {:d} rams on front".format(ladders, shields, rams))
                    if rams + shields + ladders > 50:
                        print ("BUG TOO MANY TOOLS ON FRONT\n" * 30)
                elif index == 0 or index == 2:
                    flankName = "Left"
                    if index == 2:
                        flankName = "Right"
                    if NOMAD_DEBUG:
                        print ("Would use {:d} ladders, {:d} shields {} flank".format(ladders, shields, flankName))
                    if shields + ladders > 40:
                        print ("BUG TOO MANY TOOLS ON " + flankName + "\n" * 30)
                if NOMAD_DEBUG:
                    print ("=" * 40)

            first = True
            toolsOnFlank = ""
            if ladders > 0:
                if not first:
                    toolsOnFlank = toolsOnFlank + ","
                toolsOnFlank = toolsOnFlank + "[{:d},{:d}]".format(TOOL_TYPE_LADDER, ladders)
                first = False
            if shields > 0:
                if not first:
                    toolsOnFlank = toolsOnFlank + ","
                toolsOnFlank = toolsOnFlank + "[{:d},{:d}]".format(TOOL_TYPE_MANTLET, shields)
                first = False
            if rams > 0:
                if not first:
                    toolsOnFlank = toolsOnFlank + ","
                toolsOnFlank = toolsOnFlank + "[{:d},{:d}]".format(TOOL_TYPE_BATTERING_RAM, rams)
            tools.append(toolsOnFlank)

            index += 1

        rangeOffense = TROOP_TYPE_ELITE_CROSSBOWMAN
        flankCount = self.getFlankTroopCountForCommander(commanderName)
        middleCount = self.getFrontTroopCountForCommander(commanderName)

        values = {'leftTroops':rangeOffense, 'middleTroops':rangeOffense, 'rightTroops':rangeOffense, 'leftTools':tools[0],
                  'middleTools':tools[1], 'rightTools':tools[2], 'flankCount':flankCount, 'middleCount':middleCount}

        firstWave = '{{"L":{{"U":[[{leftTroops!s},{flankCount!s}]],"T":[{leftTools}]}},' \
                      '"R":{{"U":[[{rightTroops!s},{flankCount!s}]],"T":[{rightTools}]}},' \
                      '"M":{{"U":[[{middleTroops!s},{middleCount!s}]],"T":[{middleTools}]}}}},'.format(**values)

        lootingWaves = '{"L":{"U":[],"T":[]},"R":{"U":[],"T":[]},"M":{"U":[],"T":[]}},' \
                       '{"L":{"U":[],"T":[]},"R":{"U":[],"T":[]},"M":{"U":[],"T":[]}},' \
                       '{"L":{"U":[],"T":[]},"R":{"U":[],"T":[]},"M":{"U":[],"T":[]}}'

        message = '[' + firstWave + lootingWaves + ']'
        return message, flankCount, middleCount

    def fillBerimondAttackWithAvailableTroops(self, level, adiResponse, message, flankCount, middleCount):
        log("fillBerimondAttackWithAvailableTroops IN")

        struct = json.loads(message)
        rangeTroops = {key: value for (key, value) in adiResponse['gui']['I'] if self.is_range_troop(key)}
        meleeTroops = {key: value for (key, value) in adiResponse['gui']['I'] if self.is_melee_troop(key)}

        pretty_print(rangeTroops, 'rangeTroops')
        pretty_print(meleeTroops, 'meleeTroops')

        for item in adiResponse['gui']['I']:
            if self.is_range_troop(item[0]):
                rangeTroops[item[0]] = item[1]
                log("Range troops {:d}, name {} current count {:d}".format(item[0], tools_and_troops_to_string(item[0]), item[1]))
            elif self.is_melee_troop(item[0]):
                meleeTroops[item[0]] = item[1]
                log("Range troops {:d}, name {} current count {:d}".format(item[0], tools_and_troops_to_string(item[0]), item[1]))
            else:
                log("Non classified tool/troops {:d}, name {} current count {:d}".format(item[0], tools_and_troops_to_string(item[0]), item[1]))

        print ("TODO will need to send melee in 2nd/3rd or 4th wave")
        builder = BaronAttackFormationBuilder2(struct, rangeTroops, meleeTroops, {}, False, False)
        struct = builder.buildFormation()
        pretty_print(struct, "BUILDER RETURNED")

        message = self.correctWallOrderInWave(struct)
        log("fillBerimondAttackWithAvailableTroops OUT, message=" + xstr(message))
        return message

    def attackFarm(self):
        """
        Intended to be implemented by subclasses
        :return:
        """
        pass

    def printGems(self):
        self.runDelayed(GetGemsInfo())
        self.runDelayed(GetCommandersAndCastellansInfo())
        self.runDelayed(GetEquipmentInfo())

    def leaveAlliance(self):
        self.runDelayed(LeaveAlliance())

    def applyToAlliance(self, allianceName):
        # TODO look up target alliance first. so that if we're already there then don't leave and re-apply!
        player = getPlayer()

        cmd = self.runDelayed(GetAllianceID(allianceName))
        targetAllianceID = -1
        for alliance in cmd.result['L']:
            if alliance[2][1].lower() == allianceName.lower():
               targetAllianceID = alliance[2][0]

        if player._allianceID > 0 and player._allianceID == targetAllianceID:
            console("ALREADY IN " + allianceName)
            return

        if player._allianceID > 0:
            self.runDelayed(LeaveAlliance())

        self.runDelayed(ApplyToAlliance(targetAllianceID))

    def parseCommandLine(self):
        parser = self.buildParser(True)
        self.args = parser.parse_args()
        print (self.args)

    def buildParser(self, add_help=False):
        """
        Returns the default command line parser. Can bve used by scripts/classes extending this one to build new features
        on top of the standard set.
        :return:
        """
        parser = argparse.ArgumentParser(add_help=add_help, description='GG Client')

        parser.add_argument('-a', '--attack-barons', action='store_true', help='Attack barons in all kingdoms (green not yet supported)')
        parser.add_argument(      '--attack-baron', action="append", help='Attack baron')
        parser.add_argument(      '--buy-tools-for-baron', action="store_true", help='Buy missing tools from armorer for baron attack')

        parser.add_argument('-b', '--build-tools', action='store_true', help='Produce tools')

        parser.add_argument('-c', '--print-alliance-coordinates', action='append', help='Print alliance coordinates')
        parser.add_argument(      '--include-distance-to-me', action='store_true', help='Print alliance coordinates relative to me')
        parser.add_argument(      '--rvs-only', action='store_true', help='Print alliance coordinates RVs only')

        parser.add_argument('-d', '--dry-run', action='store_true', help="Don't attack just perform validity checks")
        parser.add_argument(      '--list-barons', action='store_true', help='List barons')
        parser.add_argument('-e', '--print-economy', action='store_true', help='Print economy info (summary no troops/tools)')
        parser.add_argument(      '--print-main-economy', action='store_true', help='Print economy info for main castle only')
        parser.add_argument(      '--print-full-economy', action='store_true', help='Print full economy')
        parser.add_argument('-g', '--recruit-green', action='store_true', help='Recruit troops in Green')
        parser.add_argument('-k', '--attack-player', action='store_true', help='Attack player')
        parser.add_argument('-l', '--loop', type=int, nargs='?', default=None, const=-1, help='Run in a loop')  # if not present None is returned, if present with no value -1 is returned
        parser.add_argument('-n', '--attack-nomads', action='store_true', help='Spy and attack nomads')
        parser.add_argument(      '--attack-berimond', action='store_true', help='Spy and attack in Berimond')
        parser.add_argument(      '--recruit-berimond', action='store_true', help='Recruit troops in Berimond BETA')
        parser.add_argument('-p', '--print-info', action='store_true', help='Print castle info')
        parser.add_argument('-r', '--recruit-troops', action='store_true', help='Recruit troops')
        parser.add_argument('-s', '--send-rss', action='store_true', help='Send Rss')
        parser.add_argument(      '--send-rss-new', action='store_true', help='Send Rss')
        parser.add_argument('-t', '--collect-tax', type=int, choices=[10, 30, 90, 180, 360, 720], nargs='?', const=30, help='Collect taxes')
        parser.add_argument('-u', '--buy-tools', action='store_true', help='Buy tools from armorer')
        parser.add_argument('-v', '--favor-low-level-barons', action='store_true', help='Hit low level barons first')
        parser.add_argument('-x', '--help-all', action='store_true', help='Help all')
        parser.add_argument(      '--heal-troops', action='store_true', help='Heal troops')
        parser.add_argument(      '--spy-barons', action='store_true', help='Spy barons')
        parser.add_argument(      '--station-troops', action='store_true', help='ALPHA: station troops')
        parser.add_argument(      '--blade-coast', action='store_true', help='ALPHA: blade coast')
        parser.add_argument(      '--farm', action='store_true', help='ALPHA: farm')
        parser.add_argument(      '--print-gems', action='store_true', help='Print gems')
        parser.add_argument(      '--print-samurai-rankings', action='append', help='Print samurai alliance score')

        parser.add_argument(      '--leave-alliance', action='store_true', help='Leave alliance')
        parser.add_argument(      '--apply-alliance', action='append', help='Apply to join alliance (leaves current one first)')
        parser.add_argument(      '--use-khan-chests', action='store_true', help='Use Khan chests for nomad levels 90')
        parser.add_argument(      '--use-khan-chests-for-midas', action='store_true', help='Use Khan chests to get more points in King Midas event')
        parser.add_argument(      '--use-time-skips', action='store_true', help='Use time skips for nomads')
        parser.add_argument(      '--ask-for-help', action='store_true', help='Ask for help when recruiting and healing')
        parser.add_argument(      '--print-attack-content', action='store_true', help='Print the tool & troop counts used when sending an attack')

        parser.add_argument('inifile', help='INI file path')
        return parser

    def run(self):
        self.parseCommandLine()
        try:
            self.runscript()
            if self.args.loop:
                self.read()
        except KeyboardInterrupt:
            pass
        finally:
            self.terminate()


if __name__ == '__main__':
    c = Client()
    c.run()