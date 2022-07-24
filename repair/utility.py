import numpy as np

from repair.str_utility import split_str, get_words_vector_by_tfidf, get_words_sim, get_str_sim


def is_screen_matched(x_screen, y_screen):
    """
    判断两个页面是否匹配
    用其中匹配上的叶子节点占比来判断
    :param x_screen:
    :param y_screen:
    :return:
    """

    x_leaf_nodes = []
    y_leaf_nodes = []

    for node in x_screen.nodes:
        if not node.children:
            x_leaf_nodes.append(node)

    for node in y_screen.nodes:
        if not node.children:
            y_leaf_nodes.append(node)

    length = max(len(x_leaf_nodes), len(y_leaf_nodes))
    matched_node_num = 0

    y_matched_node_idx = []

    for x_node in x_screen.nodes:
        x_path = x_node.xpath[1:]
        for y_node in y_screen.nodes:
            if y_node.idx not in y_matched_node_idx:
                y_path = y_node.xpath[1:]
                res = list(set(x_path) & set(y_path))
                if len(res) > 0:
                    print(x_node.attrib)
                    print(y_node.attrib)
                    print('--------------')
                    matched_node_num += 1
                    y_matched_node_idx.append(y_node.idx)

    print('matched_node_num', matched_node_num)
    print('length', length)

    if (matched_node_num / length) >= 0.8:
        return True

    return False





def is_xpath_matched(x_node, y_node):
    """
    判断两个节点是否可以根据xpath匹配上
    绝对路径的xpath不能算
    """

    for x_xpath in x_node.xpath[1:]:
        if x_xpath in y_node.xpath[1:]:
            print('进行元素匹配')
            print(x_node.xpath)
            print('-----------')
            print(y_node.xpath)
            print('公共xpath')
            print(x_xpath)
            return True

    return False


def read_source_script(file_path):
    """
    读取源脚本 提取信息
    :return:
    """

    caps = {}
    locators_str = []

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            # 去除被注释的代码行
            if line.strip() != '' and line.strip()[0] != '#':
                if 'platformName' in line:
                    # print(line.strip().split('=')[1])
                    caps['platformName'] = eval(line.strip().split('=')[1])

                if 'platformVersion' in line:
                    # print(line.strip().split('=')[1])
                    caps['platformVersion'] = eval(line.strip().split('=')[1])

                if 'deviceName' in line:
                    # print(line.strip().split('=')[1])
                    caps['deviceName'] = eval(line.strip().split('=')[1])

                if 'appPackage' in line:
                    # print(line.strip().split('=')[1])
                    caps['appPackage'] = eval(line.strip().split('=')[1])

                if 'appActivity' in line:
                    # print(line.strip().split('=')[1])
                    caps['appActivity'] = eval(line.strip().split('=')[1])

                if 'newCommandTimeout' in line:
                    # print(line.strip().split('=')[1])
                    caps['newCommandTimeout'] = eval(line.strip().split('=')[1])

                if 'noReset' in line:
                    # print(line.strip().split('=')[1])
                    caps['noReset'] = eval(line.strip().split('=')[1])

                if 'find_element' in line:
                    # print(line.strip())
                    locators_str.append(line.strip().split('=')[1])
                    # locators_str.append(line.strip())

        # print(locators_str)
        # print(caps)

        return caps, locators_str


def write_target_script(source_file_path, target_file_path):
    """
    编写新的测试脚本
    :param file_path:
    :return:
    """


