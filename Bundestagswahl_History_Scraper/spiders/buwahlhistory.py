# -*- coding: utf-8 -*-
""" Copyright (C) 2018 Christian Römer
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
    Contact: https://github.com/thunfischtoast or christian.roemer[ät]posteo.de
"""

import scrapy
import re

class BuwahlhistorySpider(scrapy.Spider):
    name = 'buwahlhistory'
    allowed_domains = ['bundeswahlleiter.de']
    old_format_pages = ['https://www.bundeswahlleiter.de/bundestagswahlen/' + str(x) + '.html' for x in [1949,1953,1957,1961,1965,1969,1972,1976,1980,1983,1987,1990,1994,1998,2002,2005,2009]]
    new_format_pages = ['https://www.bundeswahlleiter.de/bundestagswahlen/' + str(x) + 'ergebnisse/bund-99.html' for x in [2013,2017]]
    
    start_urls = old_format_pages + new_format_pages

    def parse(self, response):
        seat_dict = {} #for saving the number of seats of sitting parties in years >= 2013
        year = "0"
        is_new_year_layout = "201" in response.url
        erststimmen_index = "1"
        erststimmen_percent_index = "2"
        zweitstimmen_index = "3"
        zweitstimmen_percent_index = "4"
        seat_index = "5"
        
        if(is_new_year_layout):
            # When the year is 201X the seats are in a different table, so we have to parse that as well
            year = re.match(r'(\D*)(\d*)(\D*)(\d*)(\D*)', response.url).group(2)
            
            seat_rows = response.xpath("//table[not(contains(@class, 'table-stimmen'))]/tbody/tr")
            for row in seat_rows:
                seat_party = row.xpath("./th/text()").extract()[1]
                seat_party = seat_party.strip()
                
                seat_count = row.xpath("./td[1]/text()").extract_first()
                seat_count = seat_count.strip()
                seat_dict[seat_party] = seat_count
            
            erststimmen_index = "2"
            erststimmen_percent_index = "3"
            zweitstimmen_index = "5"
            zweitstimmen_percent_index = "6"
        else:
            year = re.match(r'(\D*)(\d*)(\D*)', response.url).group(2)
            if(year == '1949'):
                # The first year had not second vote / Zweitstimmen
                zweitstimmen_index = None
                zweitstimmen_percent_index = None
                seat_index = "3"
        
        tbodies = response.xpath("//table[contains(@class, 'table-stimmen')]/tbody")
        relevant_bodies = [1,3] # the relevant parts of the table
        if(is_new_year_layout):
            relevant_bodies = [1]
        for i in relevant_bodies:
            tbody = tbodies[i]
            rows = tbody.xpath("./tr")
            for row in rows:
                party = None
                if(is_new_year_layout):
                    party = row.xpath("./td[1]/text()").extract_first()
                else:
                    party = row.xpath("./th/text()").extract_first()
                if(party is not None):
                    party = party.strip()
                
                # Extract first vote / Erststimmen. If it not present assign 0
                erststimmen = row.xpath("./td[" + erststimmen_index + "]/text()").extract_first()
                if(erststimmen is None):
                    erststimmen = "0"
                erststimmen = erststimmen.strip().replace(".", "").replace("–","0")
                
                erststimmen_percent = row.xpath("./td[" + erststimmen_percent_index + "]/text()").extract_first()
                if(erststimmen_percent is None):
                    erststimmen_percent = "0"
                erststimmen_percent = erststimmen_percent.strip().replace(",", ".").replace("–","0")
                
                if(zweitstimmen_index is not None):
                    # Extract second vote / Zweitstimmen. If it not present assign 0
                    zweitstimmen = row.xpath("./td[" + zweitstimmen_index +"]/text()").extract_first()
                    if(zweitstimmen is None):
                        zweitstimmen = "0"
                    zweitstimmen = zweitstimmen.strip().replace(".", "").replace("–","0")
                    
                    zweitstimmen_percent = row.xpath("./td[" + zweitstimmen_percent_index + "]/text()").extract_first()
                    if(zweitstimmen_percent is None):
                        zweitstimmen_percent = "0"
                    zweitstimmen_percent = zweitstimmen_percent.strip().replace(",", ".").replace("–","0")
                else:
                    zweitstimmen = "0"
                    zweitstimmen_percent = "0"
                
                #Extract the number of seats in parliament. Assign 0 if not present.
                zahl_der_sitze = "0"
                if(is_new_year_layout):
                    if party in seat_dict:
                        zahl_der_sitze = seat_dict[party]
                    else:
                        zahl_der_sitze = "0"
                else:
                    zahl_der_sitze = row.xpath("./td[" + seat_index + "]/text()").extract_first()
                    if(zahl_der_sitze is None):
                        zahl_der_sitze = "0"
                    zahl_der_sitze = zahl_der_sitze.strip().replace("–", "0")
                
                yield BUResult(
                        year = year,
                        party = party,
                        erststimmen = erststimmen,
                        erststimmen_percent = erststimmen_percent,
                        zweitstimmen = zweitstimmen,
                        zweitstimmen_percent = zweitstimmen_percent,
                        zahl_der_sitze = zahl_der_sitze
                    )
                    
                    
class BUResult(scrapy.Item):
    year = scrapy.Field()
    party = scrapy.Field()
    erststimmen = scrapy.Field()
    erststimmen_percent = scrapy.Field()
    zweitstimmen = scrapy.Field()
    zweitstimmen_percent = scrapy.Field()
    zahl_der_sitze = scrapy.Field()