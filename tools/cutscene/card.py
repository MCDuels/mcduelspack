"""The text on the card: the kit slab, both fighters' names and rank, the kit tag and the footer."""
from . import geometry as g
from .panels import bars
from .type_sets import DISPLAY_CHARS, MONO_CHARS, anton, geist_mono, text_row

DISPLAY_TEXELS_PER_UNIT = 8
MONO_TEXELS_PER_UNIT = 16
BAR_WIDTHS = [1, 2, 4, 8, 16, 32, 64]


def kit_card(font):
    """One set per kit word size, biggest first: the word, the label above it and its two rules."""
    sizes = []
    for cap in g.KIT_CAPS:
        baseline = g.kit_baseline(cap)
        top = baseline - cap
        sizes.append({
            'word': text_row(font, anton(), DISPLAY_CHARS, cap, baseline, DISPLAY_TEXELS_PER_UNIT),
            'label': text_row(font, geist_mono(700), MONO_CHARS, g.MONO_CAP, top - g.KIT_LABEL_GAP,
                              MONO_TEXELS_PER_UNIT, g.TRACKING['label']),
            'rules': [bars(font, 1, top - g.KIT_RULE_GAP_ABOVE, BAR_WIDTHS),
                      bars(font, 1, baseline + g.KIT_RULE_GAP_BELOW, BAR_WIDTHS)],
        })
    return {'width': g.KIT_WIDTH, 'min_rule': g.KIT_MIN_RULE, 'sizes': sizes}


def names(font):
    strip = g.strip_at(g.NAME_BASELINE - 1)
    return {'width': g.NAME_WIDTH,
            'sizes': [text_row(font, anton(), DISPLAY_CHARS, cap, g.NAME_BASELINE, DISPLAY_TEXELS_PER_UNIT,
                               strip=strip) for cap in g.NAME_CAPS]}


def mono_row(font, weight, cap, baseline, tracking):
    return text_row(font, geist_mono(weight), MONO_CHARS, cap, baseline, MONO_TEXELS_PER_UNIT, tracking,
                    g.strip_at(baseline - cap / 2))


def tag(font):
    strip = g.strip_at(g.TAG_TOP + g.TAG_HEIGHT / 2)
    return {'text': mono_row(font, 700, g.MONO_CAP, g.TAG_BASELINE, g.TRACKING['tag']),
            'box': bars(font, g.TAG_HEIGHT, g.TAG_TOP, BAR_WIDTHS, strip),
            'padding': g.TAG_PADDING}
