from gge_constants import *
import gge_constants


class Player(object):
    def __init__(self, playerName, playerID, allianceName, allianceID, greenCastle, ops, iceCastle, sandCastle, fireCastle, castleBerimond, rvMap, commanders, newCommanders, timeSkips, feast):
        self._playerName = playerName
        self._playerID = playerID
        self._allianceName = allianceName
        self._allianceID = allianceID

        self._greenCastle = greenCastle
        self._iceCastle = iceCastle
        self._sandCastle = sandCastle
        self._fireCastle = fireCastle
        self._castleBerimond = castleBerimond
        self._ops = ops

        # For convenience provide a list with only green castles
        self.__greenCastles = ops[:]
        self.__greenCastles.insert(0, greenCastle)

        self._castles = []
        if iceCastle is not None:
            self._castles.append(iceCastle)
        if sandCastle is not None:
            self._castles.append(sandCastle)
        if fireCastle is not None:
            self._castles.append(fireCastle)
        if castleBerimond is not None:
            self._castles.append(castleBerimond)

        self._castles.append(greenCastle)

        if ops is not None and len(ops) > 0:  # This might be useless
            self._castles.extend(ops)

        self._rvMap = rvMap
        self._kts = None  # TODO
        self._metros = None  # TODO
        self._capitals = None  # TODO Capital mapping should be per kingdom

        self.commanders = commanders
        # New object array to replace the old Name=ID hashmap (above)
        self.__newCommanders = newCommanders

        self.timeSkips = timeSkips
        self.feast = feast

    def getFeastTimeRemaining(self):
        """ Returns the number of seconds remaining in the current feast. 0 if non is running """
        return self.feast['RT']

    def getFeastType(self):
        return self.feast['T']

    def getGreenCastles(self):
        return self.__greenCastles

    def getCastle(self, kid, name=None):
        if kid == KINGDOM_ICE or kid == KINGDOM_SANDS or kid == KINGDOM_FIRE:
            for c in self._castles:
                if c.kingdomId == kid:
                    return c
        elif kid == KINGDOM_GREEN:
            if name is None:
                return self._greenCastle
            else:
                for c in self._castles:
                    if c.name == name:
                        return c
        return None

    def getCastleById(self, castleId):
        for c in self._castles:
            if c.id == castleId:
                return c
        return None

    def setEconomicData(self, economyPerCastle):
        for key, value in economyPerCastle.iteritems():
            castle = self.getCastleById(key)
            castle.setEconomicData(value)

    def getCommanders(self):
        return self.__newCommanders

    def getCommanderByName(self, commanderName):
        for c in self.__newCommanders:
            if c.getName() == commanderName:
                return c
        return None


class AuthenticatedPlayer(Player):
    def __init__(self, playerName, playerID, allianceName, allianceID, greenCastle, ops, iceCastle, sandCastle, fireCastle, castleBerimond, rvMap, commanders, newCommanders, timeSkips, feast):
        Player.__init__(self, playerName, playerID, allianceName, allianceID, greenCastle, ops, iceCastle, sandCastle, fireCastle, castleBerimond, rvMap, commanders, newCommanders, timeSkips, feast)

    def __repr__(self):
        return "AuthenticatedPlayer{playerName=" + self._playerName + ", playerID=" + str(self._playerID) + ", allianceName=" + self._allianceName + ", allianceID=" + str(self._allianceID) + ", greenCastle=" + xstr(self._greenCastle) + ", iceCastle=" + xstr(self._iceCastle) + ", sandCastle=" + xstr(self._sandCastle) + ", fireCastle=" + xstr(self._fireCastle) + ", ops=" + xstr(self._ops) + "}"
        # +", _rvMap"+self._rvMap+"}"

    # def __str__(self):
    # return "AuthenticatedPlayer"

    def __add__(self, other):
        return str(self) + other

    def __radd__(self, other):
        return other + str(self)


class AbstractCastle(object):
    def __init__(self, x, y, castleId, name, kingdomID):
        self._x = x
        self._y = y
        self._id = castleId
        self._name = name
        self._kingdomID = kingdomID

        # TODO meant to replace the ones above
        # These are all read-only!
        self.__x = x
        self.__y = y
        self.__castleId = castleId
        self.__name = name
        self.__kingdomId = kingdomID

    @property
    def x(self):
        return self.__x

    @property
    def y(self):
        return self.__y

    @property
    def id(self):
        return self.__castleId

    @property
    def name(self):
        return self.__name

    @property
    def kingdomId(self):
        return self.__kingdomId

    def getEncodedName(self):
        """ Returns a safe to print version of the name (all unicode chars are escaped)
        """
        if isinstance(self._name, unicode):
            return unicode.encode(self._name, 'utf-8')
        return self._name


