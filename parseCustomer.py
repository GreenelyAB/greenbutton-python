#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import datetime
import xml.etree.ElementTree as ET

from resources import Customer, CustomerAccount, CustomerAgreement, \
    ServiceLocation
from utils import ESPI_NAMESPACE


def parse_feed(filename):
    # print("Parsing " + str(filename))
    tree = ET.parse(filename)

    customers = {}
    for entry in tree.getroot().findall(
            'atom:entry/atom:content/espiCustomer:Customer/../..',
            ESPI_NAMESPACE):
        # print(str(entry))
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
    cs = parse_feed(sys.argv[1])
    # print(str(cs))
    for c in cs.values():
        print('Customer: %s (%s)' % (c.name, c.retailCustomerId))
        for cac in c.customerAccounts.values():
            print('   Account: %s' % (cac.name))
            for cag in cac.customerAgreements.values():
                print('      Agreement: %s, sign date: %s' % (
                    cag.name, datetime.datetime.fromtimestamp(
                        int(cag.signDate)).strftime('%x')))
                sl = cag.serviceLocation
                if sl:
                    print('         Location: %s' % sl.fullAddress())
