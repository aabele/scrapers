#!/usr/bin/env python

# Script that scrapes company name and phone/fax numbers from the zo.lv html
# source. Use at your own risk.
#
# Dependencies
#
# npm install phantomjs
#
# pip install selenium
# pip install lxml
# pip install requests

# TODO:
# Remove requests dependency
# Remove "print" and configure proper logging

from selenium import webdriver
from lxml import etree
import requests
import json
import os

# Download only first two sitemaps and first 30 records of each sitemap
DEBUG = False

SITEMAP_INDEX_URL = 'http://zo.lv/sitemaps.xml'

# If you need to rerun the script you can set all sucessfully downloaded
# sitemap IDs here so they don't have to be downloaded for the second time
SITEMAP_IGNORE_LIST = range(1, 4)

phantom_config = webdriver.DesiredCapabilities.PHANTOMJS
phantom_config['loadImages'] = False
phantom_config['javascriptEnabled'] = False
phantom_driver = webdriver.PhantomJS(desired_capabilities=phantom_config)


class Parser(object):
    """ Parse values out of HTML code """

    def __init__(self, url):
        print "Getting parsing data from %s" % url
        self.url = url
        self.driver = phantom_driver
        self.driver.get(url)

    def _get_block(self, block_name):

        template = "//div[@class='centerInfo']//*[@itemprop='%s']"

        try:
            el = self.driver.find_elements_by_xpath(template % block_name)
            return el
        except:
            return []

    @staticmethod
    def _format_phone(phone):
        """ Format phone ID """
        phone = phone.replace("+371", '')
        phone = phone.strip().lower()
        try:
            phone = int(phone)
        except:
            return None
        return phone

    def get_page_data(self):

        name = self._get_block('name')
        name = name[0].text if name else ""

        phones = self._get_block('telephone')
        phones = [self._format_phone(p.text) for p in (phones or [])]
        phones = filter(lambda x: x, phones)

        faxes = self._get_block('faxNumber')
        faxes = [self._format_phone(p.text) for p in (faxes or [])]
        faxes = filter(lambda x: x, faxes)

        return [list(set(phones + faxes)), name, self.url]


def _get_zip_urls():
    """ Get all sitemap file urls from sitemap index file """

    urls = []

    def _xml(url):
        r = requests.get(url)
        return etree.fromstring(r.content)

    sitemaps = [s for s in _xml(SITEMAP_INDEX_URL)]
    sitemaps = [s[0].text for s in sitemaps]

    if DEBUG:
        sitemaps = sitemaps[:2]

    for sitemap in sitemaps:
        print "Getting sitemap %s" % sitemap
        urls.append([u[0].text for u in _xml(sitemap)])

    return urls


def save_data(file_name, contents):
    """ Save data as file
    :param file_name: file name
    :param contents: data
    """
    print "Writing data to %s..." % file_name
    contents = json.dumps(contents, indent=4, ensure_ascii=False)
    contents = contents.encode('utf-8')
    db = open(file_name, "w")
    db.write(contents)


def dump_website():

    dirname = 'data'
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    print "Dumping website contents"
    print "Getting sitemap files"

    for i, sitemap in enumerate(_get_zip_urls(), start=1):

        if i in SITEMAP_IGNORE_LIST:
            continue

        print "Getting sitemap %s" % i

        data = []
        length = len(sitemap)
        db_name = "%s/zo.lv.%s.json" % (dirname, i)

        print "Saving to %s" % db_name

        if DEBUG:
            sitemap = sitemap[:30]

        for a, url in enumerate(sitemap, start=1):

            print '%s of %s' % (a, length)

            page = Parser(url)
            page_data = page.get_page_data()
            if page_data[0]:
                data.append(page_data)

            # In case of network problem save already fetched data to file
            # after each 10 http requests
            if a % 10 == 0:
                save_data(db_name, data)

        save_data(db_name, data)


if __name__ == "__main__":
    dump_website()
