from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support.select import Select
import time
import logging
from datetime import datetime as dt
from selenium.common.exceptions import NoSuchElementException
from .settings import SUREWISE_LOG, SUREWISE_PAS, PAYMENT_CVC, PAYMENT_EXP, PAYMENT_NUM

def log_in():
    options = FirefoxOptions()
    options.headless = True
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1200")
    options.add_argument("--remote-debugging-port=9222")
    driver = webdriver.Firefox(firefox_options=options)
    driver.get("https://secure.surewise.com/myaccount/login")
    driver.find_element_by_name('username').send_keys(SUREWISE_LOG)
    driver.find_element_by_name('password').send_keys(SUREWISE_PAS)
    driver.find_element_by_id('form-login').find_element_by_class_name('btn-primary').click()
    time.sleep(1)
    print("logged in")
    return driver


def request_quote(driver, input):
    driver.get("https://secure.surewise.com/portal/newquote")
    time.sleep(2)
    Select(driver.find_element_by_name('product')).select_by_value("carers")
    driver.find_element_by_id('startQuoteBtn').click()
    time.sleep(2)
    Select(driver.find_element_by_id('employment-type')).select_by_value('selfemployed')
    time.sleep(0.2)
    Select(driver.find_element_by_id('policy-term')).select_by_value('annual')
    driver.find_element_by_id('submit-btn').click()
    time.sleep(2)
    driver.find_element_by_id('card-bronze').find_element_by_class_name('btn-success').click()
    time.sleep(2)
    if input['gender'] == 'male':
        title = 'Mr'
    else:
        title = 'Mrs'
    Select(driver.find_element_by_name('title')).select_by_value(title)
    driver.find_element_by_name('first_name').send_keys(input['first_name'])
    driver.find_element_by_name('last_name').send_keys(input['last_name'])
    driver.find_element_by_name('email_address').send_keys(input['email'])
    driver.find_element_by_name('telephone_number').send_keys(input['phone'])
    driver.find_element_by_name('postcode_finder').send_keys(input['postcode'])
    driver.find_element_by_id('address-finder-button').click()
    time.sleep(2)
    try:
        Select(driver.find_element_by_name('choose_address')).select_by_value(input['address_line_1'])
    except NoSuchElementException as e:
        try:
            value = driver.find_element_by_xpath("//option[contains(text(), '%s')]" % input['address_line_1'])
            text = value.get_attribute('innerText')
            Select(driver.find_element_by_name('choose_address')).select_by_value(text)
        except NoSuchElementException as e:
            return False
    value = driver.find_element_by_xpath("//option[contains(text(), '69 Carisbrooke Road')]")
    text = value.get_attribute('innerText')

    time.sleep(1.2)
    Select(driver.find_element_by_name('date_[day]')).select_by_value(str(dt.now().strftime("%d")))
    Select(driver.find_element_by_name('date_[month]')).select_by_value(str(dt.now().strftime("%m")))
    Select(driver.find_element_by_name('date_[year]')).select_by_value(str(dt.now().strftime("%Y")))

    driver.find_element_by_id('policyAssumptionsCheck').click()
    driver.find_element_by_id('termsCheck').click()

    driver.find_element_by_class_name('sw-large-next-btn').click()
    time.sleep(1)
    driver.find_element_by_id('payment-submit').click()
    time.sleep(1)
    driver.find_element_by_name('address1').clear()
    driver.find_element_by_name('address2').clear()
    driver.find_element_by_name('town').clear()
    driver.find_element_by_name('county').clear()
    driver.find_element_by_name('postcode').clear()

    driver.find_element_by_name('address1').send_keys('148 Sylvan Road')
    driver.find_element_by_name('address2').send_keys('')
    driver.find_element_by_name('town').send_keys('Stockwell')
    driver.find_element_by_name('county').send_keys('London')
    driver.find_element_by_name('postcode').send_keys('SE19 2SA')

    driver.find_element_by_name('name').send_keys('James')
    time.sleep(2)

    iframe =  driver.find_element_by_xpath('//div[@id="pay-card-number"]/div/iframe')
    driver.switch_to.frame(iframe)
    cardnumber = driver.find_element_by_name('cardnumber')
    cardnumber.send_keys(PAYMENT_NUM)
    driver.switch_to.default_content()

    iframe = driver.find_element_by_xpath('//div[@id="pay-card-expiry"]/div/iframe')
    driver.switch_to.frame(iframe)
    expiry = driver.find_element_by_name('exp-date')
    expiry.send_keys(PAYMENT_EXP)
    driver.switch_to.default_content()

    iframe = driver.find_element_by_xpath('//div[@id="pay-card-cvc"]/div/iframe')
    driver.switch_to.frame(iframe)
    cvc = driver.find_element_by_name('cvc')
    cvc.send_keys(PAYMENT_CVC)
    driver.switch_to.default_content()

    driver.find_element_by_id('payBtn').click()
    time.sleep(10)
    driver.find_element_by_id('methodCC').click()
    driver.find_element_by_id('subscription-submit').click()
    time.sleep(10)
    policy_number = driver.find_element_by_xpath('/html/body/div[1]/div[4]/div[2]/div/div/div[3]/div[2]').text
    print(policy_number)
    return policy_number

def cancel_quote(driver, policy_no):
    driver.get("https://secure.surewise.com/portal/dashboard")
    time.sleep(5)
    driver.find_element_by_name('quicksearch').send_keys(policy_no)
    driver.find_element_by_xpath('/html/body/header/div[2]/div/div/form/table/tbody/tr/td[3]/button').click()
    time.sleep(5)
    driver.find_element_by_xpath('/html/body/div[1]/div[2]/div/div[3]/div[1]/div/div/div[1]/a').click()
    time.sleep(5)
    Select(driver.find_element_by_id('cancelReason')).select_by_value('No longer needed')
    try:
        Select(driver.find_element_by_id('handleRefund')).select_by_value('worldpay')
    except NoSuchElementException as e:
        Select(driver.find_element_by_id('handleRefund')).select_by_value('dont_refund')
    time.sleep(3)
    driver.find_element_by_xpath('/html/body/div[1]/div[2]/div/div[3]/div[1]/div/div/div/div/form/button').click()
