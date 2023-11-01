from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

import os
from glob import glob

from .account import Account, Transaction
from .util import Log, Timeout

import time

class ScrapeSession:
    driver: webdriver.Firefox
    account: Account

    def __init__(self, driver: webdriver.Firefox, account: Account, short_name: str, download_dir: str):
        self.driver = driver
        self.account = account
        if 'cc' in short_name:
            self.account_type = 'card'
        else:
            self.account_type = 'account'
        self.short_name = short_name
        self.download_dir = download_dir

        Log.log('Starting scraping session for account %s' % account.get_name())
        url = self.account.get_element().find_element(By.TAG_NAME, "a").get_attribute("href")
        self.driver.execute_script('window.open()')
        self.driver.switch_to.window(self.driver.window_handles[1])
        self.driver.get(url)
        Timeout.timeout()
        Log.log('Tab opened for account %s' % account.get_name())

    def close(self):
        Log.log('Closing tab for account %s...' % self.account.get_name())
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])
        Log.log('Closed')

    def scrape_transactions(self):
        Log.log('Scraping transactions for account %s...' % self.account.get_name())
        i: int = 0
        out: list[Transaction] = []
        row: WebElement
        table_id = 'transactions'
        if len(self.driver.find_elements(By.ID, table_id)) == 0:
            Log.log('No transaction table found')    
            return self
        table = self.driver.find_element(By.ID, table_id)
        body = table.find_element(By.TAG_NAME, "tbody")
        rows = body.find_elements(By.TAG_NAME, "tr")
        Log.log('%d transactions found.' % (len(rows)))
        for i, row in enumerate(rows):
            cell = row.find_element(By.TAG_NAME, "td")
            expander = cell.find_element(By.TAG_NAME, "a")
            self.driver.execute_script("arguments[0].scrollIntoView();", expander)
            WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((expander)))
            time.sleep(1)
            expander.click()
            time.sleep(1)
            transaction = Transaction()
            transaction.amount = float(row.find_element(By.CLASS_NAME, "trans-amount-cell").text.replace(",","").replace("$",""))
            transaction.balance = float(row.find_element(By.CLASS_NAME, "trans-balance-cell").text.replace(",","").replace("$",""))
            transaction.date = row.find_element(By.CLASS_NAME, "trans-date-cell").text
            transaction.desc = row.find_element(By.CLASS_NAME, "expand-trans-from-desc").text
            transaction.trans_date = row.find_element(By.CLASS_NAME, "second-expanded-cell").text

            out.append(transaction)
            expander.click()
        Log.log('Found %d transactions on account %s' % (i, self.account.get_name()))
        self.account.set_transactions(out)
        return self

    def load_more_transactions(self):
        Log.log('Loading more transactions in account %s...' % self.account.get_name())
        view_more = self.driver.find_element(By.CLASS_NAME, "view-more-transactions")
        self.driver.execute_script("arguments[0].click();", view_more)
        Timeout.timeout()
        Log.log('Loaded more transactions in account %s' % self.account.get_name())
        return self
    
    def prepare_transaction_menu(self):
        if self.account_type == 'account':
            self.driver.find_element(By.ID, "download-transactions").click()
        else:
            self.driver.find_element(By.NAME, "download_transactions_top").click()
        time.sleep(1)

    def get_period_list_element(self):
        if self.account_type == 'account':
            element_id = 'select_txnPeriod'
        else:
            element_id = 'select_transaction'
        element = self.driver.find_element(By.ID, element_id)
        return element

    def select_period_list(self):
        period_list_element = self.get_period_list_element()
        select_list_element = Select(period_list_element)
        return select_list_element

    def format_period_str(self, period_element):
        if self.account_type == 'account':
            period_str = period_element.get_attribute('value')
            if period_str == 'Current transactions':
                period_str = 'current' 
            period_str = period_str.replace('/','-')
        else:
            period_name = period_element.get_attribute('name')
            if period_name == 'transaction_period':
                print('Did it here')
                print(period_name)
                period_str = 'current'
            else:
                period_str = period_name.split('_')
                period_str = '-'.join(period_str[3:])
        return period_str
            
    def select_filetype(self, ftype='csv'):
        if self.account_type == 'account':
            select_ftype = Select(self.driver.find_element(By.ID, "select_fileType"))   
        else:
            if ftype == 'csv':
                ftype = '&formatType=csv'
            select_ftype = Select(self.driver.find_element(By.ID, "select_filetype"))   
        select_ftype.select_by_value(ftype)

    def select_period(self, period_element, period_list_element):
        if self.account_type == 'account':
            period_value = period_element.get_attribute('value')
            period_list_element.select_by_value(period_value)
        else:
            value = period_element.get_attribute('value')
            list_element = self.get_period_list_element()
            self.driver.execute_script("arguments[0].scrollIntoView();", list_element)
            period_list_element.select_by_value(value)

    def download_transactions(self):
        if self.account_type == 'account':
            self.driver.find_element(By.ID, 'btn-download-txn').click()
        else:
            Timeout.timeout()
            #self.driver.find_element(By.CLASS_NAME, 'submit-download').click()
            element = self.driver.find_element(By.XPATH, '/html/body/div[1]/div/div[4]/div[1]/div/div[5]/div[2]/div[2]/div/div[3]/div/div[4]/div[2]/a')
            self.driver.execute_script("arguments[0].click();", element)

    def get_statement(self, period='cur'):
        self.prepare_transaction_menu()
        if period == 'cur':
            period_value = 'Current transactions'
        else:
            period_value = period
        self.select_period(period_value)
        self.select_filetype()
        self.download_transactions()

    def get_all_statements(self, period_limit=10):
        self.prepare_transaction_menu()
        self.select_filetype()
        period_list_element = self.select_period_list()
        # Not enumerating to deal with skipped periods
        i = 0
        for period_element in period_list_element.options:
            name = period_element.get_attribute('name')
            print(f'Period element: {name}')
            print(f'Period text: {period_element.text}')
            if i > period_limit - 1:
                break
            period_text = period_element.text
            if self.account_type == 'account':
                if (period_text != 'Current transactions') and ('Period' not in period_text):
                    continue
            self.select_period(period_element, period_list_element)
            self.download_transactions()
            Timeout.timeout()
            list_of_files = glob(f'{self.download_dir}*')
            latest_file = max(list_of_files, key=os.path.getctime)
            period_str = self.format_period_str(period_element)
            renamed_file = f'{self.download_dir}stmt_{self.short_name}_{period_str}'
            os.rename(latest_file, renamed_file)
            if self.account_type != 'account':
                self.prepare_transaction_menu()
                self.select_filetype()
                period_list_element = self.select_period_list()
            i += 1
        Timeout.timeout()
