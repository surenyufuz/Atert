import cv2
import os
import pickle
import time
import traceback
import xml.etree.ElementTree as xeTree
from appium import webdriver

from backend.edge import Edge
from backend.xml_tree import parse_nodes
from backend.screen import Screen
from backend.model import Model
from repair.search import Search
from repair.utility import read_source_script


class Recorder:
    """
    记录器类 从源脚本中提取进行 并重放 进行记录
    """

    def __init__(self, source_path, save_path):
        # 源测试脚本路径
        self.source_path = source_path

        # 保存文件路径
        self.save_path = save_path

        # appinum脚本匹配信息
        self.caps = {}
        self.locators_str = []

        # 源测试脚本遍历的页面和边
        self.screens = {}
        self.edges = []

        # 当前页面id
        self.cur_screen_id = -1

        self.screen_id = 1

        # 当前点击元素
        self.clicked_node = None

    def read_file(self):
        """
        读取源测试脚本中的信息
        :return:
        """

        self.caps, self.locators_str = read_source_script(self.source_path)

        print(self.caps)
        print(self.locators_str)

    def get_tmp_screen(self, driver):
        """
        dump当前页面 获得一个临时的screen节点
        :return:
        """

        xml_info = driver.page_source
        root = xeTree.fromstring(xml_info)
        nodes = parse_nodes(root)
        act_name = driver.current_activity
        tmp_screen = Screen(nodes, -1, act_name, True)

        return tmp_screen

    def save_screen(self, screen, driver, clicked_node):
        """
        保存页面信息
        :param screen:
        :return:
        """

        sub_dir = self.save_path + '/' + 'scenario_screens'
        if not os.path.exists(sub_dir):
            os.makedirs(sub_dir)

        # 获取屏幕截图
        driver.get_screenshot_as_file(sub_dir + '/' + str(screen.id) + '.png')

        # 保存xml文件
        with open(sub_dir + '/' + str(screen.id) + '.xml', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)

        screen.shot_dir = sub_dir + '/' + str(screen.id) + '.png'

        if clicked_node is not None:
            # 使用cv2读取该页面 然后将点击元素画出
            img = cv2.imread(screen.shot_dir)
            # 画出点击节点
            x1, y1, x2, y2 = clicked_node.parse_bounds()
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
            # 再次存储
            cv2.imwrite(sub_dir + '/' + str(screen.id) + '.png', img)

    def work(self):
        """
        对测试脚本进行重放
        :return:
        """

        print('正在记录源脚本的GUI信息')
        self.read_file()

        driver = webdriver.Remote('http://127.0.0.1:4723/wd/hub', self.caps)
        time.sleep(10)

        try:
            # 重放测试脚本
            for code in self.locators_str:

                if self.cur_screen_id == -1:
                    # dump当前页面
                    xml_info = driver.page_source
                    root = xeTree.fromstring(xml_info)
                    nodes = parse_nodes(root)
                    act_name = driver.current_activity
                    print(act_name)
                    screen = Screen(nodes, self.screen_id, act_name, True)

                    # 更新screen
                    self.cur_screen_id = screen.id

                    # 将其加入screen中
                    self.screens[self.cur_screen_id] = screen
                    self.screen_id += 1

                    # 定位当前操作元素
                    ele = eval(code)

                    # 获取元素的相应信息
                    for node in screen.nodes:
                        if ele.location['x'] == node.loc_x and \
                                ele.location['y'] == node.loc_y and \
                                'Group' not in ele.get_attribute('className'):
                            self.clicked_node = node
                            break

                    # 在找到操作元素后 保存页面
                    self.save_screen(screen, driver, self.clicked_node)

                    ele.click()
                    time.sleep(5)

                else:
                    # 记录页面的转移
                    tmp_screen = self.get_tmp_screen(driver)
                    tmp_screen.id = self.screen_id

                    # 将页面加入
                    self.screens[tmp_screen.id] = tmp_screen
                    self.screen_id += 1

                    # 记录边的转移
                    edge = Edge(self.cur_screen_id, tmp_screen.id, self.clicked_node.idx)
                    self.edges.append(edge)

                    # 记录页面之间的转移
                    self.screens[self.cur_screen_id].des.append(tmp_screen.id)
                    self.cur_screen_id = tmp_screen.id

                    # 定位当前操作元素
                    ele = eval(code)

                    # 获取元素的相应信息
                    for node in tmp_screen.nodes:
                        if ele.location['x'] == node.loc_x and \
                                ele.location['y'] == node.loc_y and \
                                'Group' not in ele.get_attribute('className'):
                            self.clicked_node = node
                            break

                    # 在找到操作元素后 保存页面
                    self.save_screen(tmp_screen, driver, self.clicked_node)

                    ele.click()
                    time.sleep(5)

            # 记录终点页面
            tmp_screen = self.get_tmp_screen(driver)
            # 记录页面的转移以及边
            tmp_screen.id = self.screen_id

            # 将页面加入
            self.screens[tmp_screen.id] = tmp_screen
            self.screen_id += 1

            edge = Edge(self.cur_screen_id, tmp_screen.id, self.clicked_node.idx)
            self.edges.append(edge)

            # 记录页面之间的转移
            self.screens[self.cur_screen_id].des.append(tmp_screen.id)
            self.cur_screen_id = tmp_screen.id

            # 保存页面
            self.save_screen(tmp_screen, driver, None)

            scenario_model = Model(self.screens, self.edges)
            model = pickle.dumps(scenario_model)

            with open(self.save_path + '/scenario_model', 'wb') as f:
                f.write(model)

            print('记录成功')

        except Exception as e:
            traceback.print_exc()
        finally:
            driver.quit()

    def test(self):

        self.read_file()
        # self.work()
        # tip = int(input("请卸载旧版本app 并安装新版本, 确认后输入1"))
        # if tip == 1:
        f = open(self.save_path + '/scenario_model', 'rb')
        scenario_model = pickle.load(f)
        obj = Search(2, self.caps, self.save_path, scenario_model.screens, scenario_model.edges)

        # obj.local_search([])
        # obj.get_similar_path(3)


if __name__ == '__main__':
    # 可封装为命令行工具 参数为script_path, save_path
    script_path = '../scripts/example-1.py'

    # 最好把存储路径设置为当前工作目录下的某个文件夹中
    save_path = '../example'

    obj = Recorder(script_path, save_path)
    # obj.run()
    obj.test()
