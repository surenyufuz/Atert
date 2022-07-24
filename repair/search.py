import cv2
import os
import traceback
import time
import xml.etree.ElementTree as xeTree

from queue import Queue
from appium import webdriver

from backend.edge import Edge, has_same_edge
from backend.screen import Screen, is_same_screen
from backend.xml_tree import parse_nodes

from repair.utility import get_edge_sequences_sim, is_xpath_matched, is_screen_matched


class Search:
    """
    搜索类
    """

    def __init__(self, depth, caps, path, source_screens, source_edges, source_path):

        # 将原先的字典screen转换为列表 方便后续的相似度计算
        # self.source_screens = []
        # for key in source_screens.keys():
        #     screen = source_screens[key]
        #     self.source_screens.append(screen)

        self.source_screens = source_screens

        self.source_edges = source_edges

        # appium配置信息
        self.caps = caps

        # 遍历的深度 对应于论文中的参数 w1
        self.w_depth = depth

        # 局部遍历收集的页面信息
        self.screens = {}

        # 局部遍历手机边信息
        self.edges = []

        # 控制当前页面id
        self.screen_id = 1

        # 当前页面
        self.cur_screen_id = -1

        # 所有的结果路径
        self.event_sequences = []

        # 已经访问过的页面
        self.visited_screen_id = []

        # 页面队列
        self.screen_que = Queue()

        # 当前操作元素
        self.clicked_node = None

        # 用于记录遍历的当前深度
        self.cur_depth = 0

        # 遍历开始和结束时间
        self.start_time = 0
        self.cost_time = 0

        # 最终的结果路径
        self.final_sequence = []

        # 工作目录
        self.path = path

        # 搜索轮次
        self.turn = 1

        # 遍历开始和结束时间
        self.start_time = 0
        self.cost_time = 0

        # 每个轮次的最大搜索时间
        self.max_time = 10000

        # 页面对比时 所用的相似参数
        self.distinct_rate = 0.9

        # 应用包信息
        self.package_name = ''

        # 源测试脚本路径
        self.source_path = source_path

    def save_screen(self, screen, driver):
        """
        保存页面截图
        :return:
        """

        sub_dir = self.path + '/' + 'search_screens' + '/turn' + str(self.turn)

        if not os.path.exists(sub_dir):
            os.makedirs(sub_dir)

        try:
            # 获取屏幕截图
            driver.get_screenshot_as_file(sub_dir + '/' + str(screen.id) + '.png')

            screen.shot_dir = sub_dir + '/' + str(screen.id) + '.png'

            # 保存xml文件
            with open(sub_dir + '/' + str(screen.id) + '.xml', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)

        except Exception as  e:
            screen.shot_dir = 'none'
            traceback.print_exc()

    def action_click(self, tmp_node, driver):
        """
        对当前元素进行点击
        :return:
        """

        x, y = tmp_node.get_click_position()
        driver.tap([(x, y)])

        print('当前点击元素')
        print(tmp_node.attrib)

    def get_tmp_screen(self, driver):
        """
        dump当前页面 获得一个临时的screen节点
        :return:
        """

        xml_info = driver.page_source
        root = xeTree.fromstring(xml_info)
        nodes = parse_nodes(root)
        act_name = driver.current_activity
        tmp_screen = Screen(nodes, -1, act_name)

        return tmp_screen

    def has_same_screen(self, tmp_screen):
        """
        判断是否已有相同页面
        :param tmp_screen:
        :return:
        """

        for screen_id in self.screens.keys():
            screen = self.screens[screen_id]
            if is_same_screen(screen, tmp_screen, self.distinct_rate):
                return screen_id

        return -1

    def get_package_name(self):
        """
        初始获得包名
        初始获取包名可以从Manifest文件中获取
        还有一种获取包名的方法是 先dump 然后查看节点信息
        return:
        """

        try:
            cmd = "adb shell \"dumpsys window w | grep name=\""
            r = os.popen(cmd)
            info = r.readlines()

            for i in range(len(info)):
                if 'Activity' in info[i]:
                    package_name = info[i].strip().split('/')[0].split('name=')[1]
                    break
                else:
                    if 'mumu' not in info[i] and 'systemui' not in info[i] and '/' in info[i]:
                        package_name = info[i].strip().split('/')[0].split('name=')[1]
                        break

            return package_name
        except Exception as e:
            return 'error package name'

    def replay_by_edges(self, sequences, driver):
        """
        重放至当前页面
        :return:
        """

        if sequences:
            for edge in sequences:
                screen = self.screens[edge.begin_id]
                node = screen.get_node_by_id(edge.node_id)
                self.action_click(node, driver)
                time.sleep(5)

    def initial_search(self):
        """
        初始化搜索操作
        将当前的搜索结果置为空
        :return:
        """

        for key in self.screens:
            # 还原页面搜索配置
            screen = self.screens[key]
            # screen.all_transfer_sequences = []
            screen.cur_transfer_sequences = []
            screen.transfer_sequences_queue.queue.clear()
            screen.shortest_transfer_sequences = []

        # 当前页面
        self.cur_screen_id = -1

        # 所有的结果路径
        self.event_sequences = []

        # 已经访问过的页面
        self.visited_screen_id = []

        # 页面队列
        self.screen_que.queue.clear()

        # 当前操作元素
        self.clicked_node = None

        # 用于记录遍历的当前深度
        self.cur_depth = 0

    def get_cur_screen_id(self, driver):
        """
        获取当前页面id
        如果是新页面 那么加入
        如果是老页面 直接返回其id
        :return:
        """

        # 判断当前页面是否是新页面
        tmp_screen = self.get_tmp_screen(driver)
        exist_screen_id = self.has_same_screen(tmp_screen)

        # 新页面
        if exist_screen_id == -1:
            # 加入新页面
            tmp_screen.id = self.screen_id
            print('发现新页面')
            self.screens[self.screen_id] = tmp_screen
            self.screen_id += 1
            self.cur_screen_id = tmp_screen.id
            self.save_screen(tmp_screen, driver)
        else:
            self.cur_screen_id = exist_screen_id

    def local_search(self, seq_to_begin, driver, tmp_source_edges):
        """
        局部搜索 限定深度 广度优先
        思路 使用队列存储各页面 然后点击
        还需要存储到达各页面的路径 用于后续的路径拼接
        类似于实现树的层次遍历

        其实只要找到了最终的匹配页面 就不用搜索下去了 可以给出一个阈值 相对可以给高一点


        :param tmp_source_edges:
        :param driver:
        :param w_depth:
        :param seq_to_begin 搜索时指定到达起点的序列
        :return:
        """

        print('当前待匹配序列长度为')
        print(len(tmp_source_edges))

        # 获得当前待匹配序列的终点页面
        final_edge = tmp_source_edges[-1]
        final_screen = self.source_screens[final_edge.end_id]

        print('当前待匹配序列页面终点为')
        print(final_screen.id)
        print('页面主要内容')
        for node in final_screen.nodes:
            if node.attrib['text'] != '':
                print(node.attrib['text'])

        self.start_time = time.time()

        self.package_name = self.get_package_name()

        cur_level_num = 1
        next_level_num = 0
        cur_level = 0

        self.get_cur_screen_id(driver)

        print('起点页面id')
        print(self.cur_screen_id)

        screen = self.screens[self.cur_screen_id]

        if seq_to_begin:

            # 初始化到达起点的操作序列
            screen.transfer_sequences_queue.put(seq_to_begin)
            screen.shortest_transfer_sequences = seq_to_begin

        # 页面加入队列
        self.screen_que.put(screen.id)

        # 当队列不为空的时候
        # break_flag = False
        while not self.screen_que.empty():
            print('当前页面层次为')
            print(cur_level)

            # cur_level 是页面的深度 而不是边的深度 所以当页面深度为2时 其实已经包含了两个操作了
            if cur_level == len(tmp_source_edges) + 1:
                print('超过搜索深度')
                break

            # 判断时间是否到达最大
            if self.cost_time > self.max_time:
                print('时间到')
                print(self.cost_time)
                break

            # 队头页面出队 还需要重新打开app 然后重放到这个cur_screen才行 （目前默认重新打开 回到初始页面 然后进行必要的重放）

            self.cur_screen_id = self.screen_que.get()
            cur_screen = self.screens[self.cur_screen_id]

            # 页面出栈的时候 同时更新到达当前页面的所在序列
            if not cur_screen.transfer_sequences_queue.empty():
                cur_screen.cur_transfer_sequences = cur_screen.transfer_sequences_queue.get()

            print('当前页面为')
            print(self.cur_screen_id)

            # 这里貌似也要进行必要的重放
            driver.close_app()
            driver.start_activity(self.caps['appPackage'], self.caps['appActivity'])
            time.sleep(5)

            # 如何获取所有页面 并进行点击 并记录每一个页面的层次（仿照树的层次遍历）
            # 然后screen 获取可点击元素那里 可以进行改进 直接返回一个列表 而不是一步一步返回
            cur_level_num -= 1

            clickable_nodes = cur_screen.get_clickable_leaf_nodes()

            # for node in clickable_nodes:
            #     print(node.attrib)
            #     print('-------------')
            #
            # exit(0)

            clicked_num = 0
            # 遍历这些节点 然后进行点击
            for node in clickable_nodes:
                print('当前页面为')
                print(self.cur_screen_id)

                print('当前页面层次为')
                print(cur_level)

                print('待点击元素数量')
                print(len(clickable_nodes) - clicked_num)

                # 这里貌似也要进行必要的重放
                driver.close_app()
                driver.start_activity(self.caps['appPackage'], self.caps['appActivity'])
                time.sleep(5)

                # 利用最短序列进行重放
                shortest_sequence = cur_screen.shortest_transfer_sequences

                print('当前重放路径长度为')
                print(len(shortest_sequence))
                print('重放序列')
                print('-------')
                self.replay_by_edges(shortest_sequence, driver)
                print('重放完成')
                print('-------')

                self.action_click(node, driver)
                clicked_num += 1
                time.sleep(5)

                # 创建临时screen 判别是否发生页面转换
                tmp_screen = self.get_tmp_screen(driver)
                exist_screen_id = self.has_same_screen(tmp_screen)

                # 如果发生了页面转换
                if exist_screen_id != self.cur_screen_id:
                    # 如果不是发现了新页面
                    if exist_screen_id != -1:
                        print('已有相同界面')
                        print(exist_screen_id)

                        # 记录页面之间的转移
                        if exist_screen_id not in self.screens[self.cur_screen_id].des:
                            self.screens[self.cur_screen_id].des.append(exist_screen_id)

                        print('页面的转移')
                        print('source')
                        print(self.cur_screen_id)
                        print('des')
                        print(exist_screen_id)

                        if True:
                            edge = Edge(self.cur_screen_id, exist_screen_id, node.idx)

                            # self.edges.append(edge)

                            print('当前边')
                            print(edge)

                            # 然后该页面进队列
                            self.screen_que.put(exist_screen_id)
                            next_level_num += 1

                            # if not cur_screen.all_transfer_sequences:
                            if not cur_screen.cur_transfer_sequences:

                                print('当前边')
                                print(edge)

                                print('上一个页面序列为空')

                                tmp_event_seq = [edge]

                                print('当前加入事件')
                                print(tmp_event_seq)

                                # 将当前拼接后的事件序列加入候选事件序列中
                                self.event_sequences.append(tmp_event_seq)

                                # 将当前拼接后的事件序列 接入该页面重放事件序列当中
                                # self.screens[exist_screen_id].all_transfer_sequences.append(tmp_event_seq)
                                # self.screens[exist_screen_id].cur_transfer_sequences = tmp_event_seq
                                self.screens[exist_screen_id].transfer_sequences_queue.put(tmp_event_seq)

                                if not self.screens[exist_screen_id].shortest_transfer_sequences or \
                                        len(tmp_event_seq) < len(
                                    self.screens[exist_screen_id].shortest_transfer_sequences):
                                    self.screens[exist_screen_id].shortest_transfer_sequences = tmp_event_seq

                                # 如果当前页面与原序列终点匹配 那么结束
                                if is_screen_matched(final_screen, self.screens[exist_screen_id]):
                                    print('遇到终点页面 停止搜索')
                                    return


                            else:
                                print('上一个页面序列非空')
                                # 将事件与之前的页面事件进行拼接 (这种拼接是不合理的)

                                pre_event_seq = cur_screen.cur_transfer_sequences[0:]
                                tmp_event_seq = pre_event_seq.copy()
                                tmp_event_seq.append(edge)

                                # 将当前拼接后的事件序列加入候选事件序列中 要把头部重放事件去除
                                self.event_sequences.append(tmp_event_seq[len(seq_to_begin):])

                                # 更新当前事件序列
                                # self.screens[exist_screen_id].cur_transfer_sequences = tmp_event_seq

                                # 当前序列进队列
                                self.screens[exist_screen_id].transfer_sequences_queue.put(tmp_event_seq)

                                if not self.screens[exist_screen_id].shortest_transfer_sequences or \
                                        len(tmp_event_seq) < len(
                                    self.screens[exist_screen_id].shortest_transfer_sequences):
                                    self.screens[exist_screen_id].shortest_transfer_sequences = tmp_event_seq

                                # 如果当前页面与原序列终点匹配 那么结束
                                if is_screen_matched(final_screen, self.screens[exist_screen_id]):
                                    print('遇到终点页面 停止搜索')
                                    return

                    else:
                        # 发现新界面
                        tmp_screen.id = self.screen_id
                        tmp_package_name = self.get_package_name()

                        if tmp_package_name == self.package_name:
                            print('发现新页面')
                            self.screens[self.screen_id] = tmp_screen
                            self.screen_id += 1

                            edge = Edge(self.cur_screen_id, tmp_screen.id, node.idx)
                            # self.edges.append(edge)

                            print('当前边')
                            print(edge)

                            # 记录页面之间的转移
                            self.screens[self.cur_screen_id].des.append(tmp_screen.id)

                            print('页面的转移')
                            print('source')
                            print(self.cur_screen_id)
                            print('des')
                            print(tmp_screen.id)

                            # 页面入队列
                            self.screen_que.put(tmp_screen.id)
                            next_level_num += 1

                            self.save_screen(tmp_screen, driver)

                            # if not cur_screen.all_transfer_sequences:
                            if not cur_screen.cur_transfer_sequences:
                                print('当前边')
                                print(edge)

                                tmp_event_seq = [edge]

                                print('上一个页面序列为空')

                                print('当前加入事件')
                                print(tmp_event_seq)

                                # 将当前拼接后的事件序列加入候选事件序列中
                                self.event_sequences.append(tmp_event_seq)

                                # 将当前拼接后的事件序列 接入该页面重放事件序列当中
                                # self.screens[tmp_screen.id].all_transfer_sequences.append(tmp_event_seq)

                                # 当前序列进队列
                                self.screens[tmp_screen.id].transfer_sequences_queue.put(tmp_event_seq)

                                if not self.screens[tmp_screen.id].shortest_transfer_sequences or \
                                        len(tmp_event_seq) < len(
                                    self.screens[tmp_screen.id].shortest_transfer_sequences):
                                    self.screens[tmp_screen.id].shortest_transfer_sequences = tmp_event_seq

                                # 如果当前页面与原序列终点匹配 那么结束
                                if is_screen_matched(final_screen, tmp_screen):
                                    print('遇到终点页面 停止搜索')
                                    return

                            else:

                                print('上一个页面序列非空')

                                # 将事件与之前的页面事件进行拼接 (原来的拼接是有问题的)

                                pre_event_seq = cur_screen.cur_transfer_sequences[0:]
                                tmp_event_seq = pre_event_seq.copy()
                                tmp_event_seq.append(edge)

                                # 将当前拼接后的事件序列加入候选事件序列中 要把头部重放事件去除
                                self.event_sequences.append(tmp_event_seq[len(seq_to_begin):])

                                # 当前序列进队列
                                self.screens[tmp_screen.id].transfer_sequences_queue.put(tmp_event_seq)

                                if not self.screens[tmp_screen.id].shortest_transfer_sequences or \
                                        len(tmp_event_seq) < len(
                                    self.screens[tmp_screen.id].shortest_transfer_sequences):
                                    self.screens[tmp_screen.id].shortest_transfer_sequences = tmp_event_seq

                                if is_screen_matched(final_screen, tmp_screen):
                                    print('遇到终点页面 停止搜索')
                                    return
                        else:
                            print('跳出了应用 不保存应用外的页面')
                            continue


                else:
                    print('页面未发生转换')
                    continue

            if cur_level_num == 0:
                cur_level_num = next_level_num
                next_level_num = 0
                cur_level += 1

        print('当前搜索到的事件序列数量')
        print(len(self.event_sequences))

        print('搜索完毕')

    def get_path_screens(self, edges, v_screens):
        """
        输入edge序列 返回页面序列
        :return:
        """

        re_screens = []

        # 搜集页面
        for edge in edges:
            screen = v_screens[edge.begin_id]
            re_screens.append(screen)

        # 搜集终点页面
        final_edge = edges[-1]
        des_screen = v_screens[final_edge.end_id]

        re_screens.append(des_screen)

        return re_screens

    def get_similar_path(self, tmp_source_screens, tmp_source_edges):
        """
        从候选路径中 根据相似得分 得到最优路径
        :return:
        """

        max_score = 0
        final_seq = self.event_sequences[0]

        print('计算相似序列')

        for i in range(len(self.event_sequences)):
            # 边的序列
            edges = self.event_sequences[i]
            screens = self.get_path_screens(edges, self.screens)

            # 注意 页面要比edge多一个
            # tmp_source_screens = self.source_screens[0:w_depth + 1]
            # tmp_source_edges = self.source_edges[0:w_depth]

            # print('tmp_source_screens的长度')
            # print(len(tmp_source_screens))
            #
            # print('tmp_source_edges的长度')
            # print(len(tmp_source_edges))

            print('------------')
            print('序列' + str(i))
            print('长度')
            print(len(screens))
            for edge in edges:
                screen = self.screens[edge.begin_id]
                clicked_node = screen.get_node_by_id(edge.node_id)
                print('source')
                print(edge.begin_id)
                print('clicked_node')
                print(clicked_node.attrib)
                print('des')
                print(edge.end_id)

            # 更改为两边都可以跳步
            print('score1')
            score1 = get_edge_sequences_sim(tmp_source_screens, tmp_source_edges, screens,
                                            edges, 1, 0, self.w_depth, 0)
            print(score1)

            print('score2')
            score2 = get_edge_sequences_sim(screens, edges, tmp_source_screens, tmp_source_edges, 1, 0, self.w_depth, 0)
            print(score2)

            score = max(score1, score2)

            print('最终得分')
            print(score)
            print('------------')

            if score > max_score:
                max_score = score
                final_seq = edges

        return final_seq

    def work(self):
        """
        搜索策略函数
        :return:
        """

        try:
            print('进行测试修复过程')
            # 连接appium
            driver = webdriver.Remote('http://127.0.0.1:4723/wd/hub', self.caps)
            time.sleep(10)

            # 默认到达的当前的页面 通过重放路径到达
            # self.replay(seq_to_begin, driver)

            # 从第0步开始走
            source_edge_index = 0

            while source_edge_index < len(self.source_edges):
                print('当前的source_edge_index')
                print('当前正在修复的动作序号')
                print(source_edge_index)
                # 重新打开app 并重放之前已经选择的测试用例
                driver.close_app()
                driver.start_activity(self.caps['appPackage'], self.caps['appActivity'])
                time.sleep(5)
                self.replay_by_edges(self.final_sequence, driver)

                # 获取当前的edge
                edge = self.source_edges[source_edge_index]
                screen = self.source_screens[edge.begin_id]
                clicked_node = screen.get_node_by_id(edge.node_id)

                print('修复的原动作为')
                print(clicked_node.attrib)

                matched_node = None
                # 然后在当前页面里看 是否有可以使用xpath匹配的元素
                tmp_screen = self.get_tmp_screen(driver)
                for node in tmp_screen.nodes:
                    if is_xpath_matched(clicked_node, node):
                        matched_node = node
                        break

                # 说明当前页面可以找到匹配节点
                if matched_node is not None:
                    print('当前节点能够匹配')

                    # 判断当前页面是否是新页面
                    self.get_cur_screen_id(driver)
                    begin_id = self.cur_screen_id
                    # click到终点页面
                    self.action_click(matched_node, driver)
                    time.sleep(5)
                    self.get_cur_screen_id(driver)
                    end_id = self.cur_screen_id

                    print('begin_id')
                    print(begin_id)
                    print('end_id')
                    print(end_id)

                    # 记录边操作
                    re_edge = Edge(begin_id, end_id, matched_node.idx)

                    # 将此边加入结果边中
                    self.final_sequence.append(re_edge)

                    # 往后走一步
                    source_edge_index += 1

                    # 整个搜索回合向后走一步
                    self.turn += 1

                else:
                    print('当前节点不能够匹配')

                    # 否则 按照步长取出当前的screens 以及edges 然后进行搜索
                    tmp_edge_index = source_edge_index
                    num = 0

                    # 注意 如果是取出头部两个操作 那么只要 + 1即可
                    while tmp_edge_index < len(self.source_edges) and num < self.w_depth - 1:
                        num += 1
                        tmp_edge_index += 1

                    # 然后相对应的取出screens 以及 edges
                    tmp_source_edges = self.source_edges[source_edge_index: tmp_edge_index + 1]
                    tmp_source_screens = self.get_path_screens(tmp_source_edges, self.source_screens)
                    #  开启搜索模式
                    print('开启搜索模式')
                    self.initial_search()

                    self.local_search(self.final_sequence, driver, tmp_source_edges)
                    # 保存局部搜索所得的候选路径
                    self.save_tmp_work()


                    similar_path = self.get_similar_path(tmp_source_screens, tmp_source_edges)

                    self.final_sequence.extend(similar_path)

                    source_edge_index = tmp_edge_index + 1

                    self.turn += 1

            print('寻找路径成功')

            print('最终所得路径为')
            for edge in self.final_sequence:
                print('source')
                print(edge.begin_id)
                print('des')
                print(edge.end_id)
                print('点击元素')
                node = self.screens[edge.begin_id].get_node_by_id(edge.node_id)
                print(node.attrib)

        except Exception as e:
            print(e)
            traceback.print_exc()

        finally:
            driver.quit()

    def save_tmp_work(self):
        """
        保存每一次寻路阶段所得的候选路径
        :return:
        """

        tmp_result_dir = self.path + '/' + 'candidate_path' + '/turn' + str(self.turn)

        try:
            for i in range(len(self.event_sequences)):
                # 边的序列
                edges = self.event_sequences[i]
                # screens = self.get_path_screens(edges, self.screens)

                e_count = 1
                for edge in edges:
                    # 找到页面
                    screen = self.screens[edge.begin_id]
                    # 找到节点
                    clicked_node = screen.get_node_by_id(edge.node_id)

                    img_path = screen.shot_dir

                    # 读取图片
                    img = cv2.imread(img_path)

                    # 画出点击节点
                    x1, y1, x2, y2 = clicked_node.parse_bounds()
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)

                    e_count += 1

                    tmp_dir = tmp_result_dir + '/path' + str(i)

                    if not os.path.exists(tmp_dir):
                        os.makedirs(tmp_dir)

                    cv2.imwrite(tmp_dir + '/' + 'action' + str(e_count) + '.png', img)

                # 搜集一下终点
                final_edge = edges[-1]
                final_screen = self.screens[final_edge.end_id]
                img_path = final_screen.shot_dir

                # 读取图片
                img = cv2.imread(img_path)

                cv2.imwrite(tmp_dir + '/' + 'des.png', img)

        except Exception as e:
            traceback.print_exc()
            pass

    def save_work(self):
        """
        保存页面以及交互元素信息
        :return:
        """

        print('正在保存结果GUI信息')
        result_dir = self.path + '/' + 'result_screens'
        if not os.path.exists(result_dir):
            os.makedirs(result_dir)

        e_count = 1
        for edge in self.final_sequence:
            # 找到页面
            screen = self.screens[edge.begin_id]
            # 找到节点
            clicked_node = screen.get_node_by_id(edge.node_id)

            img_path = screen.shot_dir

            # 读取图片
            img = cv2.imread(img_path)

            # 画出点击节点
            x1, y1, x2, y2 = clicked_node.parse_bounds()
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)

            cv2.imwrite(result_dir + '/' + 'action' + str(e_count) + '.png', img)
            e_count += 1

        # 然后搜集一下终点页面
        final_edge = self.final_sequence[-1]
        final_screen = self.screens[final_edge.end_id]
        img_path = final_screen.shot_dir

        # 读取图片
        img = cv2.imread(img_path)

        cv2.imwrite(result_dir + '/' + 'des.png', img)

    def get_target_script(self):
        """
        获得更新之后的脚本
        :return:
        """

        print('正在生成修复后的目标测试脚本')
        with open(self.path + '/' + 'target_script.py', 'w', encoding='utf-8') as f_w:

            f_w.writelines('import time')
            f_w.writelines('\n')
            f_w.writelines('from appium import webdriver')
            f_w.writelines('\n\n')

            f_w.writelines('desired_caps = {}')
            f_w.writelines('\n')

            with open(self.source_path, 'r', encoding='utf-8') as f_r:
                lines = f_r.readlines()
                for line in lines:
                    # 去除被注释的代码行
                    if line.strip() != '' and line.strip()[0] != '#':
                        if 'platformName' in line:
                            f_w.writelines(line)
                            # f_w.writelines('\n')

                        if 'platformVersion' in line:
                            f_w.writelines(line)
                            # f_w.writelines('\n')

                        if 'deviceName' in line:
                            f_w.writelines(line)
                            # f_w.writelines('\n')

                        if 'appPackage' in line:
                            f_w.writelines(line)
                            # f_w.writelines('\n')

                        if 'appActivity' in line:
                            f_w.writelines(line)
                            # f_w.writelines('\n')

                        if 'newCommandTimeout' in line:
                            f_w.writelines(line)
                            # f_w.writelines('\n')

                        if 'noReset' in line:
                            f_w.writelines(line)
                            f_w.writelines('\n')

            f_w.writelines("driver = webdriver.Remote('http://127.0.0.1:4723/wd/hub', desired_caps)")
            f_w.writelines('\n')
            f_w.writelines('time.sleep(10)')
            f_w.writelines('\n\n')

            # 开始写元素定位
            # 元素定位语句
            for edge in self.final_sequence:
                screen = self.screens[edge.begin_id]
                # 获得点击的元素
                clicked_node = screen.get_node_by_id(edge.node_id)

                print(clicked_node.xpath)

                # 总共支持id,text,content-desc,以及坐标定位
                for attr_path in clicked_node.xpath:
                    if 'resource-id' in attr_path and '&&' not in attr_path:
                        print(attr_path)
                        clicked_node.loc_method['id'] = 1

                    if 'text' in attr_path and '&&' not in attr_path:
                        print(attr_path)
                        clicked_node.loc_method['text'] = 1

                    if 'content-desc' in attr_path and '&&' not in attr_path:
                        print(attr_path)
                        clicked_node.loc_method['content-desc'] = 1

                print(clicked_node.loc_method)

                if clicked_node.loc_method['id'] == 1 and clicked_node.attrib2['resource-id'] != '':
                    loc_text = "el = driver.find_element_by_id" + "('" + clicked_node.attrib2['resource-id'] + "')"
                    f_w.writelines(loc_text)
                    f_w.writelines('\n')
                    f_w.writelines('el.click()')
                    f_w.writelines('\n')
                    f_w.writelines('time.sleep(5)')
                    f_w.writelines('\n\n')
                    continue

                if clicked_node.loc_method['text'] == 1 and clicked_node.attrib2['text'] != '':
                    loc_text = "el = driver.find_element_by_android_uiautomator" + \
                               "(" + "'new UiSelector().text(\"" + clicked_node.attrib2['text'] + "\"" + ")'" + ")"
                    f_w.writelines(loc_text)
                    f_w.writelines('\n')
                    f_w.writelines('el.click()')
                    f_w.writelines('\n')
                    f_w.writelines('time.sleep(5)')
                    f_w.writelines('\n\n')
                    continue

                if clicked_node.loc_method['content-desc'] == 1 and clicked_node.attrib2['content-desc'] != '':
                    loc_text = "el = driver.find_element_by_accessibility_id" + \
                               "('" + clicked_node.attrib2['content-desc'] + "')"
                    f_w.writelines(loc_text)
                    f_w.writelines('\n')
                    f_w.writelines('el.click()')
                    f_w.writelines('\n')
                    f_w.writelines('time.sleep(5)')
                    f_w.writelines('\n\n')
                    continue

                # 最后则使用坐标定位
                x, y = clicked_node.get_click_position()
                # driver.tap([(x, y)])
                loc_text = "el = driver.tap([(" + str(x) + ", " + str(y) + ")])"
                f_w.writelines(loc_text)
                f_w.writelines('\n')
                f_w.writelines('el.click()')
                f_w.writelines('\n')
                f_w.writelines('time.sleep(5)')
                f_w.writelines('\n\n')

            f_w.writelines('driver.quit()')

            print('目标测试脚本生成完毕')
