from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import BofaScraper

from selenium.webdriver.remote.webelement import WebElement
from .transaction import Transaction

def _login(self: BofaScraper):
    self._driver.get("https://bankofamerica.com")
    self._driver.find_element_by_id("onlineId1").clear()
    self._driver.find_element_by_id("onlineId1").send_keys(self._credentials["username"])
    self._driver.find_element_by_id("passcode1").clear()
    self._driver.find_element_by_id("passcode1").send_keys(self._credentials["password"])
    self._driver.find_element_by_id("signIn").click()


def _get_account(self: BofaScraper, accountName: str) -> WebElement:
    account: WebElement
    for account in self._driver.find_elements_by_class_name("AccountItem"):
        account_name = account.find_element_by_tag_name("a").get_attribute("innerHTML")
        if account_name == accountName:
            return account


def _open_account(self: BofaScraper, accountName: str):
    # self._driver.implicitly_wait(2)
    self._get_account(accountName).find_element_by_tag_name("a").click()


def _get_transactions(self: BofaScraper) -> dict[str, list[Transaction]]:
    out: dict[str, list[Transaction]] = dict()
    
    scraped_entries = _scrape_transactions(self)

    #sort scraped data by month
    for entry in scraped_entries:
        date: str
        if entry.getDate() == "processing":
            date = "processing"
        else:
            date = entry.getDate().split("/")
            month = date[0]
            year = date[2]
            date = year + "-" + month

        #initialize list for entries in current entry's month
        if date not in out:
            out[date] = list()
        
        #append current entry to scraped_by_month
        out[date].append(entry)
    return out


def _scrape_transactions(self: BofaScraper) -> list[str]:
    out: list[Transaction] = list()
    row: WebElement

    for row in self._driver.find_elements_by_class_name("in-transit-record"):
        out.append(
            Transaction(
                "processing",
                float(row.find_element_by_class_name("amount").get_attribute("innerHTML")),
                row.find_elements_by_tag_name("td")[1].get_attribute("innerHTML").split("<br>")[0]
            ).toDict()
        )
    for row in self._driver.find_elements_by_class_name("record"):
        out.append(
            Transaction(
                row.find_elements_by_tag_name("span")[1].get_attribute("innerHTML"),
                float(row.find_element_by_class_name("amount").get_attribute("innerHTML")),
                row.find_element_by_class_name("transTitleForEditDesc").get_attribute("innerHTML")
            ).toDict()
        )
    return out