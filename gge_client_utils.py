from gge_constants import *
from gge_commands import pretty_print
from gge_utils import console


class BaseFormationBuilder(object):
    def __init__(self):
        pass

    def fillWallWithTroops(self, excludedTroops, availableTroops, requiredTroopCount, maxTypesOnWall, mustFill=True, favorSmall=False):
        debug_log("fillWallWithTroops IN, {}".format(str(mustFill)))

        type1, type1Count = self.findLowest1TroopTypeToCover(excludedTroops, availableTroops, requiredTroopCount)
        if type1 != 0:
            return [[type1, type1Count]]

        if maxTypesOnWall == 1:
            return None

        if mustFill:
            type1, type1Count, type2, type2Count = self.find2TroopTypesToCover(excludedTroops, availableTroops, requiredTroopCount)
        else:
            type1, type1Count, type2, type2Count = self.find2TroopTypesBestEffort(excludedTroops, availableTroops, requiredTroopCount)
        if type1 != 0:
            if type2 != 0:
                return [[type1, type1Count], [type2, type2Count]]
            return [[type1, type1Count]]

        return None

    def findLowest1TroopTypeToCover(self, excludedTroops, availableTroops, requiredTroopCount):
        debug_log("findLowest1TroopTypeToCover IN")

        low = 10000
        selectedKey = 0
        for key, count in availableTroops.iteritems():
            debug_log("findLowest1TroopTypeToCover key {:3d} count {:4d} requiredTroopCount {:3d} low {:d}".format(key, count, requiredTroopCount, low))
            if requiredTroopCount <= count <= low and key not in excludedTroops:
                selectedKey = key
                low = count

        debug_log("findLowest1TroopTypeToCover OUT {:d} {:d}".format(selectedKey, requiredTroopCount))

        return selectedKey, requiredTroopCount

    def find2TroopTypesToCover(self, excludedTroops, availableTroops, requiredTroopCount):
        debug_log("find2TroopTypesToCover IN")
        highKey = 0
        lowKey = 0

        high = 0
        for key, count in availableTroops.iteritems():
            if count > high and key not in excludedTroops:
                highKey = key
                high = count

        if highKey == 0:
            debug_log("find2TroopTypesToCover OUT NO HIGH KEY")
            return 0, 0, 0, 0

        requiredRemainder = requiredTroopCount - availableTroops[highKey]
        if requiredRemainder > 0:
            low = 9999
            for key, count in availableTroops.iteritems():
                if key != highKey and requiredRemainder <= count <= low and key not in excludedTroops:
                    lowKey = key
                    low = count

            if lowKey == 0:
                debug_log("find2TroopTypesToCover OUT NO LOW KEY")
                return 0, 0, 0, 0

        debug_log("find2TroopTypesToCover OUT {:d} {:d} {:d} {:d}".format(highKey, availableTroops[highKey], lowKey, requiredRemainder))
        return highKey, availableTroops[highKey], lowKey, requiredRemainder

    def find2TroopTypesBestEffort(self, excludedTroops, availableTroops, requiredTroopCount):
        highKey = 0
        lowKey = 0

        high = 0
        for key, count in availableTroops.iteritems():
            if count > high and key not in excludedTroops:
                highKey = key
                high = count

        if highKey == 0:
            debug_log("find2TroopTypesBestEffort OUT NO HIGH KEY")
            return 0, 0, 0, 0

        requiredRemainder = requiredTroopCount - availableTroops[highKey]
        high = 0
        if requiredRemainder > 0:
            for key, count in availableTroops.iteritems():
                if key != highKey and count > high and key not in excludedTroops:
                    lowKey = key
                    high = count

        lowCount = requiredRemainder
        if high < requiredRemainder:
            lowCount = high

        debug_log("find2TroopTypesBestEffort OUT {:d} {:d} {:d} {:d}".format(highKey, availableTroops[highKey], lowKey, lowCount))
        return highKey, availableTroops[highKey], lowKey, lowCount

    def updateAvailableTroops(self, availableTroops, usedTroops):
        """
        Remove the consumed troops from the total of available troops.
        :param availableTroops:
        :param usedTroops: Array of [troopType,troopCount] sub-arrays
        :return:
        """
        debug_pretty_print(usedTroops, "usedTroops")
        for used in usedTroops:
            troopType = used[0]
            if troopType in availableTroops:
                availableTroops[troopType] = availableTroops[troopType] - used[1]


