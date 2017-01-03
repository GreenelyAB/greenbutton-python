# -*- coding: utf-8 -*-

import bisect
import functools
import re

from utils import ESPI_NAMESPACE, getEntity, getLink
from enums import AccumulationBehaviourType, CommodityType, \
    ConsumptionTierType, CurrencyCode, DataQualifierType, FlowDirectionType, \
    KindType, PhaseCode, QualityOfReading, ServiceKind, TimeAttributeType, \
    UomType

from objects import *


class Resource(object):
    def __init__(self, entry):
        self.link_self = getLink(entry, 'self')
        self.link_up = getLink(entry, 'up')
        self.link_related = getLink(entry, 'related', True)
        self.title = getEntity(entry, 'atom:title', lambda e: e.text)

    def __repr__(self):
        return '<%s (%s)>' % (
            self.__class__.__name__, self.title or self.link_self)

    def isParentOf(self, other):
        return (other.link_self in self.link_related
                or other.link_up in self.link_related)


class UsagePoint(Resource):
    def __init__(self, entry, meterReadings=[]):
        super(UsagePoint, self).__init__(entry)
        obj = entry.find('./atom:content/espi:UsagePoint', ESPI_NAMESPACE)
        self.roleFlags = getEntity(
            obj, 'espi:roleFlags', lambda e: int(e.text, 16))
        self.status = getEntity(obj, 'espi:status', lambda e: int(e.text))
        self.serviceCategory = getEntity(
            obj, './espi:ServiceCategory/espi:kind',
            lambda e: ServiceKind(int(e.text)))

        self.meterReadings = set()
        (self.subscriptionId, self.usagePointId) = self.parseLink()

        self.usageSummaries = {}

        for mr in meterReadings:
            if self.isParentOf(mr):
                self.addMeterReading(mr)

    def addMeterReading(self, meterReading):
        assert self.isParentOf(meterReading)
        self.meterReadings.add(meterReading)
        meterReading.usagePoint = self

    def addUsageSummary(self, usageSummary):
        assert self.isParentOf(usageSummary)
        if usageSummary.usageSummaryId not in self.usageSummaries:
            self.usageSummaries[usageSummary.usageSummaryId] = usageSummary
        usageSummary.usagePoint = self

    def parseLink(self):
        searchPattern = re.compile(
            'resource/Subscription/(\d+)/UsagePoint/(\d+)')
        m = searchPattern.search(self.link_self)
        if m:
            return (m.group(1), m.group(2))
        else:
            return (None, None)


class MeterReading(Resource):

    def __init__(
            self, entry, usagePoints=[], readingTypes={}, intervalBlocks=[]):
        super(MeterReading, self).__init__(entry)

        self.usagePoint = None
        self.readingType = None
        self.intervalBlocks = []
        for up in usagePoints:
            if up.isParentOf(self):
                up.addMeterReading(self)
        for rtId in readingTypes:
            rt = readingTypes[rtId]
            if self.isParentOf(rt):
                self.setReadingType(rt)
        for ib in intervalBlocks:
            if self.isParentOf(ib):
                self.addIntervalBlock(r)

    @property
    def intervalReadings(self):
        for ib in self.intervalBlocks:
            for ir in ib.intervalReadings:
                yield ir

    def setReadingType(self, readingType):
        assert self.isParentOf(readingType)
        assert (self.readingType is None
                or self.readingType.link_self == readingType.link_self)
        self.readingType = readingType
        readingType.meterReading = self

    def addIntervalBlock(self, intervalBlock):
        assert self.isParentOf(intervalBlock)
        bisect.insort(self.intervalBlocks, intervalBlock)
        intervalBlock.meterReading = self


