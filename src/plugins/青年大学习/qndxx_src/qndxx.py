import os
import re
import sys
import time
import yaml
import base64
import ddddocr
import warnings
import logging.handlers
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains


def many_times_try(log_func, action_func, times, interval, success_func, failure_func):
    """
        :param log_func: logging function, get str(try_time) as arguments
        :param action_func: action function, no arguments
        :param times: maximum times
        :param interval: interval after an error time
        :param success_func: success logging function
        :param failure_func: failure logging function
        :return: None
    """
    success = False
    try_time = 1
    while not success and try_time <= times:
        log_func(str(try_time))
        try_time += 1
        try:
            action_func()
            success = True
        except Exception as e:
            time.sleep(interval)
    if success:
        success_func()
    else:
        failure_func()


class Logger:
    def __init__(self, init):
        self.logger = logging.getLogger("qndxx")
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False

        if init:
            rh_formatter = logging.Formatter(
                "%(asctime)s - %(module)s - %(levelname)s - %(message)s"
            )

            hfh = logging.handlers.RotatingFileHandler(
                '../qndxx.log', mode="a", maxBytes=1024 * 1024 * 8, backupCount=1
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


class QNDXX:
    def __init__(self, _username, _password, _student_list, init = False):
        self.logger = Logger(init)
        self.username = _username
        self.password = _password
        self.student_list = _student_list
        self.max_try_time = 10
        self.try_interval_sec = 4
        self.done_list = []
        self.error = False
        self.error_code = "UNDEFINED_ERROR"
        option = webdriver.ChromeOptions()
        option.add_argument("--headless")
        option.add_argument('--log-level=3')
        option.add_argument("--disable-logging")
        option.add_argument("--disable-notifications")
        option.add_argument("--disable-popup-blocking")
        os.environ['WDM_LOG_LEVEL'] = '0'
        warnings.filterwarnings("ignore")
        self.browser = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=option)

    # 登录陕西青少年团委平台
    def login(self):

        self.error = False

        self.browser.get('''https://www.sxgqt.org.cn/bgsxv2/login''')
        self.browser.find_elements(by=By.CSS_SELECTOR, value=r'[name=emial]')[0].send_keys(self.username)

        error = 1
        try_time = 1

        while error > 0 and try_time <= self.max_try_time:
            self.logger.info("当前登录次数为" + str(try_time))
            try_time += 1
            self.browser.find_elements(by=By.CSS_SELECTOR, value=r'[name=password]')[0].send_keys(self.password)
            img = self.browser.find_elements(by=By.CSS_SELECTOR, value=r'.login_verify.el-input + img')[0].get_attribute("src")
            result = re.search("data:image/(?P<ext>.*?);base64,(?P<data>.*)", img, re.DOTALL)
            if result:
                ext = result.groupdict().get("ext")
                data = result.groupdict().get("data")
                img = base64.urlsafe_b64decode(data)
                with open('temp.jpg', 'wb') as file:
                    file.write(img)
                ocr = ddddocr.DdddOcr()
                with open('temp.jpg', 'rb') as f:
                    img_bytes = f.read()
                ocr_res = ocr.classification(img_bytes)
                self.browser.find_elements(by=By.CSS_SELECTOR, value=r'[name=verify]')[0].clear()
                self.browser.find_elements(by=By.CSS_SELECTOR, value=r'[name=verify]')[0].send_keys(ocr_res)
            self.browser.find_elements(by=By.CSS_SELECTOR, value=r'.el-button.btn_submit.btn.el-button--button')[0].click()
            time.sleep(0.5)
            error = len(self.browser.find_elements(by=By.CSS_SELECTOR, value=r".el-message.el-message--error"))
            if error:
                time.sleep(self.try_interval_sec)

        if error == 0:
            self.logger.info("登录成功")
        else:
            self.logger.error("登录失败")

    # 进入 首页 -> 青年大学习 -> 操作(名册) 页面
    def goto_qndxx(self):

        if self.error:
            self.logger.error("goto_qndxx() 在开头遭遇 self.error")
            return None

        self.browser.get("""https://www.sxgqt.org.cn/bgsxv2/reunion/member/youthStudy""")

        success = 0
        try_time = 1
        button_list = []
        while success != 1 and try_time <= self.max_try_time:
            self.logger.info("当前等待进入青年大学习表页面次数为" + str(try_time))
            try_time += 1
            button_list = self.browser.find_elements(by=By.CSS_SELECTOR, value=r".dropdown_span.el-dropdown-selfdefine")
            success = len(button_list)
            if not success:
                time.sleep(self.try_interval_sec)

        if success > 0:
            self.logger.info("进入青年大学习表成功")
        else:
            self.logger.error("进入青年大学习表失败")
            return

        def this_action():
            self.logger.info("正在点击<操作>")
            action = ActionChains(self.browser)
            action.click_and_hold(on_element=button_list[0])
            action.perform()
            time.sleep(1)
            self.logger.info("正在点击<用户明细>")
            self.browser.find_elements(
                by=By.CSS_SELECTOR,
                value=r".el-dropdown-menu.el-popper > .el-dropdown-menu__item > span"
            )[0].click()
        many_times_try(
            log_func=lambda x: self.logger.info("当前点击<操作><用户明细>次数为" + x),
            action_func=this_action,
            times=self.max_try_time,
            interval=self.try_interval_sec,
            success_func=lambda: self.logger.info("点击成功"),
            failure_func=lambda: self.logger.info("点击失败"),
        )

        success = 0
        try_time = 1
        while success != 1 and try_time <= self.max_try_time:
            self.logger.info("当前等待进入名册页面次数为" + str(try_time))
            try_time += 1
            stu_list = self.browser.find_elements(
                by=By.CSS_SELECTOR,
                value=r".el-table__body > tbody .el-table_2_column_13.is-center.el-table__cell > .cell"
            )
            success = len(stu_list)
            time.sleep(self.try_interval_sec)

        if success > 0:
            self.logger.info("预进入名册成功")
        else:
            self.logger.error("预进入名册失败")
            return

        time.sleep(2)

        success_2 = 0
        try_time_2 = 1
        # 这里尝试 5 次
        while success_2 != 1 and try_time_2 <= self.max_try_time / 2:
            self.logger.info("当前(真)获取名册表次数为" + str(try_time_2))

            error = 1
            try_time = 1
            while error != 0 and try_time <= self.max_try_time:
                self.logger.info("当前获取名册表次数为" + str(try_time))
                try_time += 1
                loading = self.browser.find_elements(
                    by=By.CSS_SELECTOR,
                    value=r".el-loading-text"
                )
                error = len(loading)
                time.sleep(self.try_interval_sec)
        
            if error == 0:
                self.logger.info("获取名册表成功(伪)")
                total = int(self.browser.find_elements(
                    by=By.CSS_SELECTOR, value=r".el-pagination__total"
                )[0].get_attribute("innerHTML").split(' ')[1])

                # 没有人的话就重试
                if total == 0:
                    self.logger.warning("名册表数量为 0，可能存在 bug 或官网连接问题，重试查询。")
                    self.browser.refresh()
                else:
                    success_2 = 1
            
            try_time_2 += 1
        
        if success_2 == 1:
            self.logger.info("获取名册表成功(真)")
            time.sleep(3)
        else:
            self.logger.error("获取名册表失败")
            self.error = True
            self.error_code = "search time out"

    def search(self):

        if self.error:
            self.logger.error("search() 在开头遭遇 self.error")
            return None

        max_page = 15
        total = int(self.browser.find_elements(
            by=By.CSS_SELECTOR, value=r".el-pagination__total"
        )[0].get_attribute("innerHTML").split(' ')[1])
        self.logger.debug("共" + str(total) + "人")

        next_page_time = total // max_page

        while next_page_time >= 0:

            stu_list = self.browser.find_elements(
                by=By.CSS_SELECTOR,
                value=r".el-table__body > tbody .el-table_2_column_13.is-center.el-table__cell > .cell"
            )

            if len(stu_list) == 0:
                self.error = True
                self.error_code = "cannot find list"
                self.logger.error("查询到人员存在，却无法获得列表")
                return

            for mem in stu_list:
                self.logger.debug("检测到：" + mem.get_attribute("innerHTML"))
                self.done_list.append(mem.get_attribute("innerHTML"))
            
            if next_page_time >= 1:
                many_times_try(
                    log_func=lambda x: self.logger.info("当前点击下一页次数为" + x),
                    action_func=lambda:
                        self.browser.find_elements(
                            by=By.CSS_SELECTOR,
                            value=r".el-icon.el-icon-arrow-right"
                        )[0].click(),
                    times=self.max_try_time,
                    interval=self.try_interval_sec,
                    success_func=lambda: self.logger.info("点击成功"),
                    failure_func=lambda: self.logger.info("点击失败"),
                )

                time.sleep(2)

                error = 1
                try_time = 1
                while error != 0 and try_time <= self.max_try_time:
                    self.logger.info("当前获取下一页名册表次数为" + str(try_time))
                    try_time += 1
                    loading = self.browser.find_elements(
                        by=By.CSS_SELECTOR,
                        value=r".el-loading-text"
                    )
                    error = len(loading)
                    time.sleep(self.try_interval_sec)
                
                if error == 0:
                    self.logger.info("获取下一页名册表成功")
                else:
                    self.logger.error("获取下一页名册表失败")
                    return

            next_page_time -= 1

    def get_absent(self):

        if self.error:
            self.logger.error("get_absent() 在开头遭遇 self.error")
            return None

        absent = set(self.student_list) - set(self.done_list)
        self.logger.warning("未参加青年大学习的人有：" + str(absent))
        return absent


if __name__ == "__main__":

    def read_config(yaml_file) -> dict:
        file = open(yaml_file, 'r', encoding='utf-8')
        raw_data = file.read()
        file.close()
        data = yaml.safe_load(raw_data)
        return data

    data = read_config("./id.yaml")

    username = data.get("qn_username", "")
    password = data.get("qn_password", "")
    student_list = data.get("qn_students", [])

    q = QNDXX(username, password, student_list)
    q.login()
    q.goto_qndxx()
    q.search()
    res = q.get_absent()
    print(res)