class NomadAttackFormationBuilder(BaseFormationBuilder):
    def __init__(self, attackFormationTemplate, rangeTroops, meleeTroops, flankCount, middleCount):
        BaseFormationBuilder.__init__(self)
        self.__attackFormationTemplate = attackFormationTemplate
        self.__rangeTroops = rangeTroops
        self.__meleeTroops = meleeTroops
        self.__flankCount = flankCount
        self.__middleCount = middleCount

    def buildFormation(self):

        debug_pretty_print(self.__attackFormationTemplate, 'self.__attackFormationTemplate')
        for wave in self.__attackFormationTemplate:
            index = 0
            maxTypesOnWall = 2
            maxTroopCount = self.__flankCount

            debug_pretty_print(wave, 'wave')

            for wall in [wave['L'], wave['M'], wave['R']]:
                debug_pretty_print(wall, 'wall')
                # Last wall is middle, which means we can put 3
                if wall == 2:
                    maxTypesOnWall = 3
                    maxTroopCount = self.__middleCount

                troops = wall['U']
                if len(troops) > 0:
                    troopType = troops[0][0]
                    troopCount = troops[0][1]

                    debug_log("+++ Formation Template Present (this is a probably the 1st wave) +++")

                    if is_attack_range_troop(troopType):
                        source = self.__rangeTroops
                    else:
                        source = self.__meleeTroops

                    troopArray = self.fillWallWithTroops([], source, troopCount, maxTypesOnWall)
                    if troopArray is None:
                        console("INSUFFICIENT {} troops".format('RANGE' if is_attack_range_troop(troopType) else 'MELEE'))
                        return None
                    wall['U'] = troopArray
                    self.updateAvailableTroops(source, troopArray)
                else:
                    debug_log("+++ No Template (fill in what you can) +++")
                    # Empty wave try to fill it

                    # TODO how to distinguish between walls/waves we want to leave empty vs those we want to fill with any type of available troop

                    allTroops = self.__rangeTroops.copy()
                    allTroops.update(self.__meleeTroops)

                    troopArray = self.fillWallWithTroops([], allTroops, maxTroopCount, maxTypesOnWall, False)
                    if troopArray is not None:
                        wall['U'] = troopArray
                        self.updateAvailableTroops(self.__rangeTroops, troopArray)
                        self.updateAvailableTroops(self.__meleeTroops, troopArray)

                index += 1

        return self.__attackFormationTemplate


def debug_pretty_print(o, s):
    # pretty_print(o, s)
    pass


def debug_log(s):
    # print 'AttackFormationBuilder ' + s
    pass


