import time
from appium import webdriver

desired_caps = {}
desired_caps['platformName'] = 'Android'
desired_caps['platformVersion'] = '6.0.1'
desired_caps['deviceName'] = 'device'
desired_caps['appPackage'] = 'org.billthefarmer.currency'
desired_caps['appActivity'] = 'org.billthefarmer.currency.Main'
desired_caps['newCommandTimeout'] = '1000'
desired_caps['noReset'] = True

driver = webdriver.Remote('http://127.0.0.1:4723/wd/hub', desired_caps)
time.sleep(10)

el = driver.find_element_by_accessibility_id('More options')
el.click()
time.sleep(5)

el = driver.find_element_by_android_uiautomator('new UiSelector().text("Settings")')
el.click()
time.sleep(5)

driver.quit()