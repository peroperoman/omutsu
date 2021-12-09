import pandas as pd
import requests
from selenium import webdriver
from time import sleep
from selenium.webdriver.support.select import Select
from bs4 import BeautifulSoup


def amazon_get():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(
        executable_path='/Users/ireba-pc/webdriver/chromedriver',
        options=options)

    driver.get('https://www.amazon.co.jp/')
    driver.implicitly_wait(5)
    sleep(1)

    driver.find_element_by_id('nav-search-dropdown-card').click()
    select_category = Select(driver.find_element_by_id('searchDropdownBox'))
    select_category.select_by_value('search-alias=hpc')

    driver.find_element_by_css_selector('div.nav-search-field > input').send_keys('オムツ ビッグサイズ L')
    driver.find_element_by_css_selector('div.nav-right > div > span > input').click()

    sort_select = Select(driver.find_element_by_id('s-result-sort-select'))
    sort_select.select_by_value('review-rank')
    sleep(1)

    a_tags = driver.find_elements_by_css_selector('ul.a-pagination > li.a-selected > a')
    a_tags += driver.find_elements_by_css_selector('ul.a-pagination > li.a-normal > a')
    page_links = [a_tag.get_attribute('href') for a_tag in a_tags]

    amz_prd_info = []
    for page_link in page_links:
        driver.get(page_link)
        sleep(1)
        source = driver.page_source.encode('utf-8')
        soup = BeautifulSoup(source, 'lxml')
        product_soup = soup.select('div.a-section.a-spacing-medium')

        for i in range(len(product_soup) - 1):
            miso_soup = product_soup[i]
            amz_prd_name = miso_soup.find('span', class_='a-size-base-plus a-color-base a-text-normal').text
            tmp_price = miso_soup.find('span', class_='a-price-whole')
            amz_price = tmp_price.text.replace('￥', '').replace(',', '') if tmp_price else None
            tmp_review_avg = miso_soup.find('span', class_='a-icon-alt')
            review_avg = tmp_review_avg.text if tmp_review_avg else None
            tmp_review_num = miso_soup.select_one('div.a-row.a-size-small > span:nth-of-type(2) > a > span')
            review_num = tmp_review_num.text if tmp_review_num else None

            amz_prd_info.append({
                'amz_prd_name': amz_prd_name,
                'amz_price': amz_price,
                'amz_review_avg': review_avg,
                'amz_review_num': review_num
            })

    driver.quit()

    return amz_prd_info

def add_rakuten_comp(amz_prd_info):
    for amz_prd in amz_prd_info:
        amz_prd_name = amz_prd['amz_prd_name'].replace('Amazon.co.jp ', 'Amazon.co.jp').replace('【Amazon.co.jp限定】', '')
        url = 'https://search.rakuten.co.jp/search/mall/' + amz_prd_name + '?filter=fs&s=2'
        r = requests.get(url)
        soup = BeautifulSoup(r.content, 'lxml')
        tmp_price = soup.select_one('div.content.description.price > span')
        rak_price = tmp_price.text.replace('円', '').replace(',', '') if tmp_price else None
        tmp_name = soup.select_one('div.content.title > h2 > a')
        rak_name = tmp_name.text if tmp_name else None

        if rak_price is not None and amz_prd['amz_price'] is not None:
            amz_price = int(amz_prd['amz_price'])
            rak_price = int(rak_price)
            if amz_price < rak_price:
                cheaper = 'Amazon'
            elif rak_price < amz_price:
                cheaper = 'Rakuten'
            else:
                cheaper = 'Same price'
        else:
            cheaper = None

        amz_prd.update({
            'rakuten_prd_name': rak_name,
            'rakuten_price': rak_price,
            'cheaper': cheaper
        })

    return amz_prd_info


if __name__ == '__main__':
    amz_prd_info = amazon_get()
    result = add_rakuten_comp(amz_prd_info=amz_prd_info)

    df = pd.DataFrame(result)
    df.index = df.index + 1
    df.to_csv('amazon-omutsu.csv', encoding='utf-8-sig')