class BaronAttackFormationBuilder(BaseFormationBuilder):
    WALL_TYPE_NONE = 0
    WALL_TYPE_BURNER = 1
    WALL_TYPE_WALL_BREAKER = 2
    WALL_TYPE_WALL_LOOTER = 3

    def __init__(self, attackFormationTemplate, rangeTroops, meleeTroops, excludedFromBurners, mustFillAllWaves=True):  # , flankCount, middleCount):
        """
        :param attackFormationTemplate:
        :param rangeTroops:
        :param meleeTroops:
        :param excludedFromBurners: Array of troop ids to exclude from burner waves
        :param burners:
        :param mustFillAllWaves:
        :return:
        """
        BaseFormationBuilder.__init__(self)

        self._attackFormationTemplate = attackFormationTemplate
        self._rangeTroops = rangeTroops
        self._meleeTroops = meleeTroops
        self._excludedFromBurners = excludedFromBurners
        self._allAllTroops = None  # Lazy init

        # If the amount of troops indicated in the template should be 100% respected
        # Applies waves after the wall breaking wave (waves sequence: [burner]*,wall breaker,[looting or cy fighters]*)
        self._mustFillAllWaves = mustFillAllWaves

        # self.__flankCount = flankCount
        # self.__middleCount = middleCount

    @classmethod
    def getWaveTypeForWall(cls, troopCount, index, previousWallType):
        debug_log("getWaveTypeForWall IN troopCount={:d} index={:d} previousWallType={}".format(troopCount, index, str(previousWallType)))
        wallType = cls.WALL_TYPE_NONE
        if troopCount == 1:
            wallType = cls.WALL_TYPE_BURNER
        elif troopCount > 1:
            # If previous wave on this wall was BREAKER then this is a LOOTER
            if previousWallType[index] == cls.WALL_TYPE_BURNER:
                wallType = cls.WALL_TYPE_WALL_BREAKER
            elif previousWallType[index] == cls.WALL_TYPE_WALL_BREAKER or previousWallType[index] == cls.WALL_TYPE_WALL_LOOTER:
                wallType = cls.WALL_TYPE_WALL_LOOTER
            else:
                # Could be breaker without on a flank without burners
                # Could be a looter on an empty flank ... can't tell
                # Side effect is we will want to absolutely fill this flank out!
                wallType = cls.WALL_TYPE_WALL_BREAKER

            previousWallType[index] = wallType

        debug_log("getWaveTypeForWall OUT wallType={:d}".format(wallType))
        return wallType

    def buildFormation(self):

        debug_pretty_print(self._attackFormationTemplate, 'self._attackFormationTemplate')

        previousWallType = [0, 0, 0]  # L, R, M

        for wave in self._attackFormationTemplate:
            index = 0

            # TODO this depends on the level of the rbc
            maxTypesOnWall = 2

            debug_pretty_print(wave, 'wave')

            for wall in [wave['L'], wave['R'], wave['M']]:
                debug_pretty_print(wall, 'wall')
                # Last wall is middle, which means we can put 3
                if wall == 2:
                    maxTypesOnWall = 3

                troops = wall['U']

                # Contrary to nomad attacks, the template must contain troops for a wall in a wave in order for it to be filled.
                # Otherwise it is left empty
                #
                # To express a wall+wave in the template that could be filled with whatever is left (melee or range)
                # --> Use: *
                # A variation of this is: use what is available, but make sure to fill the wave completely!
                # --> Could use: +
                # Latter not supported yet
                if len(troops) > 0:
                    # Might support it in a limited manner (1 melee type, 1 range type) in the future if needed
                    if len(troops) > 1:
                        raise Exception("Multiple troop types in template not supported " + str(troops))

                    troopType = troops[0][0]
                    troopCount = troops[0][1]

                    # # Hack to allow for any burner type instead of only range types because of template
                    # if troopCount == 1:
                    #     print "HACK FOR BURNER"
                    #     troopType = '*'

                    wallType = self.getWaveTypeForWall(troopCount, index, previousWallType)

                    if wallType == self.WALL_TYPE_NONE:
                        debug_log("Skipping wall")
                        continue

                    shortCircuitBurner = False
                    # Try to fetch the exact burner specified in the template, if it isn't available then try other troop types
                    if wallType == self.WALL_TYPE_BURNER:
                        # TODO does not work because burners is an array of ids not an array of [troopTypeId,troopCount]
                        # if len(self._burners) > 0:
                        #     print "Burner bypass: using burners dictionary instead of template"
                        #     source = self._burners
                        #     self.updateAvailableTroops(source, [self._burners[0]])
                        #     shortCircuitBurner = True
                        # else:
                        source = self.getAllAvailableTroops()
                        if troopType in source.iterkeys():
                            # No need to update wall since it is exactly what the template specified
                            self.updateAvailableTroops(source, [troops[0]])
                            shortCircuitBurner = True
                        else:
                            console("HACK FOR BURNER")
                            troopType = '*'

                    if not shortCircuitBurner:

                        if troopType == '*':
                            source = self.getAllAvailableTroops()
                        elif is_attack_range_troop(troopType):
                            source = self._rangeTroops
                        else:
                            source = self._meleeTroops

                        mustFillWall = wallType == self.WALL_TYPE_BURNER or wallType == self.WALL_TYPE_WALL_BREAKER
                        excluded = self._excludedFromBurners if wallType == self.WALL_TYPE_BURNER else []
                        troopArray = self.fillWallWithTroops(excluded, source, troopCount, maxTypesOnWall, mustFillWall)
                        if troopArray is None:
                            console("INSUFFICIENT {} troops".format('RANGE' if is_attack_range_troop(troopType) else 'MELEE' if is_attack_melee_troop(troopType) else "*"))
                            return None
                        wall['U'] = troopArray

                        self.updateAvailableTroops(source, troopArray)
                        if source == self._allAllTroops:
                            # Need to remove from specific arrays when the source is the merged array
                            self.updateAvailableTroops(self._rangeTroops, troopArray)
                            self.updateAvailableTroops(self._meleeTroops, troopArray)

                index += 1

        return self._attackFormationTemplate

    def getAllAvailableTroops(self):
        if self._allAllTroops is None:
            self._allAllTroops = self._rangeTroops.copy()
            self._allAllTroops.update(self._meleeTroops)

        return self._allAllTroops