# TODO: Castle should offer the following info
#
# BUILDING_HOSPITAL_LEVEL_1      = 1
# BUILDING_HOSPITAL_LEVEL_3      = 3

# BUILDING_BARRACKS_LEVEL_1 = 160
# BUILDING_BARRACKS_LEVEL_2 = 161
# BUILDING_BARRACKS_LEVEL_3 = 162
# BUILDING_BARRACKS_LEVEL_4 = 163
# BUILDING_BARRACKS_LEVEL_5 = 164
#
# BUILDING_STABLES_LEVEL_1 = 214
# BUILDING_STABLES_LEVEL_3 = 226
#
# BUILDING_DEFENSE_WORKSHOP_LEVEL_1 = 176
#
# Hospital level
# Barracks level
# Stables level
# Offensive workshop level
# Defensive workshop level
# Fire station level???

class Castle(AbstractCastle):
    TA_CASTLE_TYPE_MAIN = -1
    TA_CASTLE_TYPE_FOOD_OP = 0

    CASTLE_TYPE_MAIN = 1
    CASTLE_TYPE_OP = 4
    CASTLE_TYPE_NON_GREEN_CASTLE = 12

    # TODO don't know the values for wood and stone ops (not sure about 8-2 vs 6-2 either)

    def __init__(self, opType, x, y, castleId, name, kingdomID):
        AbstractCastle.__init__(self, x, y, castleId, name, kingdomID)
        self._type = opType
        self._kingdomID = kingdomID
        self._economicData = []
        self.__buildings = None

    def __repr__(self):
        name = self._name
        if isinstance(self._name, unicode):
            name = unicode.encode(self._name, 'utf-8')
        return "Castle{kingdomID=" + gge_constants.kingdom_to_string(self._kingdomID) + ", id=" + str(self._id) + ", name=" + name + ", type=" + str(self._type) + ", x=" + str(self._x) + ", y=" + str(self._y) + "}"

    def __str__(self):
        # TODO new Never tested it
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        # TODO dont think calling unicode() on integers is what we want here
        return u"Castle{kingdomID=" + unicode(self._kingdomID) + u", id=" + unicode(self._id) + u", name=" + unicode(self._name) + u", type=" + unicode(self._type) + u", x=" + unicode(self._x) + u", y=" + unicode(self._y) + u"}"

    # def __str__(self):
    # return "__str__ Castle"

    def __add__(self, other):
        return str(self) + other

    def __radd__(self, other):
        return other + str(self)

    def isOp(self):
        return self._type == Castle.CASTLE_TYPE_OP

    def isGreenMain(self):
        return self._type == Castle.CASTLE_TYPE_MAIN

    def isIceMain(self):
        return self._type == Castle.CASTLE_TYPE_NON_GREEN_CASTLE and self._kingdomID == KINGDOM_ICE

    def isSandMain(self):
        return self._type == Castle.CASTLE_TYPE_NON_GREEN_CASTLE and self._kingdomID == KINGDOM_SANDS

    def isFireMain(self):
        return self._type == Castle.CASTLE_TYPE_NON_GREEN_CASTLE and self._kingdomID == KINGDOM_FIRE

    def isBerimond(self):
        return self._kingdomID == KINGDOM_BERIMOND

    def setEconomicData(self, economy):
        self._economicData = economy

    def getEconomicData(self):
        return self._economicData

    def setBuildings(self, buildings):
        self.__buildings = buildings

    def getBuildings(self):
        return self.__buildings

    def getHospitalLevel(self):
        if self.__buildings is not None:
            for b in self.__buildings:
                if b[0] == BUILDING_HOSPITAL_LEVEL_1:
                    return 1
                # if b[0] == BUILDING_HOSPITAL_LEVEL_2:
                #     return 2
                if b[0] == BUILDING_HOSPITAL_LEVEL_3:
                    return 3
                # if b[0] == BUILDING_HOSPITAL_LEVEL_4:
                #     return 4
                # if b[0] == BUILDING_HOSPITAL_LEVEL_5:
                #     return 5
                # if b[0] == BUILDING_HOSPITAL_LEVEL_6:
                #     return 6
                # if b[0] == BUILDING_HOSPITAL_LEVEL_7:
                #     return 7
                # if b[0] == BUILDING_HOSPITAL_LEVEL_8:
                #     return 8
                # if b[0] == BUILDING_HOSPITAL_LEVEL_9:
                #     return 9
                # if b[0] == BUILDING_HOSPITAL_LEVEL_10:
                #     return 10

        return 0

    def getBarracksLevel(self):
        if self.__buildings is not None:
            for b in self.__buildings:
                if b[0] == BUILDING_BARRACKS_LEVEL_1:
                    return 1
                if b[0] == BUILDING_BARRACKS_LEVEL_2:
                    return 2
                if b[0] == BUILDING_BARRACKS_LEVEL_3:
                    return 3
                if b[0] == BUILDING_BARRACKS_LEVEL_4:
                    return 4
                if b[0] == BUILDING_BARRACKS_LEVEL_5:
                    return 5
        return 0

    def getStablesLevel(self):
        if self.__buildings is not None:
            for b in self.__buildings:
                if b[0] ==  BUILDING_STABLES_LEVEL_1:
                    return 1
                if b[0] ==  BUILDING_STABLES_LEVEL_2:
                    return 2
                if b[0] ==  BUILDING_STABLES_LEVEL_3:
                    return 3
        return 0

    def getOffensiveWorkshopLevel(self):
        if self.__buildings is not None:
            for b in self.__buildings:
                if b[0] ==  BUILDING_DEFENSE_WORKSHOP_LEVEL_1:
                    return 1
                if b[0] ==  BUILDING_DEFENSE_WORKSHOP_LEVEL_1:
                    return 2
                # if b[0] ==  BUILDING_DEFENSE_WORKSHOP_LEVEL_3:
                #     return 3
        return 0

    def getDefensiveWorkshopLevel(self):
        if self.__buildings is not None:
            for b in self.__buildings:
                if b[0] ==  BUILDING_DEFENSE_WORKSHOP_LEVEL_1:
                    return 1
                if b[0] ==  BUILDING_DEFENSE_WORKSHOP_LEVEL_1:
                    return 2
                # if b[0] ==  BUILDING_DEFENSE_WORKSHOP_LEVEL_3:
                #     return 3
        return 0

    def getFireStationLevel(self):
        if self.__buildings is not None:
            for b in self.__buildings:
                pass
                # if b[0] ==  BUILDING_FIRE_STATION_LEVEL_1:
                #     return 1
                # if b[0] ==  BUILDING_FIRE_STATION_LEVEL_1:
                #     return 2
                # if b[0] ==  BUILDING_FIRE_STATION_LEVEL_3:
                #     return 3
                # if b[0] ==  BUILDING_FIRE_STATION_LEVEL_4:
                #     return 4
        return 0

    def getMaxCoinSpeed(self):
        level = self.getStablesLevel()

        speed = SPEED_NO_BOOST
        if level == 1:
            speed = SPEED_LVL_1_STABLE_COIN_BOOST
        elif level == 2:
            speed = SPEED_LVL_2_STABLE_COIN_BOOST
        elif level == 3:
            speed = SPEED_LVL_3_STABLE_COIN_BOOST

        return speed


