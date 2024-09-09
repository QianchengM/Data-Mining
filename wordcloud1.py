import jieba
import collections
import re
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import os
from PIL import Image
import numpy as np

jieba.setLogLevel(jieba.logging.INFO)
fo = open(os.path.dirname(__file__) + "/cases", "r", encoding="utf-8")
txt = fo.read()

# 文本预处理  去除一些无用的字符   只提取出中文出来
new_data = re.findall('[\u4e00-\u9fa5]+', txt, re.S)
new_data = " ".join(new_data)

# 文本分词
seg_list_exact = jieba.cut(new_data, cut_all=True)

result_list = []
with open('stopword', encoding='utf-8') as f:
    con = f.readlines()
    stop_words = set()
    for i in con:
        i = i.replace("\n", "")   # 去掉读取每一行数据的\n
        stop_words.add(i)

for word in seg_list_exact:
    # 设置停用词并去除单个词
    if word not in stop_words and len(word) > 1:
        result_list.append(word)
#print(result_list)

# 筛选后统计
word_counts = collections.Counter(result_list)
# 获取前100最高频的词
word_counts_top100 = word_counts.most_common(100)
print(word_counts_top100)

MASK=np.array(Image.open('./hebei.jpg'))

# 绘制词云
my_cloud = WordCloud(
    background_color='white',  # 设置背景颜色  默认是black
    width=900, height=600,
    max_words=80,            # 词云显示的最大词语数量
    font_path='simhei.ttf',   # 设置字体  显示中文
    max_font_size=150,         # 设置字体最大值
    min_font_size=16,         # 设置子图最小值
    random_state=98,           # 设置随机生成状态，即多少种配色方案
    mask = MASK
).generate_from_frequencies(word_counts)

# 显示生成的词云图片
plt.imshow(my_cloud, interpolation='bilinear')
# 显示设置词云图中无坐标轴
plt.axis('off')
plt.show()