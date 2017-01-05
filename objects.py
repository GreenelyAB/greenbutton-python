# -*- coding: utf-8 -*-

import datetime
import functools
import re

from enums import CurrencyCode, ItemKind, QualityOfReading, UomType, \
    UOM_SYMBOLS
from utils import getEntity, ESPI_NAMESPACE


@functools.total_ordering
class DateTimeInterval:
    def __init__(self, entity):
        self.duration = getEntity(
            entity, 'espi:duration',
            lambda e: datetime.timedelta(seconds=int(e.text)))
        self.start = getEntity(
            entity, 'espi:start',
            lambda e: datetime.datetime.fromtimestamp(int(e.text)))

    def __repr__(self):
        return '<DateTimeInterval (%s, %s)>' % (self.start, self.duration)

    def __eq__(self, other):
        if not isinstance(other, DateTimeInterval):
            return False
        return (self.start, self.duration) == (other.start, other.duration)

    def __lt__(self, other):
        if not isinstance(other, DateTimeInterval):
            return False
        return (self.start, self.duration) < (other.start, other.duration)


@functools.total_ordering
class IntervalReading:
    def __init__(self, entity, parent):
        self.intervalBlock = parent
        self.cost = getEntity(
            entity, 'espi:cost', lambda e: int(e.text) / 100000.0)
        self.timePeriod = getEntity(
            entity, 'espi:timePeriod',
            lambda e: DateTimeInterval(e))
        self._value = getEntity(entity, 'espi:value', lambda e: int(e.text))

        self.readingQualities = set(
            [ReadingQuality(rq, self) for rq in entity.findall(
                'espi:ReadingQuality', ESPI_NAMESPACE)])

    def __repr__(self):
        return '<IntervalReading (%s, %s: %s %s)>' % (
            self.timePeriod.start, self.timePeriod.duration, self.value,
            self.value_symbol)

    def __eq__(self, other):
        if not isinstance(other, IntervalReading):
            return False
        return (self.timePeriod, self.value) == (other.timePeriod, other.value)

    def __lt__(self, other):
        if not isinstance(other, IntervalReading):
            return False
        return (self.timePeriod, self.value) < (other.timePeriod, other.value)

    @property
    def value(self):
        if (self.intervalBlock is not None and
                self.intervalBlock.meterReading is not None and
                self.intervalBlock.meterReading.readingType is not None and
                self.intervalBlock.meterReading.readingType.powerOfTenMultiplier is not None):
            multiplier = 10 ** self.intervalBlock.meterReading.readingType.powerOfTenMultiplier
        else:
            multiplier = 1
        return self._value * multiplier

    @property
    def cost_units(self):
        if (self.intervalBlock is not None and
                self.intervalBlock.meterReading is not None and
                self.intervalBlock.meterReading.readingType is not None and
                self.intervalBlock.meterReading.readingType.currency is not None):
            return self.intervalBlock.meterReading.readingType.currency
        else:
            return CurrencyCode.na

    @property
    def cost_symbol(self):
        return self.cost_units.symbol

    @property
    def value_units(self):
        if (self.intervalBlock is not None and
                self.intervalBlock.meterReading is not None and
                self.intervalBlock.meterReading.readingType is not None and
                self.intervalBlock.meterReading.readingType.uom is not None):
            return self.intervalBlock.meterReading.readingType.uom
        else:
            return UomType.notApplicable

    @property
    def value_symbol(self):
        return UOM_SYMBOLS[self.value_units]


class ReadingQuality:
    def __init__(self, entity, parent):
        self.intervalReading = parent
        self.quality = getEntity(
            entity, 'espi:quality', lambda e: QualityOfReading(int(e.text)))


class OverallConsumptionLastPeriod:
    def __init__(self, entity, parent, readingTypes):
        self.usageSummary = parent
        self.powerOfTenMultiplier = getEntity(
            entity, 'espi:powerOfTenMultiplier', lambda e: int(e.text))
        self.uom = getEntity(
            entity, 'espi:uom', lambda e: UomType(int(e.text)))
        self._value = getEntity(entity, 'espi:value', lambda e: int(e.text))
        self.readingType = getEntity(
            entity, 'espi:readingTypeRef',
            lambda e: readingTypes.get(self.parseReadingTypeId(e.text)))

    def parseReadingTypeId(self, url):
        # Following "resource/ReadingType/" match any string up to next slash.
        # Example of such a string: NzI6bnVsbDpudWxsOjQ=
        readingTypeRe = re.compile('resource/ReadingType/([^\/]+)')
        m = readingTypeRe.search(url)
        if m:
            return m.group(1)
        return ""

    @property
    def value(self):
        if self.readingType:
            multiplier = 10**self.readingType.powerOfTenMultiplier
        else:
            multiplier = 1
        return self._value * multiplier

    def __repr__(self):
        if self.uom in UOM_SYMBOLS:
            uom = UOM_SYMBOLS[self.uom]
        else:
            uom = UOM_SYMBOLS[UomType.notApplicable]
        return '%s %s' % (self.value, uom)


class CostAdditionalDetailLastPeriodMeasurement:
    def __init__(self, entity, parent):
        self.costAdditionalDetailLastPeriod = parent
        self.powerOfTenMultiplier = getEntity(
            entity, 'espi:powerOfTenMultiplier', lambda e: int(e.text))
        self.uom = getEntity(
            entity, 'espi:uom', lambda e: UomType(int(e.text)))
        self._value = getEntity(entity, 'espi:value', lambda e: int(e.text))

    @property
    def value(self):
        if self.powerOfTenMultiplier:
            multiplier = 10**self.powerOfTenMultiplier
        else:
            multiplier = 1
        return self._value * multiplier

    def __repr__(self):
        if self.uom in UOM_SYMBOLS:
            uom = UOM_SYMBOLS[self.uom]
        else:
            uom = UOM_SYMBOLS[UomType.notApplicable]
        return '%s %s' % (self.value, uom)


class CostAdditionalDetailLastPeriod:
    def __init__(self, entity, parent):
        self.usageSummary = parent
        self.note = getEntity(entity, 'espi:note', lambda e: e.text)
        self.measurement = getEntity(
            entity, 'espi:measurement',
            lambda e: CostAdditionalDetailLastPeriodMeasurement(e, self))
        self.itemKind = getEntity(
            entity, 'espi:itemKind', lambda e: ItemKind(int(e.text)))