class RV(AbstractCastle):
    CASTLE_TYPE_RV = 10

    def __init__(self, rvType, x, y, rvId, name, kingdomID, rvTroops):
        AbstractCastle.__init__(self, x, y, rvId, name, kingdomID)
        self._type = rvType
        self._rvTroops = rvTroops

        # TODO meant to replace the ones above
        self.__type = rvType
        self.__rvTroops = rvTroops

    def __repr__(self):
        if isinstance(self.name, unicode):
            rvName = unicode.encode(self.name, 'utf-8')
        else:
            rvName = self.name
        return "RV{{kingdomID={}, id={:d}, name={}, type={}, x={:d}, y={:d}}}".format(gge_constants.kingdom_to_string(self.__kingdomId), self.__castleId, rvName, gge_constants.rv_type_to_string(self.__type), self.__x, self.__y)

    def __unicode__(self):
        return u"RV{kingdomID=" + unicode(str(self.__kingdomId)) + u", id=" + unicode(str(self.__castleId)) + u", name=" + unicode(self.__name) + u", type=" + unicode(self.__type) + u", x=" + unicode(str(self.__x)) + u", y=" + unicode(str(self.__y)) + u"}"


class Commander(object):
    def __init__(self, ID, name, armorAttributes):
        self.__id = ID
        self.__name = name
        self.__armorAttributes = armorAttributes

    def getAllEquipmentBonuses(self):
        return self.__armorAttributes

    def getEquipmentBonus(self, bonusID):
        if bonusID in self.__armorAttributes:
            return self.__armorAttributes[bonusID]
        return 0

    def getName(self):
        return self.__name

    def getID(self):
        return self.__id

    # Meant to replace getName()
    @property
    def name(self):
        return self.__name

    # Meant to replace getID()
    @property
    def id(self):
        return self.__id

    def __repr__(self):
        name = self.__name
        if isinstance(self.__name, unicode):
            name = unicode.encode(self.__name, 'utf-8')
        return "Commander{id=" + str(self.__id) + ", name=" + name + "}"


