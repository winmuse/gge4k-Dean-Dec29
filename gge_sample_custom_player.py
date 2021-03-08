#!/usr/bin/env python
import time

from gge_client import Client
from gge_constants import *
from gge_utils import console


class SampleCustomPlayer(Client):
    """
    """
    def __init__(self):
        Client.__init__(self)

        # This redefines total troop counts to recruit per kingdom / it controls whether tools should be recruited again

        self._profile = {
            'recruitTroops'       : {'op': True,   'main': True,  'ice':  True,  'sand': True,  'fire': True},
            'recruitDefenseTroops': {'op': True,   'main': True,  'ice':  True,  'sand': True,  'fire': True},
            'recruitOffenseTroops': {'op': True,   'main': True,  'ice':  True,  'sand': True,  'fire': True},
            'rangeOffenseMax'     : {'op': 400,    'main': 300,   'ice':   400,  'sand':  500,  'fire':  500},
            'meleeOffenseMax'     : {'op': 400,    'main': 300,   'ice':   350,  'sand':  400,  'fire':  400},
            'rangeDefenseMax'     : {'op': 400,    'main': 400,   'ice':   400,  'sand':  400,  'fire':  400},
            'meleeDefenseMax'     : {'op': 400,    'main': 400,   'ice':   400,  'sand':  400,  'fire':  400},
            'buildTools'          : {'op': True,   'main': True,  'ice':  True,  'sand': True,  'fire': True}
            }

    # The next 4 method overrides show how to change the default troop type that is recruited

    def getMeleeDefenseType(self, castle):
        # return TROOP_TYPE_VET_HALBERDIER
        return TROOP_TYPE_VET_SPEARMAN

    def getRangeDefenseType(self, castle):
        # return TROOP_TYPE_VET_LONGBOWMAN
        return TROOP_TYPE_VET_BOWMAN

    def getMeleeOffenseType(self, castle):
        # return TROOP_TYPE_VET_TWO_HANDED_SWORDSMAN
        return TROOP_TYPE_VET_MACEMAN

    def getRangeOffenseType(self, castle):
        # return TROOP_TYPE_VET_HEAVY_CROSSBOWMAN
        return TROOP_TYPE_VET_CROSSBOWMAN

    # This overrides the default behaviour and lists the only 2 commanders you want to used for nomads

    def getCommanderForNomadAttack(self, sourceCastle, tower):
        # return self.getCommanderIfAvailable(['Johnny', 'Joye'])
        return self.getCommanderIfAvailable(['Thing Four', 'rbc'])

    # This overrides the default behaviour and lists the commanders you want to used on RBCs in every kingdom

    def getCommanderForAttack(self, sourceCastle, kid, tower, isFortress=False, isNomad=False):
        if kid == KINGDOM_ICE:
            candidates = ['Thing Four', 'rbc']
            cname, cid = self.getCommanderIfAvailable(candidates)

            # If the specified command is not available, then the following will send the 1st free one found.
            # If you don't want this then comment or remove the two lines
            if cname is None:
                return self.findFirstFreeCommander()
            else:
                return cname, cid
        elif kid == KINGDOM_SANDS:
            candidates = ['Sands guy 8']
            cname, cid = self.getCommanderIfAvailable(candidates)

            # If the specified command is not available, then the following will send the 1st free one found.
            # If you don't want this then comment or remove the two lines
            if cname is None:
                return self.findFirstFreeCommander()
            else:
                return cname, cid
        elif kid == KINGDOM_FIRE:
            candidates = ['Fire guy 9']
            cname, cid = self.getCommanderIfAvailable(candidates)

            # If the specified command is not available, then the following will send the 1st free one found.
            # If you don't want this then comment or remove the two lines
            if cname is None:
                return self.findFirstFreeCommander()
            else:
                return cname, cid
        elif kid == KINGDOM_GREEN:
            candidates = ['Berimond guy 1', 'Berimond guy 2']
            cname, cid = self.getCommanderIfAvailable(candidates)

            # If the specified command is not available, then the following will send the 1st free one found.
            # If you don't want this then comment or remove the two lines
            if cname is None:
                return self.findFirstFreeCommander()
            else:
                return cname, cid
        else:  # None defined for green ATM
            candidates = []
            console("No commander specified for " + kingdom_to_string(kid))
        return self.getCommanderIfAvailable(candidates)

    # This overrides how many archers you want to keep in stock to be used as burners on RBCs

    def getArcherMin(self, castle):
        if castle.isIceMain() or castle.isSandMain():
            return 15
        return 0

    # This overrides how many troops to recruit per slot

    def getNumberOfTroopsPerSlot(self, castle, type=None):
        if int(round(time.time())) % 2 == 0:
            return 2
        else:
            return 3

if __name__ == '__main__':
    c = SampleCustomPlayer()
    c.run()
