#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import requests
from lxml import etree

def get_calendar_pages():

    calendar_urls = [
        'http://www.cpbl.com.tw/schedule/index/2016-3-01.html?&date=2016-3-01&gameno=01&sfieldsub=&sgameno=01',
        'http://www.cpbl.com.tw/schedule/index/2016-4-01.html?&date=2016-4-01&gameno=01&sfieldsub=&sgameno=01',
        'http://www.cpbl.com.tw/schedule/index/2016-5-01.html?&date=2016-5-01&gameno=01&sfieldsub=&sgameno=01',
        'http://www.cpbl.com.tw/schedule/index/2016-6-01.html?&date=2016-6-01&gameno=01&sfieldsub=&sgameno=01',
        'http://www.cpbl.com.tw/schedule/index/2016-7-01.html?&date=2016-7-01&gameno=01&sfieldsub=&sgameno=01',
        'http://www.cpbl.com.tw/schedule/index/2016-8-01.html?&date=2016-8-01&gameno=01&sfieldsub=&sgameno=01',
        'http://www.cpbl.com.tw/schedule/index/2016-9-01.html?&date=2016-9-01&gameno=01&sfieldsub=&sgameno=01',
        'http://www.cpbl.com.tw/schedule/index/2016-10-01.html?&date=2016-10-01&gameno=01&sfieldsub=&sgameno=01',
    ]

    if not os.path.exists('cache/calendar'):
        os.makedirs('cache/calendar')

    print 'Fetching calendar pages...'

    # Get the pages and convert them into HTML trees
    calendar_pages = []

    for index, url in enumerate(calendar_urls):
        print index + 1, 'of', len(calendar_urls), ':', url

        # Try cache first
        file_name = url.split('/')[-1].split('?')[0]
        cache_path = os.path.join('cache', 'calendar', file_name)

        if os.path.exists(cache_path):
            page = open(cache_path, 'r').read()
            calendar_pages.append(page)
            continue

        # Fetch it
        page = requests.get(url).content
        open(cache_path, 'w').write(page)
        calendar_pages.append(page)

    return calendar_pages


def get_box_pages(box_urls):

    if not os.path.exists('cache/game'):
        os.makedirs('cache/game')

    print 'Fetching box pages...'

    box_pages = []

    for index, url in enumerate(box_urls):
        print index + 1, 'of', len(box_urls), ':', url

        # Try cache first
        tokens = url.split('&')
        game_id = tokens[2].split('=')[1]
        year = tokens[4].split('=')[1]
        file_name = year + '-' + game_id + '.html'
        cache_path = os.path.join('cache', 'game', file_name)

        if os.path.exists(cache_path):
            page = open(cache_path, 'r').read()
            box_pages.append(page)
            continue

        # Fetch it
        page = requests.get(url).content
        open(cache_path, 'w').write(page)
        box_pages.append(page)

    return box_pages


if __name__ == "__main__":

    # Get pages and extract trees
    calendar_pages = get_calendar_pages()
    calendar_trees = [etree.HTML(page) for page in calendar_pages]

    # Extract "block" for each game
    nested_games = [
        tree.xpath("//div[@class='one_block']")
        for tree in calendar_trees
    ]

    # Flatten nested games
    games = [
        game
        for calendar_games in nested_games
        for game in calendar_games
    ]

    # Target: completed games of Lamigo and EDA

    team_images = {
        'Lamigo':       'http://cpbl-elta.cdn.hinet.net/phone/images/team/A02_logo_01.png',
        'EDA':          'http://cpbl-elta.cdn.hinet.net/phone/images/team/B03_logo_01.png',
        'Brothers':     'http://cpbl-elta.cdn.hinet.net/phone/images/team/E02_logo_01.png',
        'Uni-Lions':    'http://cpbl-elta.cdn.hinet.net/phone/images/team/L01_logo_01.png',
    }


    box_urls = []

    for game in games:

        # Must be Lamigo and EDA
        images = game.findall('table/tr/td/img')  # Bug? Must not mention tbody
        sources = [ image.attrib['src'] for image in images ]
        if team_images['Lamigo'] not in sources:
            continue
        if team_images['EDA'] not in sources:
            continue

        # Completed games are with onclick links
        # and postponed games are not.
        if 'onclick' not in game.attrib:
            continue

        # location.href='/games/box.html?&game_type=01&game_id=4&game_date=2016-03-22&pbyear=2016';
        #        0      '     1                                                                  ' 2
        box_url = 'http://www.cpbl.com.tw/' + game.attrib['onclick'].split("'")[1]
        box_urls.append(box_url)

    box_pages = get_box_pages(box_urls)

    # Extract information

    print 'Extract information from box pages...'
    image_to_teams = {
        'http://cpbl-elta.cdn.hinet.net/pad/images/team/A02_logo_01.png': 'Lamigo',
        'http://cpbl-elta.cdn.hinet.net/pad/images/team/B03_logo_01.png': 'EDA',
        'http://cpbl-elta.cdn.hinet.net/pad/images/team/E02_logo_01.png': 'Brothers',
        'http://cpbl-elta.cdn.hinet.net/pad/images/team/L01_logo_01.png': 'Uni-Lions',
    }

    times = []

    for page in box_pages:

        tree = etree.HTML(page)

        # Teams

        elements = tree.xpath('//div[@class="team_part"]/div[@class="m_cell"]/img')
        away_team = image_to_teams[elements[0].attrib['src']]
        home_team = image_to_teams[elements[1].attrib['src']]

        # Date and Location

        elements = tree.xpath('//div[@class="team_part"]/div[@class="t_cell"]')
        date = elements[0].text
        location = elements[1].text

        # Scores

        elements = tree.xpath('//div[@class="score_part"]/div[@class="t_cell"]/span')
        score = elements[0].text

        # Time
        match = re.search('時間: (\d+:\d+)', page)
        time = match.groups()[0]

        times.append(time)

        # Attendees
        match = re.search('觀眾: (\d+)', page)
        attendees = match.groups()[0]

        print away_team, home_team, date, location, score, time, attendees

    times.sort()
    for index, time in enumerate(times):
        print '%02d' % (index + 1), time

