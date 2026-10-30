"""Shared explicit matching only; caller supplies its established quantity parser."""

def select_candidate(candidates,selection,quantity):
    if set(selection)!={'mode','sell_A','additional_B','reason'} or not selection['reason']:
        raise ValueError('EXPLICIT_SELECTION_AND_REASON_REQUIRED_NO_DEFAULT')
    mode=selection['mode']
    if mode=='GRID':
        sold=int(quantity(selection['sell_A']));added=int(quantity(selection['additional_B']))
        matches=[c for c in candidates if c['plan'] is not None and int(c['sold_A'])==sold and int(c['additional_B'])==added]
    elif mode in ('HOLD','EXIT_A_KEEP_CASH','FULL_TRANSFER'):
        if selection['sell_A'] is not None or selection['additional_B'] is not None:
            raise ValueError('ENDPOINT_SELECTION_MUST_NOT_HIDE_QUANTITY_OVERRIDE')
        matches=[c for c in candidates if mode in c['kinds']]
    else:
        raise ValueError('SELECTION_MODE_NOT_SUPPORTED')
    if len(matches)!=1:
        raise ValueError('SELECTION_MUST_MATCH_ONE_CURRENT_CANDIDATE')
    return matches[0]
