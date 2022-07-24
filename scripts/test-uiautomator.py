import time
from uiautomator import device


# adb connect

device(description="More options").click()
time.sleep(3)

device(text="Private Keys").click()
time.sleep(3)