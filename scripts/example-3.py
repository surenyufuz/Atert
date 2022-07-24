import time
from appium import webdriver

# wps_note v1.01-v1.8.6
# 测试脚本编号
# sce-27-WpsNote-10

desired_caps = {}
desired_caps['platformName'] = 'Android'
desired_caps['platformVersion'] = '6.0.1'
desired_caps['deviceName'] = 'device'
desired_caps['appPackage'] = 'cn.wps.note'
desired_caps['appActivity'] = 'cn.wps.note.main.MainActivity'
desired_caps['newCommandTimeout'] = '1000'
desired_caps['noReset'] = True
desired_caps['adbExecTimeout'] = '30000'

driver = webdriver.Remote('http://127.0.0.1:4723/wd/hub', desired_caps)
time.sleep(10)

# 系统语言设置为中文


el = driver.find_elements_by_class_name('android.widget.ImageView')[22]
el.click()
time.sleep(5)

el = driver.find_element_by_id('cn.wps.note:id/feedback')
el.click()
time.sleep(5)


driver.quit()