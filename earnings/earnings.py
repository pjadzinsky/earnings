"""

I want to create something that
1. identifies companies that are going to present earnings N days from now
2. Look at implied volatitliy and compare with historical one
3. Buy volatility when N is big ~ 1-2 month probably
4. Sell volatility when N is low ~ 7 days

First I need a way of listing tickers and their days to earnings call
https://finviz.com/screener.ashx?v=111 has something but is paid information (Filters->Descriptive->Earnings Date)
"""
import logging
import time
from html.parser import HTMLParser

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

logger = logging.getLogger(__name__)
FORMAT = '%(asctime)-15s %(clientip)s %(user)-8s %(message)s'
logging.basicConfig(format=FORMAT)
YAHOO_FINANCE = "https://finance.yahoo.com/calendar/earnings?"
EMPTY_DF = pd.DataFrame(columns=[
            "ticker",
            "company",
            "call_time",
            "eps_estimate",
            "reported_estimate",
            "surprise",
            "report_date",
        ])


class MyHTMLParser(HTMLParser):

    """
        This is what I got by printing tag start/end and data

        I'm using the information in the attrs of the tag to identify when important data is coming and
        I'm turning ON corresponding boolean flags

        Encountered a start tag: a, attrs: [('href', '/quote/PLYM?p=PLYM'), ('title', ''), ('class', 'Fw(600) C($linkColor)'), ('data-reactid', '910')]
        Encountered some data  : PLYM
        Encountered an end tag : a
        Encountered a start tag: div, attrs: [('class', 'W(3px) Pos(a) Start(100%) T(0) H(100%) Bg($pfColumnFakeShadowGradient) Pe(n) Pend(5px)'), ('data-reactid', '911')]
        Encountered an end tag : div
        Encountered an end tag : td
        Encountered a start tag: td, attrs: [('colspan', ''), ('class', 'Va(m) Ta(start) Pend(10px) Pstart(6px) Fz(s)'), ('aria-label', 'Company'), ('data-reactid', '912')]
        Encountered some data  : Plymouth Industrial REIT Inc
        Encountered an end tag : td
        Encountered a start tag: td, attrs: [('colspan', ''), ('class', 'Va(m) Ta(end) Pstart(15px) W(20%) Fz(s)'), ('aria-label', 'Earnings Call Time'), ('data-reactid', '914')]
        Encountered a start tag: span, attrs: [('data-reactid', '915')]
        Encountered some data  : Before Market Open
        Encountered an end tag : span
        Encountered an end tag : td
        Encountered a start tag: td, attrs: [('colspan', ''), ('class', 'Va(m) Ta(end) Pstart(15px) W(10%) Fz(s)'), ('aria-label', 'EPS Estimate'), ('data-reactid', '916')]
        Encountered some data  : -0.24
        Encountered an end tag : td
        Encountered a start tag: td, attrs: [('colspan', ''), ('class', 'Va(m) Ta(end) Pstart(15px) W(10%) Fz(s)'), ('aria-label', 'Reported EPS'), ('data-reactid', '918')]
        Encountered some data  : -
        Encountered an end tag : td
        Encountered a start tag: td, attrs: [('colspan', ''), ('class', 'Va(m) Ta(end) Px(15px) W(10%) Fz(s)'), ('aria-label', 'Surprise(%)'), ('data-reactid', '920')]
        Encountered some data  : -
    """
    ticker_started = False
    company_started = False
    call_time_started = False
    eps_estimated_started = False
    reported_eps_started = False
    suprise_started = False
    ticker = None
    company = None
    call_time = None
    eps_estimated = None
    reported_eps = None
    surprise = None
    df = pd.DataFrame()

    def handle_starttag(self, tag, attrs):
        # print(f"Encountered a start tag: {tag}, attrs: {attrs}")
        # attrs is of the form attrs: [('href', '/quote/PLYM?p=PLYM'), ('title', ''), ('class', 'Fw(600) C($linkColor)'), ('data-reactid', '910')]
        href = [a for a in attrs if a[0] == 'href' and 'quote' in a[1]]
        company = [a for a in attrs if a[1] == 'Company']
        call_time = [a for a in attrs if a[1] == "Earnings Call Time"]
        eps_estimate = [a for a in attrs if a[1] == "EPS Estimate"]
        reported_eps = [a for a in attrs if a[1] == "Reported EPS"]
        surprise = [a for a in attrs if a[1] == "Surprise(%)"]
        if href:
            # this is messy, href is True for any list that that has that key-value pair but there are other
            # elements in the page that have that type of key that I don't want, namely the "Futures" in the page
            # I filter further here based on 'tilte' key, that should be empty for the cells I'm looking for
            title = [a for a in attrs if a[0]=='title' and a[1]]
            if not title:
                self.ticker_started = True
        elif company:
            self.company_started = True
        elif call_time:
            self.call_time_started = True
        elif eps_estimate:
            self.eps_estimated_started = True
        elif reported_eps:
            self.reported_eps_started = True
        elif surprise:
            self.suprise_started = True

    def handle_endtag(self, tag):
        if self.surprise:
            s = pd.Series(
                {
                    "ticker": self.ticker,
                    "company": self.company,
                    "call_time": self.call_time,
                    "eps_estimate": self.eps_estimated,
                    "reported_estimate": self.reported_eps,
                    "surprise": self.surprise,
                }
            )
            self.df = self.df.append(s, ignore_index=True)
        self.surprise = None

    def handle_data(self, data):
        if self.ticker_started:
            self.ticker = data
            self.ticker_started = False
        elif self.company_started:
            self.company = data
            self.company_started = False
        elif self.call_time_started:
            self.call_time = data
            self.call_time_started = False
        elif self.eps_estimated_started:
            self.eps_estimated = data
            self.eps_estimated_started = False
        elif self.reported_eps_started:
            self.reported_eps = data
            self.reported_eps_started = False
        elif self.suprise_started:
            self.surprise = data
            self.suprise_started = False


def get_chrome_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.binary_location = '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary'

    driver = webdriver.Chrome(chrome_options=chrome_options)
    return driver


driver = get_chrome_driver()


def get_df_one_date(date, size=100):
    """
    Get a dataframe wtih the info shown in yahoo finance

    https://finance.yahoo.com/calendar/earnings?day=2021-02-26
    """
    df = EMPTY_DF
    offset = 0
    while True:
        temp_df = _get_df_for_date_and_offset(date, offset, size)
        df = df.append(temp_df).reset_index(drop=True)
        if temp_df.empty or temp_df.shape[0] < size:
            break
        offset += size
    return df


def _get_df_for_date_and_offset(date, offset, size):
    url = YAHOO_FINANCE + f"day={date}&size={size}&offset={offset}"
    print(url)
    driver.get(url)
    time.sleep(3)
    source = driver.page_source
    parser = MyHTMLParser()

    parser.feed(source)
    df = parser.df
    if df.empty:
        df = EMPTY_DF
    df.loc[:, "report_date"] = date
    return parser.df


def get_earnings(start_date, end_date):
    dfs = []
    for date in pd.date_range(start_date, end_date):
        df = get_df_one_date(f"{date.date()}")
        dfs.append(df)

    df = pd.concat(dfs).reset_index(drop=True)
    return df