class ReadingType(Resource):
    def __init__(self, entry, meterReadings=[]):
        super(ReadingType, self).__init__(entry)
        self.meterReading = None

        obj = entry.find('./atom:content/espi:ReadingType', ESPI_NAMESPACE)
        self.accumulationBehaviour = getEntity(
            obj, 'espi:accumulationBehaviour',
            lambda e: AccumulationBehaviourType(int(e.text)))
        self.commodity = getEntity(obj, 'espi:commodity',
                                   lambda e: CommodityType(int(e.text)))
        self.consumptionTier = getEntity(
            obj, 'espi:consumptionTier',
            lambda e: ConsumptionTierType(int(e.text)))
        self.currency = getEntity(obj, 'espi:currency',
                                  lambda e: CurrencyCode(int(e.text)))
        self.dataQualifier = getEntity(
            obj, 'espi:dataQualifier',
            lambda e: DataQualifierType(int(e.text)))
        self.defaultQuality = getEntity(
            obj, 'espi:defaultQuality',
            lambda e: QualityOfReading(int(e.text)))
        self.flowDirection = getEntity(
            obj, 'espi:flowDirection',
            lambda e: FlowDirectionType(int(e.text)))
        self.intervalLength = getEntity(
            obj, 'espi:intervalLength', lambda e: int(e.text))
        self.kind = getEntity(
            obj, 'espi:kind', lambda e: KindType(int(e.text)))
        self.phase = getEntity(
            obj, 'espi:phase', lambda e: PhaseCode(int(e.text)))
        self.powerOfTenMultiplier = getEntity(
            obj, 'espi:powerOfTenMultiplier', lambda e: int(e.text))
        self.timeAttribute = getEntity(
            obj, 'espi:timeAttribute',
            lambda e: TimeAttributeType(int(e.text)))
        self.tou = getEntity(obj, 'espi:tou', lambda e: TOUType(int(e.text)))
        self.uom = getEntity(obj, 'espi:uom', lambda e: UomType(int(e.text)))
        self.readingTypeId = self.parseLink()

        for mr in meterReadings:
            if mr.isParentOf(self):
                mr.setReadingType(self)

    def parseLink(self):
        readingTypeRe = re.compile('resource/ReadingType/([^\/]+)')
        m = readingTypeRe.search(self.link_self)
        if m:
            return m.group(1)
        return None


class UsageSummary(Resource):

    def __init__(self, entry, usagePoints=[], readingTypes={}):
        super(UsageSummary, self).__init__(entry)
        self.usagePoint = None
        obj = entry.find('./atom:content/espi:UsageSummary', ESPI_NAMESPACE)
        self.billingPeriod = getEntity(
            obj, 'espi:billingPeriod', lambda e: DateTimeInterval(e))
        self.billLastPeriod = getEntity(
            obj, 'espi:billLastPeriod', lambda e: int(e.text) / 100000.0)
        self.currency = getEntity(
            obj, 'espi:currency', lambda e: CurrencyCode(int(e.text)))
        self.overallConsumptionLastPeriod = getEntity(
            obj, 'espi:overallConsumptionLastPeriod',
            lambda e: OverallConsumptionLastPeriod(e, self, readingTypes))

        self.costAdditionalDetailLastPeriods = [
            CostAdditionalDetailLastPeriod(cadlp, self) for cadlp in
            obj.findall('espi:costAdditionalDetailLastPeriod', ESPI_NAMESPACE)
        ]

        _statusTimeStamp = getEntity(
            obj, 'espi:statusTimeStamp', lambda e: e.text)
        if len(_statusTimeStamp) > 10:
            # Timestamp inclues miliseconds
            _statusTimeStamp = _statusTimeStamp[:-3]
        self.statusTimeStamp = datetime.datetime.fromtimestamp(
            int(_statusTimeStamp))
        self.commodity = getEntity(obj, 'espi:commodity',
                                   lambda e: CommodityType(int(e.text)))
        self.tariffProfile = getEntity(
            obj, 'espi:tariffProfile', lambda e: e.text)
        self.readCycle = getEntity(
            obj, 'espi:readCycle', lambda e: e.text)
        _, self.usageSummaryId = self.parseLink()

        for u in usagePoints:
            if u.isParentOf(self):
                u.addUsageSummary(self)

    def parseLink(self):
        usageSummaryRe = re.compile(
            'resource/Subscription/\d+/UsagePoint/(\d+)/UsageSummary/([^\/]+)')
        m = usageSummaryRe.search(self.link_self)
        if m:
            return (m.group(1), m.group(2))
        return None, None


@functools.total_ordering
class IntervalBlock(Resource):
    def __init__(self, entry, meterReadings=[]):
        super(IntervalBlock, self).__init__(entry)
        self.meterReading = None

        obj = entry.find('./atom:content/espi:IntervalBlock', ESPI_NAMESPACE)
        self.interval = getEntity(
            obj, 'espi:interval', lambda e: DateTimeInterval(e))
        self.intervalReadings = sorted(
            [IntervalReading(ir, self) for ir in obj.findall(
                'espi:IntervalReading', ESPI_NAMESPACE)])

        for mr in meterReadings:
            if mr.isParentOf(self):
                mr.addIntervalBlock(self)

    def __eq__(self, other):
        if not isinstance(other, IntervalBlock):
            return False
        return self.link_self == other.link_self

    def __lt__(self, other):
        return self.interval < other.interval


