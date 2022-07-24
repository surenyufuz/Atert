import pickle
from repair.record import Recorder
from repair.search import Search


def main(depth):
    # 可封装为命令行工具 参数为script_path, save_path, depth
    script_path = '../scripts/example1.py'
    # 最好把存储路径设置为当前工作目录下的某个文件夹中

    save_path = '../example31'
    record_obj = Recorder(script_path, save_path)
    record_obj.read_file()
    record_obj.work()

    f = open(save_path + '/scenario_model', 'rb')
    scenario_model = pickle.load(f)

    key = int(input('确保安装应用的新版本 输入1进行确认:'))

    if key == 1:
        search_obj = Search(depth, record_obj.caps, save_path,
                            scenario_model.screens, scenario_model.edges, script_path)
        search_obj.work()
        search_obj.save_work()
        search_obj.get_target_script()


# 建议参数depth选择1 如果选2的话 再往后看一步 需要遍历到第三个层次 时间很长
"""
参数的含义：假设源测试脚本路径长度为4，页面转移序列为
s1->s2->s3->s4

那么参数为1的时候，我们逐个事件进行修复。
先修复s1->s2，然后将应用当前状态转到s2，再进行修复s2->s3...
此时，我们的待修复子序列长度(测试事件长度)为1，那么我们寻找待匹配的长度要求小于等于2，即可以是1也可以是2。

参数为2的时候，我们每两个事件进行修复。
先修复s1->s2->s3，然后将应用当前状态转到s3,再修复剩下的事件...
此时，我们待修复子序列长度(测试事件长度)为2，那么我们寻找待匹配的长度要求小于等于3，即可以是2也可以是3。

经过测试，发现参数为1更为合适，参数为2时，搜索的时间很长，有时就约等于全局遍历。

寻找完待匹配序列之后，我们使用概率转移序列进行计算各待匹配序列的相似度。

"""
main(1)





