#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from parse import parse_customers, parse_usages

if __name__ == '__main__':
    customers = parse_customers(sys.argv[1])
    ups = parse_usages(sys.argv[2])
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