class BaronAttackFormationBuilder2(BaronAttackFormationBuilder):
    def __init__(self, attackFormationTemplate, rangeTroops, meleeTroops, burners, useAttackTroopAsBurnerOfLastResort=False, mustFillAllWaves=False):  # , flankCount, middleCount):
        BaronAttackFormationBuilder.__init__(self, attackFormationTemplate, rangeTroops, meleeTroops, [], mustFillAllWaves)
        self._burners = burners
        self._useAttackTroopAsBurnerOfLastResort = useAttackTroopAsBurnerOfLastResort

    def buildFormation(self):

        debug_pretty_print(self._attackFormationTemplate, 'self._attackFormationTemplate')

        previousWallType = [0, 0, 0]  # L, R, M

        for wave in self._attackFormationTemplate:
            index = 0

            debug_pretty_print(wave, 'wave')

            for i, wall in enumerate([wave['L'], wave['R'], wave['M']]):
                debug_pretty_print(wall, 'wall')

                # TODO this depends on the level of the rbc
                maxTypesOnWall = 2

                # Last wall is middle, which means we can put 3
                if i == 2:
                    maxTypesOnWall = 3

                troops = wall['U']

                # Contrary to nomad attacks, the template must contain troops for a wall in a wave in order for it to be filled.
                # Otherwise it is left empty
                #
                # To express a wall+wave in the template that could be filled with whatever is left (melee or range)
                # --> Use: *
                # A variation of this is: use what is available, but make sure to fill the wave completely!
                # --> Could use: +
                # Latter not supported yet

                # If troop type is more than 1 then the assumption is that it is a melee/range combo otherwise what's the point?

                # TODO what this does not support correctly is the middle wall which would allow 3 where [m, r, r] or [r, m, m] is a valid formation
                # if you don't have enough of a single range or single melee type ... would need to be maxTypesOnWall 1 then 2 or vice-versa
                if len(troops) > 1:
                    maxTypesOnWall = 1

                for x in range(0, len(troops)):
                    # console(">>>>>>>>>>>>>> DEBUG TO REMOVE wall index = {} troop index = {}, maxTypesOnWall = {}".format(str(i), str(x), str(maxTypesOnWall)))
                    troopType = troops[x][0]
                    troopCount = troops[x][1]
                    # console(">>>>>>>>>>>>>> DEBUG TO REMOVE looking for {:d} troops of type {:d}".format(troopCount, troopType))

                    # Idempotent call
                    wallType = self.getWaveTypeForWall(troopCount, index, previousWallType)

                    if wallType == self.WALL_TYPE_NONE:
                        debug_log("Skipping wall")
                        break

                    # Try to fetch the exact burner specified in the template, if it isn't available then try other burner types,
                    # if that fails and we are allowed to use anything then use it
                    if wallType == self.WALL_TYPE_BURNER:
                        burnerTroopType = 0
                        if troopType in self._burners.iterkeys():
                            if troopType in self.getAllAvailableTroops():
                                qty = self.getAllAvailableTroops()[troopType]
                                if qty > 0:
                                    burnerTroopType = troopType
                            else:
                                for troop, qty in self._burners.iteritems():
                                    if qty > 0:
                                        burnerTroopType = troop
                                        break

                        if burnerTroopType > 0:
                            consumed = [[burnerTroopType,1]]
                            wall['U'] = consumed
                            self.updateAvailableTroops(self._burners, consumed)
                            self.updateAvailableTroops(self.getAllAvailableTroops(), consumed)
                            self.updateAvailableTroops(self._rangeTroops, consumed)
                            self.updateAvailableTroops(self._meleeTroops, consumed)
                            break

                        if not self._useAttackTroopAsBurnerOfLastResort:
                            console("INSUFFICIENT BURNERS")
                            return None

                        console("HACK FOR BURNER")
                        troopType = '*'

                    if troopType == '*':
                        source = self.getAllAvailableTroops()
                    elif is_attack_range_troop(troopType):
                        source = self._rangeTroops
                    else:
                        source = self._meleeTroops

                    mustFillWall = wallType == self.WALL_TYPE_BURNER or wallType == self.WALL_TYPE_WALL_BREAKER or self._mustFillAllWaves
                    excluded = []
                    troopArray = self.fillWallWithTroops(excluded, source, troopCount, maxTypesOnWall, mustFillWall)
                    if troopArray is None:
                        console("INSUFFICIENT {} troops".format('RANGE' if is_attack_range_troop(troopType) else 'MELEE' if is_attack_melee_troop(troopType) else "*"))
                        return None

                    if x == 0:
                        wall['U'] = troopArray
                    else:
                        wall['U'].extend(troopArray)

                    self.updateAvailableTroops(source, troopArray)
                    if source == self._allAllTroops:
                        # Need to remove from specific arrays when the source is the merged array
                        self.updateAvailableTroops(self._rangeTroops, troopArray)
                        self.updateAvailableTroops(self._meleeTroops, troopArray)

                index += 1

        return self._attackFormationTemplate