def get_screen_sim_score(x_screen, y_screen):
    """
    获取两个页面的相似度 使用id/text/content-desc
    还需要考虑到步长的cost 在外部进行考虑
    :param x_screen:
    :param y_screen:
    :return:
    """

    # 首先分别搜集元素的 id text content-desc
    x_id = []
    x_text = []
    x_content = []

    for node in x_screen.nodes:
        if node.attrib['resource-id'] != '':
            if '/' in node.attrib['resource-id']:
                if '_' not in node.attrib['resource-id']:
                    x_id.append(node.attrib['resource-id'].split('/')[1])
                else:
                    tmp_list = node.attrib['resource-id'].split('/')[1].split('_')
                    x_id.extend(tmp_list)
            else:
                x_id.append(node.attrib['resource-id'])

        if node.attrib['text'] != '':
            x_text.append(node.attrib['text'].lower().strip())

        if node.attrib['content-desc'] != '':
            x_content.append(node.attrib['content-desc'].lower().strip())

    y_id = []
    y_text = []
    y_content = []

    for node in y_screen.nodes:
        if node.attrib['resource-id'] != '':
            if '/' in node.attrib['resource-id']:
                if '_' not in node.attrib['resource-id']:
                    y_id.append(node.attrib['resource-id'].split('/')[1])
                else:
                    tmp_list = node.attrib['resource-id'].split('/')[1].split('_')
                    y_id.extend(tmp_list)
            else:
                x_id.append(node.attrib['resource-id'])

        if node.attrib['text'] != '':
            y_text.append(node.attrib['text'].lower().strip())

        if node.attrib['content-desc'] != '':
            y_content.append(node.attrib['content-desc'].lower().strip())

    # 计算id的相似度
    x_id_words = split_str(x_id)
    tmp_str = ' '
    x_id_str = tmp_str.join(x_id_words)
    # 获取tfidf处理过的词汇
    xx_id_words, x_weight = get_words_vector_by_tfidf([x_id_str])

    y_id_words = split_str(y_id)
    tmp_str = ' '
    y_id_str = tmp_str.join(y_id_words)
    # 获取tfidf处理过的词汇
    yy_id_words, y_weight = get_words_vector_by_tfidf([y_id_str])
    id_sim = get_words_sim(xx_id_words, x_weight, yy_id_words, y_weight)

    # print(y_words)

    # 计算text的相似度
    x_text_words = split_str(x_text)
    tmp_str = ' '
    x_text_str = tmp_str.join(x_text_words)
    # 获取tfidf处理过的词汇
    xx_text_words, x_weight = get_words_vector_by_tfidf([x_text_str])

    # print(x_words)

    y_text_words = split_str(y_text)
    tmp_str = ' '
    y_text_str = tmp_str.join(y_text_words)
    # 获取tfidf处理过的词汇
    yy_text_words, y_weight = get_words_vector_by_tfidf([y_text_str])
    text_sim = get_words_sim(xx_text_words, x_weight, yy_text_words, y_weight)

    # print(y_words)

    # 计算content的相似度
    x_content_words = split_str(x_content)
    tmp_str = ' '
    x_content_str = tmp_str.join(x_content_words)
    # 获取tfidf处理过的词汇
    xx_content_words, x_weight = get_words_vector_by_tfidf([x_content_str])

    # print(x_words)

    y_content_words = split_str(y_content)
    tmp_str = ' '
    y_content_str = tmp_str.join(y_content_words)
    # 获取tfidf处理过的词汇
    yy_content_words, y_weight = get_words_vector_by_tfidf([y_content_str])
    content_sim = get_words_sim(xx_content_words, x_weight, yy_content_words, y_weight)

    # print(y_words)

    id_flag = True
    text_flag = True
    content_flag = True

    if xx_id_words[0] == 'none' and yy_id_words[0] == 'none':
        id_flag = False

    if xx_text_words[0] == 'none' and yy_text_words[0] == 'none':
        text_flag = False

    if xx_content_words[0] == 'none' and yy_content_words[0] == 'none':
        content_flag = False

    sim_list = []

    if id_flag:
        sim_list.append(id_sim)

    if text_flag:
        sim_list.append(text_sim)

    if content_flag:
        sim_list.append(content_sim)

    final_sim = 0

    # 要求各方面的相似值不能相差太大了
    # sim_flag = True
    count = 0
    for score in sim_list:
        final_sim += score
        if score < 0.1:
            # sim_flag = False
            count += 1

    #
    # if count / len(sim_list) < 0.5:
    #     final_sim /= len(sim_list)
    # else:
    #     final_sim = 0

    final_sim /= len(sim_list)

    return final_sim


