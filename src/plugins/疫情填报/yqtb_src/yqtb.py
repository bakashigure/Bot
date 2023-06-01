import os
import re
import sys
import time
import yaml
import warnings
import logging.handlers
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains


class Logger:
    def __init__(self, init):
        self.logger = logging.getLogger("yqtb")
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False

        if init:
            rh_formatter = logging.Formatter(
                "%(asctime)s - %(module)s - %(levelname)s - %(message)s"
            )

            hfh = logging.handlers.RotatingFileHandler(
                '../yqtb.log', mode="a", maxBytes=1024 * 1024 * 8, backupCount=1
            )
            hfh.setFormatter(rh_formatter)
            self.logger.addHandler(hfh)

            hsh = logging.StreamHandler(sys.stdout)
            hsh.setFormatter(rh_formatter)
            self.logger.addHandler(hsh)

    def info(self, *args, **kwargs):
        self.logger.info(*args, **kwargs)
        # print("\033[1;34mINFO - ", args[0], "\033[0m", sep="")

    def error(self, *args, **kwargs):
        self.logger.error(*args, **kwargs)
        # print("\033[1;31mERROR - ", args[0], "\033[0m", sep="")

    def debug(self, *args, **kwargs):
        self.logger.debug(*args, **kwargs)
        # print("\033[1;32mDEBUG - ", args[0], "\033[0m", sep="")

    def warning(self, *args, **kwargs):
        self.logger.warning(*args, **kwargs)
        # print("\033[1;33mWARN - ", args[0], "\033[0m", sep="")





class YQTB:
    def __init__(self, _username, _password, _student_list, init = False):
        self.logger = Logger(init)
        self.username = _username
        self.password = _password
        self.student_list = _student_list
        self.done_list = []
        option = webdriver.ChromeOptions()
        option.add_argument("--no-sandbox")
        option.add_argument("--headless")
        option.add_argument('--log-level=3')
        option.add_argument("--disable-logging")
        option.add_argument("--disable-notifications")
        option.add_argument("--disable-popup-blocking")
        os.environ['WDM_LOG_LEVEL'] = '0'
        warnings.filterwarnings("ignore")
        self.browser = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=option)

    def run(self):

        # login

        self.logger.info("登录中")
        self.browser.get("""https://yqtb.nwpu.edu.cn/wx/ry/jrsb_xs.jsp""")
        use_password = self.browser.find_elements(by=By.CSS_SELECTOR, value=r'[role=menubar] [role=menuitem]:last-child')[0]
        use_password.click()
        self.browser.find_elements(by=By.CSS_SELECTOR, value=r'#username')[0].send_keys(self.username)
        self.browser.find_elements(by=By.CSS_SELECTOR, value=r'#password')[0].send_keys(self.password)
        self.browser.find_elements(by=By.CSS_SELECTOR, value=r"#fm1 [name=button]")[0].click()
        time.sleep(1.5)

        # phone_code

        phone_code_needed = self.browser.find_elements(by=By.CSS_SELECTOR, value=r'div[role=dialog]')
        if len(phone_code_needed) == 0:
            self.logger.info("很幸运，这次不需要验证码")
        else:
            self.logger.warning("需要验证码，请手动处理")
            # 采用邮件方式处理
            # other_method = self.browser.find_elements(by=By.CSS_SELECTOR, value=r'div[role=dialog] img.safe-icon')[0]
            # other_method.click()
            send_phone_code = self.browser.find_elements(by=By.CSS_SELECTOR, value=r'div[role=dialog] .code-wrap > button')[0]
            self.logger.warning("按回车开始获取验证码: (Enter here) ")
            input()
            self.logger.warning("正在获取验证码")
            send_phone_code.click()
            phone_code = input("请输入得到的验证码: ")
            input_area = self.browser.find_elements(by=By.CSS_SELECTOR, value=r'div[role=dialog] .code-wrap input')[0]
            input_area.send_keys(phone_code)
            confirm_button = self.browser.find_elements(by=By.CSS_SELECTOR, value=r'div[role=dialog] .el-dialog__footer button')[0]
            confirm_button.click()
            time.sleep(1.5)

        # goto_yqtb

        self.logger.info("跳转中")
        self.browser.get("""https://yqtb.nwpu.edu.cn/wx/ry/fktj.jsp""")
        time.sleep(0.5)
        self.browser.find_elements(by=By.CSS_SELECTOR, value=r"#wtbrs")[0].click()
        time.sleep(0.5)

        # search

        num = int(self.browser.find_elements(by=By.CSS_SELECTOR, value=r"#wtbrs")[0].get_attribute("innerHTML"))
        self.logger.warning("共" + str(num) + "人")
        times = num // 15
        self.logger.warning("需翻" + str(times) + "页")
        for i in range(times + 1):
            self.logger.warning("当前为第" + str(i + 1) + "页")
            k = self.browser.find_elements(by=By.CSS_SELECTOR, value=r"table.table > tbody > tr > td:first-child")
            for mem in k:
                if mem != "None":
                    self.done_list.append(mem.get_attribute("innerHTML"))
                    self.logger.info(mem.get_attribute("innerHTML"))
            all_a = self.browser.find_elements(by=By.CSS_SELECTOR, value="a")
            for a in all_a:
                if a.get_attribute("innerHTML").strip() == "下一页":
                    a.click()
                    time.sleep(0.5)
                    break
        
        return self

    def get_absent(self):
        absent = set(self.student_list) & set(self.done_list)
        self.logger.warning("未参加疫情填报的人有：" + str(absent))
        return absent


if __name__ == "__main__":

    def read_config(yaml_file) -> dict:
        file = open(yaml_file, 'r', encoding='utf-8')
        raw_data = file.read()
        file.close()
        data = yaml.safe_load(raw_data)
        return data

    data = read_config("./id.yaml")

    username = data.get("yq_username", "")
    password = data.get("yq_password", "")
    student_list = data.get("yq_students", [])

    y = YQTB(username, password, student_list)
    res = y.run().get_absent()
    print(res)
