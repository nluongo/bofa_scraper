from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .account import Account, Transaction
from .util import Log, Timeout

import time

class ScrapeSession:
	driver: webdriver.Firefox
	account: Account

	def __init__(self, driver: webdriver.Firefox, account: Account):
		self.driver = driver
		self.account = account

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
		print('Here?')
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
			#WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "second-expanded-cell")))
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