class Customer(Resource):
    def __init__(self, entry):
        super(Customer, self).__init__(entry)
        obj = entry.find(
            './atom:content/espiCustomer:Customer', ESPI_NAMESPACE)
        self.name = getEntity(obj, 'espiCustomer:name', lambda e: e.text)
        self.retailCustomerId = self.parseLink()
        self.customerAccounts = {}

    def parseLink(self):
        retailCustomerRe = re.compile('resource/RetailCustomer/(\d+)')
        m = retailCustomerRe.search(self.link_self)
        if m:
            return m.group(1)
        return None

    def addCustomerAccount(self, ca):
        assert self.isParentOf(ca)
        if ca.customerAccountId not in self.customerAccounts:
            self.customerAccounts[ca.customerAccountId] = ca
        ca.customer = self


class CustomerAccount(Resource):

    def __init__(self, entry, customers={}):
        super(CustomerAccount, self).__init__(entry)

        obj = entry.find(
            './atom:content/espiCustomer:CustomerAccount',
            ESPI_NAMESPACE)
        self.name = getEntity(obj, 'espiCustomer:name', lambda e: e.text)
        self.customer = None
        self.customerAgreements = {}

        retailCustomerId, customerAccountId = self.parseLink()
        self.customerAccountId = customerAccountId

        p = customers.get(retailCustomerId)
        if not p:
            for i in customers.values():
                if i.isParentOf(self):
                    p = i
        if p:
            p.addCustomerAccount(self)

    def parseLink(self):
        customerAccountRe = re.compile(
            'resource/RetailCustomer/(\d+)/Customer/[^/]+/CustomerAccount/(\d+)')
        m = customerAccountRe.search(self.link_self)
        if m:
            return (m.group(1), m.group(2))
        return (None, None)

    def addCustomerAgreement(self, ca):
        assert self.isParentOf(ca)
        if ca.customerAgreementId not in self.customerAgreements:
            self.customerAgreements[ca.customerAgreementId] = ca
        ca.customerAccount = self


class CustomerAgreement(Resource):
    def __init__(self, entry, customerAccounts={}):
        super(CustomerAgreement, self).__init__(entry)
        obj = entry.find(
            './atom:content/espiCustomer:CustomerAgreement',
            ESPI_NAMESPACE)
        self.name = getEntity(obj, 'espiCustomer:name', lambda e: e.text)
        self.signDate = getEntity(
            obj, 'espiCustomer:signDate', lambda e: e.text)
        self.customerAccount = None
        self.serviceLocation = None

        customerAccountId, customerAgreementId = self.parseLink()
        self.customerAgreementId = customerAgreementId

        ca = customerAccounts.get(customerAccountId)
        if not ca:
            for i in customerAccounts.values():
                if i.isParentOf(self):
                    ca = i
        if ca:
            ca.addCustomerAgreement(self)

    def parseLink(self):
        customerAgreementRe = re.compile(
            'resource/RetailCustomer/\d+/Customer/[^/]+/CustomerAccount/(\d+)/CustomerAgreement/(\d+)')
        m = customerAgreementRe.search(self.link_self)
        if m:
            return (m.group(1), m.group(2))
        return (None, None)

    def addServiceLocation(self, serviceLocation):
        if not self.serviceLocation:
            self.serviceLocation = serviceLocation
        serviceLocation.customerAgreement = self


class ServiceLocation(Resource):
    def __init__(self, entry, customerAgreements={}):
        super(ServiceLocation, self).__init__(entry)
        obj = entry.find(
            './atom:content/espiCustomer:ServiceLocation/espiCustomer:mainAddress',
            ESPI_NAMESPACE)
        self.address = getEntity(
            obj, 'espiCustomer:streetDetail/espiCustomer:addressGeneral',
            lambda e: e.text)
        self.zipCode = getEntity(
            obj, 'espiCustomer:townDetail/espiCustomer:code',
            lambda e: e.text.strip())
        self.city = getEntity(
            obj, 'espiCustomer:townDetail/espiCustomer:name',
            lambda e: e.text)
        self.state = getEntity(
            obj,
            'espiCustomer:townDetail/espiCustomer:stateOrProvince',
            lambda e: e.text)
        self.customerAgreement = None

        customerAgreementId, self.serviceLocationId = self.parseLink()
        ca = customerAgreements.get(customerAgreementId)
        if not ca:
            for i in customerAgreements.values():
                if i.isParentOf(self):
                    ca = i
        if ca:
            ca.addServiceLocation(self)

    def parseLink(self):
        serviceLocationRe = re.compile(
            'resource/RetailCustomer/\d+/Customer/[^\/]+/CustomerAccount/\d+/CustomerAgreement/(\d+)/ServiceLocation/([^\/]+)')
        m = serviceLocationRe.search(self.link_self)
        if m:
            return (m.group(1), m.group(2))
        return (None, None)

    def fullAddress(self):
        if self.address:
            return "%s, %s %s %s" % (
                self.address, self.city, self.state, self.zipCode)
        else:
            return ""
