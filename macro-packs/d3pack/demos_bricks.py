"""Demo inputs for brick_build and connect_four: small, deterministic, built in code (no random)."""
def _house():
    B = []
    for x in range(0, 6, 2):
        for z in range(0, 4, 2):
            for y in range(3):
                if (x in (0, 4) or z in (0, 2)) and not (x == 2 and z == 2): B.append({'x': x, 'y': y, 'z': z, 'w': 2, 'd': 2, 'h': 1, 'c': 0 if y < 2 else 2})
    B.append({'x': 0, 'y': 3, 'z': 0, 'w': 6, 'd': 4, 'h': 1, 'c': 3}); return B
def _pyramid(): return [[y, y, y, 6 - 2 * y, 6 - 2 * y, y % 3] for y in range(3)]
def _stairs(): return [{'x': 2 * k, 'y': 0, 'z': 0, 'w': 2, 'd': 2, 'h': k + 1, 'c': k % 3} for k in range(4)]
PAL = ['#c2182b', '#2f6fd8', '#f5c518', '#3b3f4a']
DEMOS = {'brick_house': dict(title='A small house', bricks=_house(), palette=PAL),
         'brick_pyramid': dict(title='A stepped pyramid', bricks=_pyramid(), palette=PAL),
         'brick_stairs': dict(title='A staircase', bricks=_stairs(), palette=PAL, base='#7a8aa0'),
         'connect_four_midgame': dict(title='Connect Four, mid-game', cells=['.......', '.......', '...Y...', '..RY...', '..RR...', '.YRYR..'], last=[3, 2], view='oblique')}
