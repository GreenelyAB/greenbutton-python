#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import xml.etree.ElementTree as ET

from resources import UsagePoint, MeterReading, ReadingType, UsageSummary, \
    IntervalBlock, Customer, CustomerAccount, CustomerAgreement, \
    ServiceLocation
from utils import ESPI_NAMESPACE


def parseUsages(filename):
    tree = ET.parse(filename)

    usagePoints = []
    for entry in tree.getroot().findall(
            'atom:entry/atom:content/espi:UsagePoint/../..', ESPI_NAMESPACE):
        up = UsagePoint(entry)
        usagePoints.append(up)

    meterReadings = []
    for entry in tree.getroot().findall(
            'atom:entry/atom:content/espi:MeterReading/../..', ESPI_NAMESPACE):
        mr = MeterReading(entry, usagePoints=usagePoints)
        meterReadings.append(mr)

    readingTypes = {}
    for entry in tree.getroot().findall(
            'atom:entry/atom:content/espi:ReadingType/../..', ESPI_NAMESPACE):
        rt = ReadingType(entry, meterReadings=meterReadings)
        if rt.readingTypeId not in readingTypes:
            readingTypes[rt.readingTypeId] = rt

    intervalBlocks = []
    for entry in tree.getroot().findall(
            'atom:entry/atom:content/espi:IntervalBlock/../..',
            ESPI_NAMESPACE):
        ib = IntervalBlock(entry, meterReadings=meterReadings)
        intervalBlocks.append(ib)

    usageSummaries = {}
    for entry in tree.getroot().findall(
            'atom:entry/atom:content/espi:UsageSummary/../..', ESPI_NAMESPACE):
        us = UsageSummary(
            entry, usagePoints=usagePoints, readingTypes=readingTypes)
        if us.usageSummaryId not in usageSummaries:
            usageSummaries[us.usageSummaryId] = us

    return usagePoints


def parseCustomers(filename):
    tree = ET.parse(filename)

    customers = {}
    for entry in tree.getroot().findall(
            'atom:entry/atom:content/espiCustomer:Customer/../..',
            ESPI_NAMESPACE):
        c = Customer(entry)
        if c.retailCustomerId not in customers:
            customers[c.retailCustomerId] = c

    customerAccounts = {}
    for entry in tree.getroot().findall(
            'atom:entry/atom:content/espiCustomer:CustomerAccount/../..',
            ESPI_NAMESPACE):
        ca = CustomerAccount(entry, customers=customers)
        if ca.customerAccountId not in customerAccounts:
            customerAccounts[ca.customerAccountId] = ca

    customerAgreements = {}
    for entry in tree.getroot().findall(
            'atom:entry/atom:content/espiCustomer:CustomerAgreement/../..',
            ESPI_NAMESPACE):
        ca = CustomerAgreement(entry, customerAccounts=customerAccounts)
        if ca.customerAgreementId not in customerAgreements:
            customerAgreements[ca.customerAgreementId] = ca

    serviceLocations = {}
    for entry in tree.getroot().findall(
            'atom:entry/atom:content/espiCustomer:ServiceLocation/../..',
            ESPI_NAMESPACE):
        sl = ServiceLocation(entry, customerAgreements=customerAgreements)
        if sl.serviceLocationId not in serviceLocations:
            serviceLocations[sl.serviceLocationId] = sl
    return customers


if __name__ == '__main__':
    print("Python version: " + sys.version)
    print("Python executable: " + sys.executable)
    customers = parseCustomers(sys.argv[1])
    ups = parseUsages(sys.argv[2])
    for up in ups:
        c = customers.get(up.subscriptionId)
        cag = None
        if c:
            for cacId in c.customerAccounts:
                cac = c.customerAccounts[cacId]
                if up.usagePointId in cac.customerAgreements:
                    cag = cac.customerAgreements[up.usagePointId]
        print("UsagePoint (%s) %s %s:" % (
            up.title, up.serviceCategory.name, up.status))
        if c:
            print("Customer: %s" % c.name)
            if cag and cag.serviceLocation:
                print("Location: %s" % cag.serviceLocation.fullAddress())
        else:
            print("Customer: <Unknown>")
        for mr in up.meterReadings:
            print('  Meter Reading (%s) %s:' % (
                mr.title, mr.readingType.uom.name))
            for ir in mr.intervalReadings:
                print('    %s, %s: %s %s' % (
                    ir.timePeriod.start, ir.timePeriod.duration, ir.value,
                    ir.value_symbol)),
                if ir.cost is not None:
                    print('(%s%s)' % (ir.cost_symbol, ir.cost)),
                if len(ir.readingQualities) > 0:
                    print('[%s]' % ', '.join(
                        [rq.quality.name for rq in ir.readingQualities])),
                print()
        for usId in up.usageSummaries:
            us = up.usageSummaries[usId]
            print('  UsageSummary: %s, %s' % (
                us.billingPeriod.start,
                us.billingPeriod.start + us.billingPeriod.duration))
            print("    - Tariff profile: %s" % (us.tariffProfile))
            print("    - Read cycle: %s" % (us.readCycle))
            print("    - Commodity: %s" % (us.commodity.name))
            print("    - Status timestamp: %s" % (us.statusTimeStamp))
            print("    - Bill last period: %s%s" % (
                us.currency.symbol, us.billLastPeriod))
            oclp = us.overallConsumptionLastPeriod
            print("    - Overall consumption last period: %s" % (str(oclp)))
            print("    - Cost Additional Detail:")
            for cadlp in us.costAdditionalDetailLastPeriods:
                print("      %s: %s" % (cadlp.note, str(cadlp.measurement)))
