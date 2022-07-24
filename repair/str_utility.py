import numpy as np
import re
import jieba
import Levenshtein

from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer


def split_str(str_list):
    """
    将原始字符串进行分词
    :param id_list:
    :return:
    """

    final_str_list = []
    # 把句子按字分开，中文按字分，英文按单词，数字按空格
    res_eng = re.compile('[\\W]')
    res = re.compile(r"([\u4e00-\u9fa5])")

    for tmp_str in str_list:
        p1 = res_eng.split(tmp_str.lower())
        str_list = []
        for str in p1:
            # 分割中文
            if res.split(str) is None:
                str_list.append(str)
            else:

                # 说明存在中文 那可以尝试进行结巴分词
                ret = jieba.cut(str)
                for ch in ret:
                    str_list.append(ch)

        for ch in str_list:
            final_str_list.append(ch)

    final_str_list = [s for s in final_str_list if len(s.strip()) > 0]

    return final_str_list


def get_words_vector_by_tfidf(words):
    """
    输入字符串 返回tfidf模型所获得的向量 会过滤一些较短的词 比如一个字母 一个汉字
    :param words:
    :return:
    """

    # 首先看看是不是空的 或者过于简短 如果是 那么给它加东西
    tmp_str = words[0]
    new_list = []
    if tmp_str.strip() == '':
        words = ['none']
    else:
        str_list = tmp_str.split(' ')
        for s in str_list:
            res = re.match(r'[^\x00-\xff]', s)
            if len(s) < 2 and res is not None:
                tmp_s = s + s
                new_list.append(tmp_s)
            else:
                new_list.append(s)

        tmp_str = ' '
        tmp_str = tmp_str.join(new_list)
        words = [tmp_str]

    vectorizer = CountVectorizer()  # 该类将文本中的词语转换为词频矩阵

    transformer = TfidfTransformer()  # 该类会统计每个词语的tf-idf权值

    # 第一个fit_transform是计算tf-idf 第二个fit_transform是将文本转为词频矩阵

    # 所以理论上 只要输入文本 在这里就会产生词频向量 然后去计算文本余弦相似度即可
    tfidf = transformer.fit_transform(vectorizer.fit_transform(words))

    # 获取词袋模型中的所有词语
    word = vectorizer.get_feature_names()

    # 将tf-idf矩阵抽取出来 元素a[i][j]表示j词在i类文本中的tf-idf权重
    weight = tfidf.toarray()

    return word, weight[0]


def get_cos_dist(vec1, vec2):
    """

    :param vec1:  向量1
    :param vec2:  向量2
    :return: 返回两个向量的余弦相似度
    """

    dist1 = float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))
    return dist1


def get_words_sim(x_words, x_weight, y_words, y_weight):
    """
    计算两个词列表的tfidf的相似程度 使用余弦距离计算
    :param x_words:
    :param x_weight:
    :param y_words:
    :param y_weight:
    :return:
    """

    map1 = {}
    for i in range(len(x_words)):
        map1[x_words[i]] = x_weight[i]

    map2 = {}
    for i in range(len(y_words)):
        map2[y_words[i]] = y_weight[i]

        # 合并所有词集
    key_word = list(set(x_words + y_words))

    # 给定形状和类型的用0填充向量
    word_vector1 = np.zeros(len(key_word))
    word_vector2 = np.zeros(len(key_word))

    for i in range(len(key_word)):
        for key in map1.keys():
            if key_word[i] == key:
                word_vector1[i] = map1[key]

        for key in map2.keys():
            if key_word[i] == key:
                word_vector2[i] = map2[key]

    return get_cos_dist(word_vector1, word_vector2)


def get_str_sim(x_node, y_node):
    """
    获取两个节点间的字符文本相似度
    :param x_node:
    :param y_node:
    :return:
    """

    id_flag = False
    text_flag = False
    content_flag = False

    if x_node.attrib['resource-id'] != '' or y_node.attrib['resource-id'] != '':
        x_id = x_node.attrib['resource-id']
        y_id = y_node.attrib['resource-id']
        if x_node.attrib['resource-id'] != '':
            x_id = x_id.split('/')[1]

        if y_node.attrib['resource-id'] != '':
            y_id = y_id.split('/')[1]

        id_flag = True

        id_sim = 1 - Levenshtein.distance(x_id, y_id) / max(len(x_id), len(y_id))

    if x_node.attrib['text'] != '' or y_node.attrib['text'] != '':
        x_text = x_node.attrib['text']
        y_text = y_node.attrib['text']

        text_flag = True

        text_sim = 1 - Levenshtein.distance(x_text, y_text) / max(len(x_text), len(y_text))

    if x_node.attrib['content-desc'] != '' or y_node.attrib['content-desc'] != '':
        x_content = x_node.attrib['content-desc']
        y_content = y_node.attrib['content-desc']

        content_flag = True
        content_sim = 1 - Levenshtein.distance(x_content, y_content) / max(len(x_content), len(y_content))

    sim_list = []

    if id_flag:
        sim_list.append(id_sim)

    if text_flag:
        sim_list.append(text_sim)

    if content_flag:
        sim_list.append(content_sim)

    final_sim = 0

    for sim in sim_list:
        final_sim += sim

    if sim_list:
        return final_sim / len(sim_list)
    else:
        return final_sim
