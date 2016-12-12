#!/usr/bin/python

import sys
import datetime
import xml.etree.ElementTree as ET

from resources import *

def parse_feed(filename):
    tree = ET.parse(filename)

    customers = {}
    for entry in tree.getroot().findall('atom:entry/atom:content/espiCustomer:Customer/../..', ns):
        c = Customer(entry)
        if c.retailCustomerId not in customers:
            customers[c.retailCustomerId] = c

    customerAccounts = {}
    for entry in tree.getroot().findall('atom:entry/atom:content/espiCustomer:CustomerAccount/../..',ns):
        ca = CustomerAccount(entry,customers=customers)
        if ca.customerAccountId not in customerAccounts:
            customerAccounts[ca.customerAccountId] = ca

    customerAgreements = {}
    for entry in tree.getroot().findall('atom:entry/atom:content/espiCustomer:CustomerAgreement/../..',ns):
        ca = CustomerAgreement(entry,customerAccounts=customerAccounts)
        if ca.customerAgreementId not in customerAgreements:
            customerAgreements[ca.customerAgreementId] = ca

    serviceLocations = {}
    for entry in tree.getroot().findall('atom:entry/atom:content/espiCustomer:ServiceLocation/../..',ns):
        sl = ServiceLocation(entry,customerAgreements=customerAgreements)
        if sl.serviceLocationId not in serviceLocations:
            serviceLocations[sl.serviceLocationId] = sl

#    customerAgreements = {}
#    for entry in tree.getroot().findall('atom:entry/atom:content/espiCustomer:CustomerAgreement/../..',ns):
        
#    serviceLocations = {}
#    for entry in tree.getroot().findall('atom:entry/atom:content/espiCustomer:ServiceLocation/../..',ns):
#        sl = ServiceLocation(entry,customers=customers)

    
#    meterReadings = []    
#    for entry in tree.getroot().findall('atom:entry/atom:content/espi:MeterReading/../..', ns):
#        mr = MeterReading(entry, usagePoints=usagePoints)
#        meterReadings.append(mr)
#
#    readingTypes = []
#    for entry in tree.getroot().findall('atom:entry/atom:content/espi:ReadingType/../..', ns):
#        rt = ReadingType(entry, meterReadings=meterReadings)
#        readingTypes.append(rt)
#
#    intervalBlocks = []
#    for entry in tree.getroot().findall('atom:entry/atom:content/espi:IntervalBlock/../..', ns):
#        ib = IntervalBlock(entry, meterReadings=meterReadings)
#        intervalBlocks.append(ib)
    
    return customers

if __name__ == '__main__':
    cs = parse_feed(sys.argv[1])
    for c in cs.values():
        print 'Customer: %s (%s)'%(c.name,c.retailCustomerId)
        for cac in c.customerAccounts.values():
            print '   Account: %s'%(cac.name)
            for cag in cac.customerAgreements.values():
                print '      Agreement: %s, sign date: %s'\
                    %(cag.name,datetime.datetime.fromtimestamp(int(cag.signDate)).strftime('%x'))
                sl = cag.serviceLocation
                if sl:
                    print '         Location: %s'%sl.fullAddress()
