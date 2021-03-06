# -*- coding: utf-8 -*-
"""
WebVTT's subtitle parser
"""

from pyvtt.vttexc import InvalidItem
from pyvtt.vtttime import WebVTTTime
from pyvtt.comparablemixin import ComparableMixin
from pyvtt.compat import str, is_py2
import re


class WebVTTItem(ComparableMixin):
    """
    WebVTTItem(index, start, end, text, position)

    start, end -> WebVTTTime or coercible.
    text -> unicode: text content for item.
    position -> unicode: raw vtt "display coordinates" string
    """
    ITEM_PATTERN = str('%s --> %s%s\n%s\n')
    TIMESTAMP_SEPARATOR = '-->'

    def __init__(self, index=0, start=None, end=None, text='', position=''):
        try:
            self.index = int(index)
        except (TypeError, ValueError):  # try to cast as int, but it's not mandatory
            self.index = index

        self.start = WebVTTTime.coerce(start or 0)
        self.end = WebVTTTime.coerce(end or 0)
        self.position = str(position)
        self.text = str(text)

    @property
    def duration(self):
        return self.end - self.start

    @property
    def text_without_tags(self):
        return re.compile(r'<[^>]*?>').sub('', self.text)

    @property
    def text_without_keys(self):
        return re.compile(r'{[^>]*?}').sub('', self.text)

    @property
    def text_without_strange_chars(self):
        for c in ["\\i1", "\\i0", "\\b1", "\\b0", "\\b<weight>", "\\u1", "\\u0",
                  "\\s1", "\\s0", "\\bord<size>", "\\xbord<size>",
                  "\\ybord<size>", "\\shad<depth>", "\\xshad<depth>",
                  "\\yshad<depth>"]:
            self.text = self.text.replace(c, '')
        return self.text

    @property
    def text_without_trailing_spaces(self):
        return self.text.strip()

    @property
    def characters_per_second(self):
        characters_count = len(self.text_without_tags.replace('\n', ''))
        try:
            return characters_count / (self.duration.ordinal / 1000.0)
        except ZeroDivisionError:
            return 0.0

    def __str__(self):
        position = ' %s' % self.position if self.position.strip() else ''
        return self.ITEM_PATTERN % (self.start, self.end,
                                    position, self.text)
    if is_py2:
        __unicode__ = __str__

        def __str__(self):
            raise NotImplementedError('Use unicode() instead!')

    def _cmpkey(self):
        return (self.start, self.end)

    def shift(self, *args, **kwargs):
        """
        shift(hours, minutes, seconds, milliseconds, ratio)

        Add given values to start and end attributes.
        All arguments are optional and have a default value of 0.
        """
        self.start.shift(*args, **kwargs)
        self.end.shift(*args, **kwargs)

    @classmethod
    def from_string(cls, source):
        return cls.from_lines(source.splitlines(True))

    @classmethod
    def from_lines(cls, lines):
        if len(lines) < 2:
            raise InvalidItem()
        lines = [l.rstrip() for l in lines]
        index = None
        if cls.TIMESTAMP_SEPARATOR not in lines[0]:
            index = lines.pop(0)
        start, end, position = cls.split_timestamps(lines[0])
        body = '\n'.join(lines[1:])
        return cls(index, start, end, body, position)

    @classmethod
    def split_timestamps(cls, line):
        timestamps = line.split(cls.TIMESTAMP_SEPARATOR)
        if len(timestamps) != 2:
            raise InvalidItem()
        start, end_and_position = timestamps
        end_and_position = end_and_position.lstrip().split(' ', 1)
        end = end_and_position[0]
        position = end_and_position[1] if len(end_and_position) > 1 else ''
        return (s.strip() for s in (start, end, position))
