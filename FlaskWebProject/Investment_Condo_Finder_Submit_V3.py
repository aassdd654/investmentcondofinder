
# coding: utf-8

# In[4]:

import sys

# error category
class ZillowConnectionFail(Exception):

    """
    connection error:
    test exception scenario 1: no internet connection.
    """

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class ZillowError(Exception):

    """
    Error HTTP response error messages referenced from Zillow's API documentation
    http://www.zillow.com/howto/api/GetDeepSearchResults.htm
    """

    """
    code 2 is the test exception scinario 2: invalid Zillow api key, error handling
    there are other error code, but not able to test them all.
    """

    code_list = {'2':
                 """
                 ZWSID parameter was invalid or not specified in the request.\n
                 Contact Li to check the ZWSID in the API call. \n
                 """,
                '508':
                 """
                 No exact match found for address. \n
                 Contact Li to validate the address list. \n
                 """,
                 '7':
                 """
                 Error: this account has reached is maximum number of calls for today. \n
                 Contact Li to switch to another web ID. \n
                 """}

    def __init__(self, error_code):
        self.message = self.code_list[str(error_code)]

    def __str__(self):
        return self.message

    def __unicode__(self):
        return unicode(self.__str__())




# In[26]:

from decimal import Decimal

class Mortgage():

    def __init__(self, downpayment, principal, interest_rate, amortization_period):
        self.downpayment = downpayment
        self.principal = principal
        # yearly interest rate
        self.interest_rate = interest_rate
        # amortization years
        self.amortization_period = amortization_period

    # set a max investment budget in order to select potencial listings that are within this investment budget
    # investment budget = downpayment + max loan(for example, mortgage approval from the bank)
    def getAffordableAmount(self):

        self.affordableamount = float(self.principal + self.downpayment)
        #print(self.affordableamount)

        return self.affordableamount

    """
     mortgage calculation formula referenced from https://en.wikipedia.org/wiki/Mortgage_calculator

      The fixed monthly payment for a fixed rate mortgage is the amount
      paid by the borrower every month that ensures that the loan is paid off in full
      with interest at the end of its term. The monthly payment formula is based on the annuity formula.

    """

    #set a principal value based on the listing price in order to calculate the mortgage payment
    #adjusted_principal = listing estimate price - downpayment

    def getMonthlyPayment(self, adjusted_principal):

        # convert from year interest rate to monthly rate
        monthly_interest_rate = self.interest_rate / (12 * 100.0)

        # convert from amortization year to month
        term = self.amortization_period * 12

        # mortgage formula
        monthly_payment = adjusted_principal * (monthly_interest_rate /
                                       (1 - (1 + monthly_interest_rate) ** (-1 * term )))

        # Convert to decimal and round off to two decimal places.
        monthly_payment = Decimal(monthly_payment)
        monthly_payment = round(monthly_payment, 2)

        return monthly_payment

    # customterm is hard-coded to 12 (months)
    # getInterest() calculate the first year interest for mortgage loan
    def getInterest(self, adjusted_principal, customterm):

        # convert from year interest rate to monthly rate
        monthly_interest_rate = self.interest_rate / (12 * 100.0)

        # get monthly mortgage payment
        monthly_payment = self.getMonthlyPayment(adjusted_principal)

        # initial state of the loop
        begin_balance = adjusted_principal
        total_interest = 0

        for num in range(1, customterm + 1):

            # monthly interest
            interest = round(begin_balance * (monthly_interest_rate), 2)
            #print(interest)

            # term_principal = monthly principal part of the monthly mortgage payment
            term_principal = round(float(monthly_payment) - interest, 2)
            # end_balance = leftover principal
            end_balance = round(begin_balance - term_principal, 2)
            begin_balance = end_balance
            total_interest += interest

        return total_interest





# In[27]:

import os
import time
import sys

#clear the screen
def cls():
    os.system("clear")

class Waitbar():
    def __init__(self):
        self.initial_bar = "|----------|"

    def updateWaitbar(self, percent):
        start = self.initial_bar
        percent_int = int(percent * 10)
        rest_percent_int = 10 - percent_int
        print("loading analysis result |" + "*"*percent_int + "-"*rest_percent_int + "| " + str(percent_int * 10) + "%" )
        time.sleep(0.6)
        cls()
        return


# In[28]:

import sys
# for zillow API
import requests
# for xml.etree is standard library # https://docs.python.org/2/library/xml.etree.elementtree.html
from xml.etree import cElementTree as ElementTree
# for scrapying HOA fee from the zillow link
from bs4 import BeautifulSoup
import time
import re
# scraping sleep timer to avoid the "Please verify you're a human to continue." error
from random import randint
from time import sleep
import random



class Listing():

    """
    data flow to search for proper listings:
    1. run getDeepSearchResults(self, address) to get response
    2. run getListing(self, response) to get all zillow ids(zpids) of the all available listings
    3. in the getListing def, get all listings' attributes:
       ZPID as dict key, all other attributes(price, rental, tax, hoa) as dict values
    """

    def __init__(self, affordable_amount):

        #input the Directory API, Mortgage API, Postings API, Property Details API, Reviews API, Valuation API
        #Your Zillow Web Services Identification (ZWSID) is: X1-ZWz1fvxxv1347f_376md
        self.api_key = 'X1-ZWz1fvxxv1347f_376md' #lisa.chuli@gmail.com

        #backup api_key if above api_key's 1000 calls per day is used up
        #self.api_key = 'X1-ZWz193zt9pz2mj_7zykg' #zillowapi1000@gmail.com

        """
        test exception scinario 2: invalid Zillow api key
        """
        #self.api_key = '1-ZWz193zt9pz2mj_7zykg' # invalid api key

        #fix value for zipcode to meet zillow API requirement
        #self.zipcode = 'San Francisco, CA 94158'

        #get property tax #take the latest data: 2016-2017: 1.1792%
        #reference from http://sftreasurer.org/online-property-tax-payment-faq#taxrate
        self.property_tax_rate = 0.011792

        #get investment budget from class Mortgage.getAffordableAmount()
        self.affordable_amount = affordable_amount


    # set API # https://www.zillow.com/howto/api/GetDeepSearchResults.htm
    def getDeepSearchResults(self, address, zipcode):
        """
        GetDeepSearchResults API
        """
        url = 'http://www.zillow.com/webservice/GetDeepSearchResults.htm'
        params = {
            'address': address,
            'citystatezip': zipcode,
            'zws-id': self.api_key,
            'rentzestimate': True}

        return self.getZillowData(url, params)

    # get API response # generate request content from API and assign the content to self.request
    def getZillowData(self, url, params):

        #get request
        try:
            self.request = requests.get(url=url, params=params,)
            #print('request', self.request) # working

        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.TooManyRedirects,
            requests.exceptions.Timeout):
            raise ZillowConnectionFail('call to Zillow API is failed, please check your connection')

        # convert http requst to readable http response
        try:
            #parse XML using ElementTree
            response = ElementTree.fromstring(self.request.text)
            #print('response', response) # working
            #print('request.text', self.request.text) # working

        except ElementTree.ParseError:
            raise ZillowConnectionFail('the XML response from Zillow listing is not available')


        """
        test exception scinario 2: invalid Zillow api key, error handling
        """
        # Error: invalid or missing ZWSID parameter
        # <message><text>Error: invalid or missing ZWSID parameter</text><code>2</code></message>

        error_code = response.findall('message/code')[0].text
        error_description = response.findall('message/text')[0].text

        if  error_code != '0':
            print('error: ', error_description)
            raise ZillowError(int(error_code))
        #else:
            #print("test successful process")

        return response

    # scraping tool to get HOA data as it is not offered by Zillow API
    # hoa_fee is the yearly strata fee
    def getHoa(self, url):
        # Create a variable with the url
        # Use requests to get the contents
        #print("looking for HOA using scraping tool") #working
        #sleep(randint(1,3))

        headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)AppleWebKit 537.36 (KHTML, Like Gecko) Chrome",
                  "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"}

        r = requests.get(url, headers=headers)

        # Get the text of the request contents
        html_content = r.text
        #print(html_content)

        """
        # set ramdom sleep timer
        count = 0
        while "Please verify you're a human to continue." in html_content and count <= 1:
            count += 1
            #print(count)
            #print("scraper detected, trigger ramdom sleep timer")
            sleep(randint(1,3))
            r = requests.get(url)
            html_content = r.text
        """

        # Convert the html content into a beautiful soup object
        soup = BeautifulSoup(html_content, 'lxml')

        #Sample text from Zillow request: """<div class="hdp-fact-ataglance-value">$"""
        x = 'div'
        div_list = soup.find_all(x)
        hoa_fee = None

        #print(html_content)

        if "Please verify you're a human to continue." in html_content:
            hoa_fee = "the scraper tool got detected"
        else:
            #go throught every div that may contains HOA fee.
            for div in div_list:

                #check if HOA is displayed in the http
                if """<div class="hdp-fact-ataglance-value">$""" in str(div):

                    #allocate the begining of the HOA fee display position
                    position = str(div).find("""<div class="hdp-fact-ataglance-value">$""")

                    # len("<div class="hdp-fact-ataglance-value">$" = 39)
                    hoa_value = str(div)[(position + 39) : (position + 39 + 3)]

                    #print('source hoa value', hoa_value)

                    # monthly HOA * 12 months
                    # only keep number, remove '/'
                    hoa_value = re.sub("[^0-9]", "", hoa_value)
                    hoa_fee = float(hoa_value) * 12
                    #print("hoa fee found!", hoa_fee)



                # check if valid hoa fee maintained on the zillow listing, sample text is "No Data"
                # found it is not necessary to review the
                """
                elif ""<div class="hdp-fact-ataglance-value">"" in str(div):
                    #allocate the begining of the HOA fee display position
                    position = str(div).find(""<div class="hdp-fact-ataglance-value">"")
                    # len("<div class="hdp-fact-ataglance-value">" = 38)
                    hoa_value = str(div)[(position + 38) : (position + 39 + 10)]

                    if 'No Data' in hoa_value:
                        hoa_fee = "not maintained in zillow"
                        #print('no HOA maintained for this listing')


                    else:
                        #print('other missing hoa reason', hoa_value)
                        hoa_fee = "not maintained in zillow"
                """


        return hoa_fee



    # extract listing details from all available listings at one address.
    # the listing that misses any of the required information is ignored
    def getListing(self, response):

        """
        data flow:
        'zpid': 'result/zpid', # Required
        'home_detail_link': 'result/links/homedetails', #used for reference of HOA fee extraction
        'hoa' is extracted from def getHoa(self, url)
        'tax_assessment': 'result/taxAssessment', # Required
        'zestimate_amount': 'result/zestimate/amount',# Required function as estimate selling price.
        'rentzestimate_amount': 'result/rentzestimate/amount', # Required
        'address':'result/address/street' # optional reference for later on map interface

        data structure:
        listing is a dictionary list
        {ZPID as dict key : all other attributes(price, rental, tax, hoa) as dict values}
        """


        listings = {}

        for listing in response.iter('result'):
            #time.sleep()
            for temp_zpid in listing.findall('zpid'):
                zpid = temp_zpid.text
                #print('zpid', zpid)
                for temp_zestimate_amount in listing.findall('zestimate/amount'):
                    #print("temp_zestimate_amount.text", temp_zestimate_amount.text)
                    if temp_zestimate_amount.text != None:
                        zestimate_amount = temp_zestimate_amount.text
                        #print('zestimate_amount', zestimate_amount) #working
                        for temp_address in listing.findall('address/street'):
                            address = temp_address.text
                            #print('extract address', address)
                            price_estimate = float(zestimate_amount)
                            #add all attributes into listings dictionary
                            listings[zpid] = [price_estimate, address]
                            #print(listings)

        return listings



    # consolidate all listings from the address list
    def getAllListings(self, addresslist, zipcode):

        #print('test begin')
        all_listings = {}
        #print("-"*50)
        #print('going through', len(addresslist), 'address(es)')


        #print("-"*50)
        #print('searching for the estimated selling price of every listing found')

        #print("-"*50)
        for address in addresslist:
            #print('all listings addresses', address)
            new_listings = self.getListing(self.getDeepSearchResults(address, zipcode))
            #print('found ' + str(len(new_listings)) + ' listing(s) ' + address )

            all_listings.update(new_listings)

        #print("-"*50)
        #print('found ' + str(len(all_listings)) + ' listing(s) in total')

        #print("-"*50)
        #print('start reviewing...(￣(エ)￣)ゞ...')
        #time.sleep(2)

        #print(all_listings)
        return all_listings


    #class Mortgage() - getAffordableAmount(self)

    def getAffordableListings(self, all_listings):

        # make the affordable_listings as dictionary
        # dict.key = zpid
        # dict.value = [strata fee, tax fee, rentestimate]
        affordable_listings = {}

        # filter the affordable listings only.
        # use zestimate_amount
        for key, value in all_listings.items():

            #print(key, value)
            #print(all_listings[key][3])

            if all_listings[key][0] <= self.affordable_amount:
                #print(key, value)
                #print(all_listings[key][0])
                affordable_listings.update({key: value})

        if len(affordable_listings) > 0:
            #print("-"*50)
            #print("found " + str(len(affordable_listings)) + " listing(s) within your investment budget")
            #time.sleep(2)
            return affordable_listings

        elif len(affordable_listings) == 0:

            #print("-"*50)
            #print("no advisable listing with given investment budget")
            return affordable_listings




    # consolidate all listings from the address list
    def getAffordableListingsProperty(self, affordable_listings, zipcode):

        all_affordable_listings = {}

        x = list(affordable_listings.values())
        #[[a, b], [a1, b1]]
        #print(x) #working.
        affordable_address_list = []
        for value in x:
            affordable_address_list += [value[1]]
        #print(affordable_address_list)
        all_affordable_listings_property = {}


        #print("-"*50)
        #print("retrieving estimated rental income, estimated property tax and listed strata fee")
        #time.sleep(2)
        #cls()
        #waitbar setting
        #waitbar_full = len(affordable_address_list)
        #print(waitbar_full)
        #count_waitbar = 0

        #print("-"*50)
        for address in affordable_address_list:
            #print(address)
            #count_waitbar += 1
            #print("count bar", count_waitbar)
            #percentage = round(count_waitbar / waitbar_full, 2)
            #print("percentage", percentage)
            #Waitbar().updateWaitbar(percentage)

            new_affordable_listings = self.getListingProperty(affordable_listings, self.getDeepSearchResults(address, zipcode))
            #print('found ' + str(len(new_affordable_listings)) + ' listing(s) on ' + address )

            all_affordable_listings.update(new_affordable_listings)

        #print('pass ' + str(len(affordable_listings) - len(all_affordable_listings)) + ' listing(s) due to missing rental and tax information')
        #print('found ' + str(len(all_affordable_listings)) + ' listing(s) with complete information in total')

        #print(all_affordable_listings)
        return all_affordable_listings


    def getListingProperty(self, affordable_listings, response):

        """
        data flow:
        'zpid': 'result/zpid', # Required
        'home_detail_link': 'result/links/homedetails', #used for reference of HOA fee extraction
        'hoa' is extracted from def getHoa(self, url)
        'tax_assessment': 'result/taxAssessment', # Required
        'zestimate_amount': 'result/zestimate/amount',# Required function as estimate selling price.
        'rentzestimate_amount': 'result/rentzestimate/amount', # Required
        'address':'result/address/street' # optional reference for later on map interface

        data structure:
        listing is a dictionary list
        {ZPID as dict key : all other attributes(price, rental, tax, hoa) as dict values}
        """

        # make the affordable_listings as dictionary
        # dict.key = zpid
        # dict.attribute => listings[zpid] = [price_estimate]
        affordable_listings_property = {}
        affordable_zpids = affordable_listings.keys()
        #print(affordable_listings.keys())

        for listing in response.iter('result'):

            for temp_zpid in listing.findall('zpid'):
                zpid = temp_zpid.text

                #check only the affordable zpid
                if zpid in affordable_zpids:
                    #print('zpid', zpid)

                    for temp_home_detail_link in listing.findall('links/homedetails'):
                        # convert to hoa tracable link:
                        home_detail_link = temp_home_detail_link.text
                        home_detail_link = home_detail_link + '?fullpage=true'
                        #print(' home_detail_link',  home_detail_link) #working


                        #use timer to pretend as human for scraper tool
                        timer = random.randint(1, 3)
                        time.sleep(timer)

                        #get hoa value from scraper tool
                        hoa = self.getHoa(home_detail_link)
                        #print('extract HOA data', hoa)


                        # validate the HOA fee
                        # if the HOA is not found but the rental income can cover all other fees, the listing is output as incomplete deal


                        if type(hoa)== float:
                            #print("got hoa fee")

                            for temp_tax_assessment in listing.findall('taxAssessment'):


                                tax_assessment = temp_tax_assessment.text
                                #print('tax_assessment', tax_assessment) # working

                                for temp_rentzestimate_amount in listing.findall('rentzestimate/amount'):


                                    rentzestimate_amount = temp_rentzestimate_amount.text
                                    #print('rentzestimate_amount', rentzestimate_amount)
                                    # convert the tax assessment value to one year property tax value
                                    property_tax = round(float(tax_assessment) * self.property_tax_rate,2)
                                    rental_estimate = float(rentzestimate_amount) * 12
                                    price_estimate = affordable_listings[zpid][0]
                                    hoa = self.getHoa(home_detail_link)
                                    address = affordable_listings[zpid][1]

                                    #add all attributes into listings dictionary
                                    affordable_listings_property[zpid] = [home_detail_link,
                                                                          property_tax,
                                                                          rental_estimate,
                                                                          price_estimate,
                                                                          hoa,
                                                                          address,]


                        elif hoa == "the scraper tool got detected":

                            for temp_tax_assessment in listing.findall('taxAssessment'):

                                tax_assessment = temp_tax_assessment.text
                                #print('tax_assessment', tax_assessment) # working

                                for temp_rentzestimate_amount in listing.findall('rentzestimate/amount'):

                                    rentzestimate_amount = temp_rentzestimate_amount.text
                                    #print('rentzestimate_amount', rentzestimate_amount)
                                    # convert the tax assessment value to one year property tax value
                                    property_tax = round(float(tax_assessment) * self.property_tax_rate,2)
                                    rental_estimate = float(rentzestimate_amount) * 12
                                    price_estimate = affordable_listings[zpid][0]
                                    hoa = self.getHoa(home_detail_link)
                                    address = affordable_listings[zpid][1]

                                    #add all attributes into listings dictionary
                                    affordable_listings_property[zpid] = [home_detail_link,
                                                                          property_tax,
                                                                          rental_estimate,
                                                                          price_estimate,
                                                                          hoa,
                                                                          address,]

                        """

                        elif hoa == 'not maintained in zillow':

                            for temp_tax_assessment in listing.findall('taxAssessment'):

                                tax_assessment = temp_tax_assessment.text
                                #print('tax_assessment', tax_assessment) # working

                                for temp_rentzestimate_amount in listing.findall('rentzestimate/amount'):

                                    rentzestimate_amount = temp_rentzestimate_amount.text
                                    #print('rentzestimate_amount', rentzestimate_amount)
                                    # convert the tax assessment value to one year property tax value
                                    property_tax = round(float(tax_assessment) * self.property_tax_rate,2)
                                    rental_estimate = float(rentzestimate_amount) * 12
                                    price_estimate = affordable_listings[zpid][0]
                                    hoa = self.getHoa(home_detail_link)
                                    address = affordable_listings[zpid][1]

                                    #add all attributes into listings dictionary
                                    affordable_listings_property[zpid] = [home_detail_link,
                                                                          property_tax,
                                                                          rental_estimate,
                                                                          price_estimate,
                                                                          hoa,
                                                                          address,]
                        """


        #print(affordable_listings_property)

        return affordable_listings_property