class BladeCoast(object):
    """
    Wrapper around the Blade coast info
    """
    def __init__(self, data):
        # It is possible that the tower or ship is not present in the array before you attack it (or maybe open it to see its content)
        self.__data = data
        # bladeCoastID = payload['tmp']['TM'][0]['MID']
        # campContent = payload['tmp']['TM'][0]['S'] # Wood, Stone, Food, Max capacity for Stone, Food, Wood
        # campTroops  = payload['tmp']['TM'][0]['I'] # Troops

    def getBladeCoastID(self):
        return self.__data['MID']

    def getTroopsAndTools(self):
        return self.__data['I']

    def getNextAttackableTower(self):
        pass

    def getCampContent(self):
        return self.__data[0]['S']

    # Ships are the RBCs of blade coast
    def getAttackableShip(self):
        #
        # Pirate ships and towers seem to have hard coded IDs
        #
        # 166: First Tower (1st row of towers)
        # 167: RBC  (1st row of RBCs after first tower)
        # 168: RBC  (1st row of RBCs after first tower)
        # 169: RBC  (1st row of RBCs after first tower)
        #
        # 170: 2nd Tower (2nd row of towers)
        # 172: 3rd Tower (2nd row of towers)
        #
        # 171: RBC (2nd row of RBCs)
        # 173: RBC (2nd row of RBCs)
        #
        # 174: Tower (3rd row)
        # ----------------------------------------------------------
        # Beaten tower:
        # {NID: 170, A: 1}
        #
        # Not Beaten tower:
        # {NID: 174, A: 0}
        #
        # RBC available to hit
        # {NID: 167, CD: 0}
        #
        # Burning RBC hittable in 713 seconds
        # {NID: 169, CD: 713}
        for tower in self.__data['N']:
            if tower['NID'] in [167, 168, 169] and tower['CD'] == 0:
                return tower
        return None


def xstr(s):
    if s is None:
        return ''
    return str(s)


def has_enough_rss_to_build_tools(toolType, toolCount, rssCounts):
    # Undefined tool type just quit early
    if toolType == -1:
        return False

    # TODO this should lookup the server not a static map
    if toolType == gge_constants.TOOL_TYPE_MANTLET:
        # This is based on Kornh ... check if different for other players (not sure research might affect this or some other aspect of the game)
        return rssCounts['wood'] > (toolCount * 105) and rssCounts['stone'] > (toolCount * 45)
    elif toolType == gge_constants.TOOL_TYPE_LADDER:
        return rssCounts['wood'] > (toolCount * 28) and rssCounts['stone'] > (toolCount * 12)
    elif toolType == gge_constants.TOOL_TYPE_BATTERING_RAM:
        return rssCounts['wood'] > (toolCount * 56) and rssCounts['stone'] > (toolCount * 24)
    elif toolType == TOOL_TYPE_BANNER:  # TODO this only needs coins
        return True

    return False


def has_enough_coins_to_recruit_troops(troopType, troopCount, coinCount):
    # TODO this should lookup the server not a static map
    if troopType == gge_constants.TROOP_TYPE_KINGSGUARD_BOW:
        return coinCount > (troopCount * 500)
    if troopType == gge_constants.TROOP_TYPE_KINGSGUARD_KNIGHT:
        return coinCount > (troopCount * 500)
    if troopType == gge_constants.TROOP_TYPE_KINGSGUARD_ROYAL_SCOUT:
        return coinCount > (troopCount * 500)
    if troopType == gge_constants.TROOP_TYPE_KINGSGUARD_ROYAL_SENTINEL:
        return coinCount > (troopCount * 500)

    # TODO fix this is bogus
    return False