def get_edge_sim_score(source_screens, source_edges, screens, edges, x_screen, y_screen):
    """
    计算到达页面两条边的相似度
    :param source_edges:
    :param edges:
    :param x_screen:
    :param y_screen:
    :return:
    """

    b_edge = None
    u_edge = None

    # 首先获取以x_screen为des的边
    for edge in source_edges:
        if edge.end_id == x_screen.id:
            b_edge = edge
            break

    # 然后获取以y_screen为des的边
    for edge in edges:
        if edge.end_id == y_screen.id:
            u_edge = edge
            break

    b_begin_screen = None
    u_begin_screen = None

    # 然后获取b_edge的起点页面
    for screen in source_screens:
        if screen.id == b_edge.begin_id:
            b_begin_screen = screen
            break

    # 然后获取u_edge的起点页面
    for screen in screens:
        if screen.id == u_edge.begin_id:
            u_begin_screen = screen
            break

    # 获取边中点击的元素
    b_node = b_begin_screen.get_node_by_id(b_edge.node_id)
    u_node = u_begin_screen.get_node_by_id(u_edge.node_id)

    if is_xpath_matched(b_node, u_node):
        sim = 1

    else:
        sim = get_str_sim(b_node, u_node)

    return sim


def get_edge_sequences_sim(source_screens, source_edges, screens, edges, s_i, t_j, w_length, step):
    """
    利用序列概率转移算法来计算
    :param source_screens:
    数组
    :param source_edges:
    数组
    :param screens:
    数组
    :param edges:
    数组
    :param s_i:
    数组中的序号 代表当前需要匹配的页面
    :param t_j:
    数组中的序号 代表上一个匹配好了的页面
    :param step:
    步长 用几步的相似度 去近似 整个序列的相似度 相当于w2
    :return:
    W is the maximal number of elements in F that a single element in E can be converted to
    w_length =
    """

    # 首先给出current score
    current_score = 0

    # 如果超出了 原序列的范围
    if s_i == len(source_screens):
        return current_score

    # 如果超出了设置的步长
    if step > w_length:
        return 0

    # 获取t_j之后三步可达的页面

    # 获得当前需要匹配的页面s_i
    screen_s_i = source_screens[s_i]

    # 搜集可达页面
    for i in range(1, w_length + 1):
        if t_j + i < len(screens):
            screen_t_k = screens[t_j + i]
            # 计算这些候选页面与页面s_i的相似度 要计算步长cost
            jump_t = i
            jump_s = 1
            jump_cost = np.log2(abs(jump_t - jump_s) + 1) + 1
            screen_sim = get_screen_sim_score(screen_s_i, screen_t_k)
            edge_sim = get_edge_sim_score(source_screens, source_edges, screens, edges, screen_s_i, screen_t_k)
            # 递归的含义就是 默认这一步可达的t_j + i 与s_i是匹配的 然后去计算后面的转移概率
            score_next = get_edge_sequences_sim(source_screens, source_edges, screens, edges,
                                                s_i + 1, t_j + i, w_length, step + 1)
            # 首次尝试增加权重
            # 由于相似的操作要在相同的页面里 所以screen_sim是很重要的 要被加大 另外 步长的惩罚也许需要相应的减少
            sim = 0.8 * screen_sim + 0.1 * edge_sim + 0.1 * score_next

            sim /= jump_cost

            if step == 0:
                print('---------')
                print('跳步数', i)
                print('screen_id', screen_t_k.id)
                print('screen_sim:', screen_sim)
                print('edge_sim:', edge_sim)
                print('score_next:', score_next)
                print('步长惩罚:', jump_cost)
                print('综合得分', sim)
                print('---------')

            if sim > current_score:
                current_score = sim

    return current_score
