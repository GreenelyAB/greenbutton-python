#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET

from resources import UsagePoint, MeterReading, ReadingType, UsageSummary, \
    IntervalBlock, Customer, CustomerAccount, CustomerAgreement, \
    ServiceLocation
from utils import ESPI_NAMESPACE


def _parse_usages(root):

    usagePoints = []
    for entry in root.findall(
            'atom:entry/atom:content/espi:UsagePoint/../..', ESPI_NAMESPACE):
        up = UsagePoint(entry)
        usagePoints.append(up)

    meterReadings = []
    for entry in root.findall(
            'atom:entry/atom:content/espi:MeterReading/../..', ESPI_NAMESPACE):
        mr = MeterReading(entry, usagePoints=usagePoints)
        meterReadings.append(mr)

    readingTypes = {}
    for entry in root.findall(
            'atom:entry/atom:content/espi:ReadingType/../..', ESPI_NAMESPACE):
        rt = ReadingType(entry, meterReadings=meterReadings)
        if rt.readingTypeId not in readingTypes:
            readingTypes[rt.readingTypeId] = rt

    intervalBlocks = []
    for entry in root.findall(
            'atom:entry/atom:content/espi:IntervalBlock/../..',
            ESPI_NAMESPACE):
        ib = IntervalBlock(entry, meterReadings=meterReadings)
        intervalBlocks.append(ib)

    usageSummaries = {}
    for entry in root.findall(
            'atom:entry/atom:content/espi:UsageSummary/../..', ESPI_NAMESPACE):
        us = UsageSummary(
            entry, usagePoints=usagePoints, readingTypes=readingTypes)
        if us.usageSummaryId not in usageSummaries:
            usageSummaries[us.usageSummaryId] = us

    return usagePoints


def parse_usages(source, file=True):
    """ Parses an xml  file or an xml string.
    :param source: Input to parse, either a filepath or a string with xml.
    :type source: string
    :param file: True if source is a filepath. If source is a string with XML,
        set this to False.
    :type file: boolean
    """
    if file:
        tree = ET.parse(source)
        root = tree.getroot()
    else:
        root = ET.fromstring(source)

    return _parse_usages(root)


def _parse_customers(root):

    customers = {}
    for entry in root.findall(
            'atom:entry/atom:content/espiCustomer:Customer/../..',
            ESPI_NAMESPACE):
        c = Customer(entry)
        if c.retailCustomerId not in customers:
            customers[c.retailCustomerId] = c

    customerAccounts = {}
    for entry in root.findall(
            'atom:entry/atom:content/espiCustomer:CustomerAccount/../..',
            ESPI_NAMESPACE):
        ca = CustomerAccount(entry, customers=customers)
        if ca.customerAccountId not in customerAccounts:
            customerAccounts[ca.customerAccountId] = ca

    customerAgreements = {}
    for entry in root.findall(
            'atom:entry/atom:content/espiCustomer:CustomerAgreement/../..',
            ESPI_NAMESPACE):
        ca = CustomerAgreement(entry, customerAccounts=customerAccounts)
        if ca.customerAgreementId not in customerAgreements:
            customerAgreements[ca.customerAgreementId] = ca

    serviceLocations = {}
    for entry in root.findall(
            'atom:entry/atom:content/espiCustomer:ServiceLocation/../..',
            ESPI_NAMESPACE):
        sl = ServiceLocation(entry, customerAgreements=customerAgreements)
        if sl.serviceLocationId not in serviceLocations:
            serviceLocations[sl.serviceLocationId] = sl
    return customers


def parse_customers(source, file=True):
    """ Parses an xml file or an xml string.
    :param source: Input to parse, either a filepath or a string with xml.
    :type source: string
    :param file: True if source is a filepath. If source is a string with XML,
        set this to False.
    :type file: boolean
    """
    if file:
        tree = ET.parse(source)
        root = tree.getroot()
    else:
        root = ET.fromstring(source)

    return _parse_customers(root)
