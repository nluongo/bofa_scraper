from bofa_scraper import BofAScraper
from pathlib import Path
from .util import Log, Timeout

def main():
    try:
        with open(Path.home()/'login.txt') as f:
            username, pwd, download_dir, account_short_names = f.readlines()

        username, pwd, download_dir = username.strip(), pwd.strip(), download_dir.strip()
        print(f'Download directory: {download_dir}')
        scraper = BofAScraper(
            username,
            pwd,
            download_dir,
            headless=False
        )   

        account_short_names = account_short_names.split(',')
        account_short_names = [name.strip() for name in account_short_names]

        Log.log('About to login')
        scraper.login()

        for i in range(len(account_short_names)):
            if i == 0:
                accounts_url = scraper.driver.current_url
            else:
                scraper.driver.get(accounts_url)
            print(f'Account {account_short_names[i]}')
            Timeout.timeout()
            accounts = scraper.get_accounts()
            short_name, account = account_short_names[i], accounts[i]
            session = scraper.open_account(account, short_name)
            Timeout.timeout()
            session.get_all_statements(period_limit=5)
    except:
        raise
    finally:
        if scraper:
            scraper.driver.close()
            scraper.driver.quit()

if __name__ == '__main__':
    main()
