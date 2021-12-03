import yfinance as yf
import requests
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
from selenium import webdriver
import time
import ast

class Company():
    def __init__(self, companyName):
        '''
        Base Company object
        '''
        self.companyName = companyName
        
        res = self.__getTickerSymbol()
        
        if res == None:
            # company not found
            self.found = False
        else:
            # company found, we can move on
            self.found = True
            self.__tickerObj = yf.Ticker(res)
            self.__data = self.__tickerObj.info # 2 web requests
            self.ticker = self.__data['symbol']
            self.YFURL = 'https://finance.yahoo.com/quote/{0}/'.format(self.ticker)
            self.displayName = self.__data['longName']

    def __getTickerSymbol(self): # only use for __init__. Otherwise reference self.ticker
        '''
        Return ticker symbol from company name.
        '''
        queryForURL = urllib.parse.quote_plus(self.companyName)
        fp = urllib.request.urlopen(f"http://d.yimg.com/autoc.finance.yahoo.com/autoc?query={queryForURL}&region=1&lang=en")
        mybytes = fp.read()
        res = ast.literal_eval(mybytes.decode("unicode_escape")) # read and convert to dict
        fp.close()

        try:
            firstResult = res['ResultSet']['Result'][0]
        except IndexError:
            # company not found (query was empty)
            return None
        return firstResult['symbol']


    def getHistoricalPricesDf(self, period='5d', interval='1d'): # 1 web request
            '''
            Return DataFrame of historical stock data of the given ticker between two given dates.

            use "period" instead of start/end
             valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
             (optional, default is '1mo')

            fetch data by "interval" (including intraday if period < 60 days)
             valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
             (optional, default is '1d')
            '''
            return self.__tickerObj.history(period=period, interval=interval)
            # return yf.download(tickers='T', period=period)


    def getStockPrice(self):
        '''
        Return stock price (bid and ask) of given ticker at close
        '''
        return (self.__data['bid'], self.__data['ask'])


    def getConvo(self): # 1 web request
        '''
        :param None
        :return: Lists containing both the comments and relative timestamps from Yahoo Finance Conversations
        '''
        
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors')
        driver = webdriver.Chrome(options=options)

        commentList = []
        stamps = []
        driver.get('https://finance.yahoo.com/quote/'+str(self.ticker)+'/community?p='+str(self.ticker))
        showMore = driver.find_element_by_xpath('//*[@id="canvass-0-CanvassApplet"]/div/button')
        for _ in range(3):
            showMore.click()
            time.sleep(1)
        comments = driver.find_elements_by_class_name('comment')
        for i in range(len(comments)):
            stamps.append(driver.find_element_by_xpath('//*[@id="canvass-0-CanvassApplet"]/div/ul/li['+str(i+1)+']/div/div[1]/span/span').text)
        for c in comments:
            comment = c.text
            comment = comment[:comment.rfind('Reply')].replace('\n',' ')
            if 'ago' in comment:
                ago = comment.find('ago')
                commentList.append(comment[ago+4:])
            if 'Yesterday' in comment:
                yesterday = comment.find('yesterday')
                commentList.append(comment[yesterday+10:])

        stampsOut = []
        for i in range(len(commentList)):
            print(commentList[i])
            stampsOut.append(stamps[i])

        return commentList, stampsOut


    def getStockPriceChange(self, afterHours=False): # 1 web request

        req = urllib.request.Request(self.YFURL, headers={'User-Agent' : "Magic Browser"}) 
        html = urllib.request.urlopen(req)
        soup = BeautifulSoup(html, 'html.parser')
        if not afterHours:
            return soup.findAll('span', {"data-reactid": "51"})[0].contents[0]   # broken
        else:
            return soup.findAll('span', {"data-reactid": "51"})[0].contents[0]

    def getSector(self):
        return self.__data['sector']