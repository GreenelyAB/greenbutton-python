# -*- coding: utf-8 -*-

ESPI_NAMESPACE = {
    'atom': 'http://www.w3.org/2005/Atom',
    'espi': 'http://naesb.org/espi',
    'espiCustomer': 'http://naesb.org/espi/customer'
}


def getEntity(source, target, accessor=None, multiple=False):
    """ Extracts the named entity from the source XML tree.  `accessor` is a
    function of one argument; if provided and the target entity is found, the
    target will be passed into `accessor` and its result will be returned.  If
    `multiple` is true, the result will be all entities that match (i.e. the
    function will use `findall` instead of `find`).

    :param source: XML (sub)tree
    :type source: etree.Element

    :param target: etree path expression
    :type target: string

    :param accessor: function which processes a single etree.Element and
        returns result
    :type accessor: function(etree.Element)

    :param multiple: whether to call etree.Element.find() or
        etree.Element.findall() on source
    :type multiple: boolean

    :return: accessor(etree.Element) or etree.Element if accessor is None
    """
    if multiple:
        es = source.findall(target, ESPI_NAMESPACE)
        if accessor:
            return [accessor(e) for e in es]
        else:
            return es
    else:
        e = source.find(target, ESPI_NAMESPACE)
        if e is not None and accessor is not None:
            return accessor(e)
        else:
            return e


def getLink(source, relation, multiple=False):
    """ Shorthand for pulling a link with the given "rel" attribute from the
    source. Returns the href attribute content.

    :param source: XML (sub)tree
    :type source: etree.Element

    :param relation: "rel" attribute from source, such as "up", "self" etc. See
        Atom xml schema.
    :type relation: string

    :param multiple: whether to call etree.Element.find() or
        etree.Element.findall() on source
    :type multiple: boolean

    :return: href attribute content
    :rtype: string
    """
    return getEntity(
        source, './atom:link[@rel="%s"]' % relation,
        lambda e: e.attrib['href'], multiple)
