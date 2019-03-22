#!/usr/bin/env python
"""Wikidata sync or follow experiment.

Code to explore the feasibility of maintaining and updating a local
copy of wikidata information based on following the `feedrecentchanges`
API and then getting the entity RDF for each entity (Q##) updated.

Stores a set of graphs for each entity in memory and when there is a new
update attempts to do a diff to see which triples are changed. Has no
support for cleanup or limits of memory -- THIS IS ONLY A TEST SCRIPT THAT
WILL EVENTUALLY USE UP ALL MEMORY IF LEFT RUNNING!
"""

from datetime import datetime
import dateutil.parser
import logging
from lxml import etree
from rdflib.graph import Graph
from rdflib.compare import graph_diff
import re
import requests
import time

# Global state for tracking updates
PREVIOUS_NEWEST_STR = '3000-01-01'  # latest time from last request
UPDATED = {}  # Q number -> last update datetime
GRAPHS = {}  # Q number -> last graph for entity

# API configuration
WIKIDATA_WB_API = 'https://www.wikidata.org/w/api.php'
WIKIDATA_WB_PARAMS = {
    'action': 'feedrecentchanges',
    'format': 'json',
    'formatversion': 2,
    'feedformat': 'atom',
    'days': 0.01,
    'limit': 100  # is 50 actually the max returned from wikidata?
}
WIKIDATA_ENTITY_BASE = 'https://www.wikidata.org/entity/'


def get_updates():
    """Get a list of Q numbers from the wikibase search API.

    Will dedupe this list so that a given Q number is returned only
    once. Will also remove entries that are for updates already
    recorded in the global UPDATES dictionary.
    """
    global PREVIOUS_NEWEST_STR, UPDATED, WIKIDATA_WB_API, WIKIDATA_WB_PARAMS
    r = requests.get(url=WIKIDATA_WB_API, params=WIKIDATA_WB_PARAMS)
    root = etree.fromstring(r.text)
    seen = 0
    updates = []
    oldest_str = None
    newest_str = None
    for entry in root.iterchildren('{http://www.w3.org/2005/Atom}entry'):
        # print(etree.tostring(entry))
        q = entry.find('{http://www.w3.org/2005/Atom}title').text
        updated_str = entry.find('{http://www.w3.org/2005/Atom}updated').text
        if newest_str is None or updated_str > newest_str:
            newest_str = updated_str
        if oldest_str is None or updated_str < oldest_str:
            oldest_str = updated_str
        updated = dateutil.parser.parse(updated_str)
        if not re.match(r'''Q\d+$''', q):
            # This is not an updated entity, ignore
            pass
        elif q in UPDATED and UPDATED[q] >= updated:
            # print("See %s update already" % (q))
            seen += 1
        else:
            updates.append(q)
            # print("Got %s (updated at %s)" % (q, updated))
            UPDATED[q] = updated
    print("%s: Got %d updates (ignored %d already seen)" % (datetime.now(), len(updates), seen))
    if oldest_str > PREVIOUS_NEWEST_STR:
            print("WARNING: Gap between feed dates from %s to %s" % (PREVIOUS_NEWEST_STR, oldest_str))
    PREVIOUS_NEWEST_STR = newest_str
    return updates


def update_graph(q):
    """Update global GRAPHS dictionary with the current data for the given Q number.

    Downloads the entity data from wikidata in Turle form, parses it and then
    does a diff (to stdout) with any current version of that entity.

    FIXME -- THIS IS NOT THE RIGHT WAY TO GET THE GRAPH DATA! DON'T KNOW HOW TO GET
    CURRENT RDF.
    """
    global GRAPHS
    try:
        r = requests.get(url=WIKIDATA_ENTITY_BASE + q, headers={'Accept': 'text/turtle'})
        g_new = Graph()
        g_new.parse(data=r.text, format='turtle')
    except:
        print("Update for %s failed" % (q))
        return
    if q in GRAPHS:
        g_old = GRAPHS[q]
        print("%s: old, %d -> new, %d triples" % (q, len(g_old), len(g_new)))
        in_both, in_old, in_new = graph_diff(g_old, g_new)
        print("%s: < %d, == %d, > %d" % (q, len(in_old), len(in_both), len(in_new)))
        for s, p, o in in_old:
            print("< %s %s %s" % (str(s), str(p), str(o)))
        for s, p, o in in_new:
            print("> %s %s %s" % (str(s), str(p), str(o)))
    else:
        print("%s: new, %d triples" % (q, len(g_new)))
    GRAPHS[q] = g_new


while True:
    # print("Getting updates...")
    for q in get_updates():
        update_graph(q)
    time.sleep(1)
