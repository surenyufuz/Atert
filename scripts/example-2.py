import time
from appium import webdriver

# currency v1.0-v1.35
# 测试脚本编号
# sce-17-Currency-6

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



el = driver.find_element_by_id('org.billthefarmer.currency:id/action_settings')
el.click()


driver.quit()