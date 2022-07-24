import time
from appium import webdriver

desired_caps = {}
desired_caps['platformName'] = 'Android'
desired_caps['platformVersion'] = '6.0.1'
desired_caps['deviceName'] = 'device'
desired_caps['appPackage'] = 'cn.wps.note'
desired_caps['appActivity'] = 'cn.wps.note.main.MainActivity'
desired_caps['newCommandTimeout'] = '1000'
desired_caps['noReset'] = True

driver = webdriver.Remote('http://127.0.0.1:4723/wd/hub', desired_caps)
time.sleep(10)

el = driver.tap([(472.5, 932.5)])
el.click()
time.sleep(5)

el = driver.find_element_by_id('cn.wps.note:id/me_setting')
el.click()
time.sleep(5)

driver.quit()