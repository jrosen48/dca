#!/usr/bin/env python

import requests
import logging
import time
import json


class DonorsChooseResponse:
    """
    Class for donors choose response.  Because the API only allows for 50 record requests at a
    time, I made the class so that calls populate and looks to see if the general metadata was
    scraped via the populated attribute.  If it already has it simply adds the new proposals to
    the proposal attribute.  This may not be the fastest solution and there's almost no error
    handling but you get the idea.  The views of the data -- e.g., as_ascii() -- can just return
    different transformations of the data held in the class

    Usage:
        response = DonorsChooseResponse()
        response.populate(data)

        print response.search_terms
        print response.proposals

    Called by the search_donors_choose wrapper function.
    """

    def __init__(self):
        logging.debug('Initiating DonorsChooseResponse Class')
        self.populated = False
        self.total_proposals = 0
        self.proposals = None
        self.breadcrumb = None
        self.records_per_request = None
        self.search_terms = None
        self.search_url = None

    def populate(self, data):
        if self.populated:
            self.proposals.extend(data['proposals'])
        else:
            self.search_terms = data['searchTerms']
            self.search_url = data['searchURL']
            self.total_proposals = data['totalProposals']
            self.records_per_request = data['max']
            self.breadcrumb = data['breadcrumb']
            self.proposals = data['proposals']
            self.populated = True

    def as_ascii(self):
        pass # Placeholder for new export method


def generate_http_request(keywords, start=0, records=50, api_key='DONORSCHOOSE'):
    """
    Generates the URL request to send to the HTTP endpoint. A lot of the complexity of the
    request handling will have to be incorporated into this function (or subfunctions of it).

    Right now it only takes keywords and searches the entire database. The start and records
    parameters are there to allow you to iterate through the JSON response. The API is set
    up with a buffer of 50 records max per request :/.
    """
    if records > 50:
        raise ValueError('Error: records must be <= 50 per API')
    http_keywords = '+'.join(keywords.split())
    base_url = 'https://api.donorschoose.org/common/json_feed.html?' \
               'APIKey={api_key}' \
               '&keywords="{keywords}"' \
               '&index={index}' \
               '&max={max}'
    url = base_url.format(keywords=http_keywords, index=start, max=records, api_key=api_key)
    return url


def search_donors_choose(keywords):
    """
    This is the outward facing function. Everything else behind it is abstracted away.  It will
    need more complex input as we add more functionality to the request generator.  If this gets
    too complex it may be necessary to make this a more complex object; e.g., a class.

    It works by iterating through the starting position of the response until it finds an empty
    response and busts out the 'while' loop.  It is using the populate method on a response object
    to add the responses as you loop through.  A good test of this looping is a search of 'Hawaii'
    which returns 234 responses:

    response = search_donors_choose('Hawaii')
    print len(response.proposals) == 234  # Should be True!

    """
    records_per_request = 50
    sleep_time = 1
    empty = False
    count = 0
    data = DonorsChooseResponse()
    while not empty:
        index = count * records_per_request
        url = generate_http_request(keywords, start=index, records=records_per_request)
        logging.info('Requesting: %s', url)
        response = requests.get(url).json()
        if len(response['proposals']) < 1:
            empty = True
            continue
        data.populate(response)
        time.sleep(sleep_time)
        count += 1
    return data


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    response = search_donors_choose('Canoga Park') # using their test search

    print response.total_proposals, '==?', len(response.proposals) # check
    print json.dumps(response.proposals, indent=2)