# In[29]:

class Deal():


    judgement = ["Good Deal", "Perfect Deal", 'Pass', 'Incomplete Good Deal', 'Incomplete Perfect Deal']

    def __init__(self, downpayment, principal, interest_rate, amortization_period):
        self.downpayment = downpayment
        self.principal = principal
        self.interest_rate = interest_rate
        self.amortization_period = amortization_period


    def getAffordableAmount(self):

        self.affordable_amount= float(Mortgage(self.downpayment,
                                         self.principal,
                                         self.interest_rate,
                                         self.amortization_period).getAffordableAmount())
        return self.affordable_amount


    def getListing(self, zipcode):

        if zipcode == 'San Francisco, CA 94158':
            #address_list = ['330 Mission Bay Blvd N'] # 94158

            """
            # test scenario : address list
            """

            address_list = ['718 Long Bridge St',
                            '435 China Basin St',
                            '875 Vermont St',
                            '330 Mission Bay Blvd N']

            # add explain how the full address will work

            """
            # test scenario:
            # Search for all listing for zipcode: 94158

            # using address_list_94158.txt
            all_address_list = []
            with open('address_list_94158.txt') as f:
                for line in f:
                    #print(line[:-2])
                    newline = line[:-1]
                    all_address_list += [newline]
                # test only for limited address to avoid API limits
                address_list = all_address_list[6127:6229]
                print(type(all_address_list[6228]))
            """


        elif zipcode == 'San Francisco, CA 94103':
            #'1160 Mission St UNIT 2213'
            #'1160 Mission St UNIT 1409'
            #'60 Rausch St APT 406'
            #'1328 Mission St UNIT 4'
            #'1150 Folsom St UNIT 1'
            #'57 Woodward St # A'
            address_list = ['1160 Mission St',
                            '360 10th St',
                            '1328 Mission St UNIT 4',
                            '1150 Folsom St',
                            '356 12th St',
                            '57 Woodward St',
                            '60 Rausch St',
                            '426 14th St'] # 94103

        elif zipcode == 'San Francisco, CA 94105':
            # '301 Mission St APT 24D'
            address_list = ['201 Harrison St APT 1126',
                            '355 1st St',
                            '338 Spear St UNIT 31A',
                            '338 Spear St UNIT 26G',
                            '333 Main St',
                            '300 Beale St',
                            '425 1st St',
                            '501 Beale St PH 1D',
                            '38 Bryant St APT 702',
                            '318 Main',
                            '400 Spear St'] # 94105

        elif zipcode == 'San Francisco, CA 94107':
            address_list = ['2250 24th St',
                            '875 Vermont St',
                            '116 Connecticut St'] # 94107


        all_listings = Listing(self.affordable_amount).getAllListings(address_list, zipcode)
        self.affordable_listings = Listing(self.affordable_amount).getAffordableListings(all_listings)
        self.all_affordable_listings = Listing(self.affordable_amount).getAffordableListingsProperty(self.affordable_listings, zipcode)


        return self.all_affordable_listings

    def getUpdatedInterest(self):


        """
        #before getUpdatedInterest(): sample:
        listings[zpid] = [home_detail_link,
                          property_tax,
                          rental_estimate,
                          price_estimate,
                          hoa,
                          address,]

        #after getUpdatedInterest(): sample:
        listings[zpid] = [home_detail_link,
                          property_tax,
                          rental_estimate,
                          price_estimate,
                          hoa,
                          address,
                          interest of the first year loan,
                          principal of the first year loan]
        """


        for key, value in self.all_affordable_listings.items():

            principal = value[3] - self.downpayment
            #print(principal)
            if principal > 0:
                new_mortgage = Mortgage(self.downpayment, principal, self.interest_rate, self.amortization_period)

                # getInterest(self, adjusted_principal, customterm)
                # customterm is set to 12, as to get the first year interest and mortgage payment
                interest = round(new_mortgage.getInterest(principal, 12), 2)

                #update pay_principal into listing details
                pay_principal = float(new_mortgage.getMonthlyPayment(principal) * 12) - float(interest)
                #print(interest)y
                self.all_affordable_listings[key] = value + [round(interest, 2)] + [round(pay_principal, 2)]
            else:
                #print("downpayment is too large!")
                self.all_affordable_listings[key] = value + [0] + [0]


        return self.all_affordable_listings


        """
        before calculation: listing sample:
        listings[zpid] = [home_detail_link,
                          property_tax,
                          rental_estimate,
                          price_estimate,
                          hoa,
                          address,]

        after calculation: listing sample:
        listings[zpid] = [0.home_detail_link,
                          1.property_tax,
                          2.rental_estimate,
                          3.price_estimate,
                          4.hoa,
                          5.address,
                          6.interest of the first year loan,
                          7.principal of the first year loan
                          8.judgement
                          9.gross_income (rental_estimate - all expenses(interest, property_tax, hoa))
                          10.net_income profit (rental_estimate - all expenses(interest, property_tax, hoa) - principal)
                          11.coverage percentage of principal/rental
        """

    def compare(self):


        for key, value in self.all_affordable_listings.items():
            # if HOA is valid
            # print(key, value)
            if type(value[4]) == float:

                # scenairo: mortage loan = 0 (0 value[7] principal, 0 value[6] interest), downpayment convers all listing price:
                if value[7] == 0:
                    #print("downpayment is too large!")
                    # Scenario: rental income is able to cover expenses.
                    all_expense = value[1] + value[4]
                    #rental_estimate - all expenses(property_tax, hoa)
                    gross_income = round((value[2] - all_expense), 2)
                    #rental_estimate - all expenses(property_tax, hoa)
                    net_income = round(gross_income, 2)


                    # Scenario: no principal and rental_estimate covers 100% all expenses, set judgement "Perfect Deal"
                    if net_income >= 0:
                        value = value + [self.judgement[1] + " and no mortgage needed"] + [gross_income] + [net_income] + [100]
                        self.all_affordable_listings[key] = value


                # scenairo: mortgage loan > 0
                else:
                    # Scenario: rental income is able to cover expenses.
                    all_expense = value[6] + value[1] + value[4]
                    #rental_estimate - all expenses(interest, property_tax, hoa)
                    gross_income = round((value[2] - all_expense), 2)
                    #rental_estimate - all expenses(interest, property_tax, hoa) - principal
                    net_income = round(gross_income - value[7], 2)

                    if gross_income > 0:
                        # Scenario: rental_estimate covers 100% the principal and more, set judgement "Perfect Deal"
                        if net_income >= 0:
                            value = value + [self.judgement[1]] + [gross_income] + [net_income] + [round(100 * gross_income/value[7], 2)]
                            self.all_affordable_listings[key] = value
                        else:
                            # Scenario: rental_estimate covers less than 100% the principal, set judgement "Good Deal"
                            value = value + [self.judgement[0]] + [gross_income] + [net_income] + [round(100 * gross_income/value[7], 2)]
                            self.all_affordable_listings[key] = value


                    else:
                        # Scenario: rental income is not able to cover expenses. set judgement "Pass"
                        value = value + [self.judgement[2]] + [gross_income] + [net_income] + [round(100 * gross_income/value[7], 2)]
                        self.all_affordable_listings[key] = value
            else:
                #if HOA data is not valid, then only consider the listings which can cover the principal.
                #Additionally, ask user to verify the HOA with professionals:


                # scenairo: mortage loan = 0 (0 value[7] principal, 0 value[6] interest), downpayment convers all listing price:
                # Scenario:Incomplete Deal"
                if value[7] == 0:
                    #print("downpayment is too large!")
                    # Scenario: rental income is able to cover expenses.
                    incomplete_expense = value[1]
                    #rental_estimate - all expenses(interest, property_tax, hoa)
                    incomplete_gross_income = round((value[2] - incomplete_expense), 2)
                    incomplete_net_income = round((incomplete_gross_income - value[7]), 2)

                    if incomplete_gross_income > 0:
                        if incomplete_net_income > 0:
                            value = value + [self.judgement[4]] + [incomplete_gross_income] + [incomplete_net_income] + [100]
                            self.all_affordable_listings[key] = value
                        else:
                            value = value + [self.judgement[3]] + [incomplete_gross_income] + [incomplete_net_income] + [100]
                            self.all_affordable_listings[key] = value

                    else:
                        # incomplete info, incomplete_gross_income is negative
                        value = value + [self.judgement[2]] + [incomplete_gross_income] + [incomplete_net_income] + [100]
                        self.all_affordable_listings[key] = value

                # Scenario:Incomplete Deal"
                else:
                    # Scenario: rental income is able to cover expenses.
                    all_expense = value[6] + value[1]
                    #rental_estimate - all expenses(interest, property_tax, hoa)
                    incomplete_gross_income = round((value[2] - all_expense), 2)
                    #rental_estimate - all expenses(interest, property_tax, hoa) - principal
                    incomplete_net_income = round(incomplete_gross_income - value[7], 2)
                    #print("all_expense", all_expense)
                    #print("incomplete_gross_income", incomplete_gross_income)
                    #print("incomplete_net_income", incomplete_net_income)
                    if incomplete_gross_income > 0:
                        if incomplete_net_income > 0:
                            value = value + [self.judgement[4]] + [incomplete_gross_income] + [incomplete_net_income] + [round(100 * incomplete_gross_income/value[7], 2)]
                            self.all_affordable_listings[key] = value
                            #print("key", key)
                            #print("value", value)
                        else:
                            value = value + [self.judgement[3]] + [incomplete_gross_income] + [incomplete_net_income] + [round(100 * incomplete_gross_income/value[7], 2)]
                            self.all_affordable_listings[key] = value
                    else:
                        # incomplete info, incomplete_gross_income is negative
                        value = value + [self.judgement[2]] + [incomplete_gross_income] + [incomplete_net_income] + [round(100 * incomplete_gross_income/value[7], 2)]
                        self.all_affordable_listings[key] = value

        return self.all_affordable_listings


