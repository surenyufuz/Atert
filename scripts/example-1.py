import time
from appium import webdriver

# Sgit v1.3.0-v1.3.2
# 测试脚本编号 sce-2-Sgit-2

desired_caps = {}
desired_caps['platformName'] = 'Android'
desired_caps['platformVersion'] = '6.0.1'
desired_caps['deviceName'] = 'device'
desired_caps['appPackage'] = 'me.sheimi.sgit'
desired_caps['appActivity'] = 'me.sheimi.sgit.RepoListActivity'
desired_caps['newCommandTimeout'] = '1000'
desired_caps['noReset'] = True

driver = webdriver.Remote('http://127.0.0.1:4723/wd/hub', desired_caps)
time.sleep(10)

el = driver.find_element_by_accessibility_id('More options')
el.click()


time.sleep(5)

el = driver.find_element_by_android_uiautomator('new UiSelector().text("Private Keys")')
el.click()
time.sleep(5)

driver.quit()
