

def get_formation_for_green_baron_attack(commanderID, level, sourceCastleInGreen, burner="606"):
    message = None

    # EMPTY TEMPLATE
    #
    # message = '[{"L":{"U":[],"T":[]},"R":{"U":[],"T":[]},"M":{"U":[],"T":[]}},' \
    #           '{"L":{"U":[],"T":[]},"R":{"U":[],"T":[]},"M":{"U":[],"T":[]}},' \
    #           '{"L":{"U":[],"T":[]},"R":{"U":[],"T":[]},"M":{"U":[],"T":[]}},' \
    #           '{"L":{"U":[],"T":[]},"R":{"U":[],"T":[]},"M":{"U":[],"T":[]}}]'

    if level == 0:  # 1, 1 victory to level 2 -- totals -- flank: 3, front: 7  -- tools -- flank: 10, front: 10
        # 0, 1 sword, 0
        message = '[{"L":{"U":[],"T":[]},"R":{"U":[],"T":[]},"M":{"U":[[664,7]],"T":[]}},' \
                  '{"L":{"U":[],"T":[]},"R":{"U":[],"T":[]},"M":{"U":[],"T":[]}},' \
                  '{"L":{"U":[],"T":[]},"R":{"U":[],"T":[]},"M":{"U":[],"T":[]}}]'
    elif level == 1:  # 2, 1 victory to level 3 -- totals -- flank: 4, front: 10  -- tools -- flank: 10, front: 10
        # 1 AC, 1 AC, 1 AC
        message = '[{"L":{"U":[],"T":[]},"R":{"U":[],"T":[]},"M":{"U":[[664,7]],"T":[]}},' \
                  '{"L":{"U":[],"T":[]},"R":{"U":[],"T":[]},"M":{"U":[],"T":[]}},' \
                  '{"L":{"U":[],"T":[]},"R":{"U":[],"T":[]},"M":{"U":[],"T":[]}}]'
    else:
        pass

    return message