# In[43]:

## import itertools
import threading
import time
import sys

def display_investment_budget(downpayment, principal, interest_rate, amortization_period):
    downpayment = float(downpayment)
    principal = float(principal)
    interest_rate = float(interest_rate)
    amortization_period = int(amortization_period)
    deal = Deal(downpayment, principal, interest_rate, amortization_period)
    affordable_amount = deal.getAffordableAmount()
    return affordable_amount

def find_valuable_listing(zipcode, downpayment, principal, interest_rate, amortization_period):
    downpayment = float(downpayment)
    principal = float(principal)
    interest_rate = float(interest_rate)
    amortization_period = int(amortization_period)

    deal = Deal(downpayment, principal, interest_rate, amortization_period)

    #deal = Deal(200000, 850000, 3.75, 30) # for quick testing

    affordable_amount = deal.getAffordableAmount()

    listings = deal.getListing(zipcode)
    result = []

    if len(listings) > 0:

        interest = deal.getUpdatedInterest()
        final_result = deal.compare()
        #print('analyzing ' + str(len(final_result)) + ' deal(s)...')
        #count = 0
        #store output result for web display
        #for example: result = {{zpid: [partial of attributes]}, {listng2: [partial of attributes]}}

        for key, value in final_result.items():

            #count += 1
            """
            listing sample:
            listings[zpid] = [0.home_detail_link,
                              1.property_tax,
                              2.rental_estimate,
                              3.price_estimate,
                              4.hoa,
                              5.address,
                              6.interest of the first year loan,
                              7.principal of the first year loan
                              8.judgement : ["Good Deal (•◡•)", "Perfect Deal [̲̅$̲̅(̲̅5̲̅)̲̅$̲̅]", 'Pass', 'Incomplete']
                              9.gross_income (rental_estimate - all expenses(interest, property_tax, hoa))
                              10.net_income profit (rental_estimate - all expenses(interest, property_tax, hoa) - principal)
                              11.coverage percentage of principal/rental
            """

            if value[8] == "Perfect Deal":
                result.append([
                str(value[8]),
                "a. worry free: rental income will cover all expense and principal",
                "b. covered '100%' expense",
                "c. covered '100%' principal of the first year",
                str("d. net cash income (rental - all expenses - principal) = "+ str(value[10]) + " for first year"),
                str("e. " + value[0])
                ])

            elif value[8] == "Good Deal":
                result.append([
                str(value[8]),
                "a. you will still need to pay partial principal",
                "b. cover '100%' Expense",
                str("c. cover " + str(value[11]) + '% principal of the first year'),
                str("d. gross income [rental - expenses] = "+ str(value[9]) + " for first year"),
                str("e. net cash shortage [rental - expenses - principal] =  " + str(value[10])+ " for first year"),
                str("f. " + value[0])
                ])

            elif value[8] == "Pass":
                result.append([
                str(value[8]),
                "a. you will have to pay partial expense and all principal",
                "b. gross shortage [rental - expenses] =  " + str(value[10])+ " for first year",
                str("b. gross shortage [rental - expenses] =  " + str(value[10])+ " for first year"),
                str("c. net cash shortage [rental - expenses - principal] =  " + str(value[10])+ " for first year"),
                str("d. " + value[0])
                ])

            elif value[8] == 'Incomplete Good Deal' or value[8] == 'Incomplete Perfect Deal':
                result.append([
                str(value[8]),
                str("a. the HOA value is not found due to " + value[4]),
                "b. worth to check this listing as its rental income will cover all expense(without HOA) and principal",
                str("b. gross shortage [rental - expenses] =  " + str(value[10])+ " for first year"),
                str("c. incomplete net cash income (rental - expenses(without HOA) - principal) = "+ str(value[10]) + " for first year"),
                str("d. use this link to verify the HOA fee: " + value[0])
                ])

            elif value[8] == 'Perfect Deal and no mortgage needed':
                result.append([
                str(value[8]),
                "a. worry free: rental income will cover all expense",
                "b. covered '100%' expense",
                str("b. gross shortage [rental - expenses] =  " + str(value[10])+ " for first year"),
                str("net cash income (rental - all expenses - principal) = "+ str(value[10]) + " for first year"),
                str("d. " + value[0])
                ])

        return result

    else:
        return "no listing found for this zipcode"


if __name__ == "__find_valuable_listing__":
    find_valuable_listing()




# In[44]:

find_valuable_listing('San Francisco, CA 94158', 200000, 850000, 3.75, 30)


# In[ ]:
