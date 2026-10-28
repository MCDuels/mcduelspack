"""Where everything on the VS card sits, in title units from the screen centre (x right, y down).

A title is drawn 4x scaled, so one unit is 4 GUI pixels. At the default GUI scale on a 1080p
screen the visible area is about 120 x 67 units; the card is designed for that and the panels
reach far enough to cover GUI scale 2 on a 1440p screen.
"""
SEAM_SLOPE = 0.18      # the seam leans like a forward slash: x = -SEAM_SLOPE * y
SEAM_WIDTH = 0.75
PANEL_REACH = 250      # each panel covers at least this far past the seam
VISIBLE_HALF_WIDTH = 160

COVER_TOP = -136
COVER_HEIGHT = 272

STRIP_HEIGHT = 8
STRIPS_TOP = -36
CENTRE_STRIPS = 9

FACE_PIXEL = 2.5
FACE_TOP = -18
FACE_X = {'p1': -40, 'p2': 20}
FACE_BORDER = 1
FACE_SHADOW = 1.25

NAME_BASELINE = 11
NAME_CAPS = [6, 5, 4, 3]
NAME_WIDTH = 30

MONO_CAP = 1.5
FOOTER_CAP = 1.25
STATS_BASELINE = 14.5
TAG_TOP = 12
TAG_HEIGHT = 4
TAG_BASELINE = 14.75
TAG_PADDING = 2.25
RANKED_BASELINE = 19.5
FOOTER_BASELINE = 30

VS_CAP = 16
VS_BASELINE = 7.5
VS_ECHO_STEP = (1.3125, 0.9375)

KIT_CAPS = [20, 16, 12]
KIT_WIDTH = 94
KIT_MIN_RULE = 41
KIT_RULE_GAP_ABOVE = 4
KIT_RULE_GAP_BELOW = 2
KIT_LABEL_GAP = 5.5

TRACKING = {'label': 0.47, 'stats': 0.28, 'tag': 0.56, 'ranked': 0.66, 'footer': 0.56}


def strips():
    """Bands the card is cut into for the exit: nine thin ones across the middle, two tall ones outside.

    The middle leaves first; neighbours slide in opposite directions.
    """
    bands = [{'top': COVER_TOP, 'bottom': STRIPS_TOP, 'order': 5, 'direction': 1}]
    for index in range(CENTRE_STRIPS):
        top = STRIPS_TOP + index * STRIP_HEIGHT
        bands.append({'top': top, 'bottom': top + STRIP_HEIGHT, 'order': abs(index - CENTRE_STRIPS // 2),
                      'direction': -1 if index % 2 == 0 else 1})
    bottom = STRIPS_TOP + CENTRE_STRIPS * STRIP_HEIGHT
    bands.append({'top': bottom, 'bottom': COVER_TOP + COVER_HEIGHT, 'order': 5, 'direction': 1})
    return bands


def strip_at(y):
    for index, band in enumerate(strips()):
        if band['top'] <= y < band['bottom']:
            return index
    raise ValueError('y = %s is outside every strip' % y)


def seam_x(y):
    return -SEAM_SLOPE * y


def kit_baseline(cap):
    return round(cap * 0.42)
