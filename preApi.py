import re
import time
import requests
import json
import os
import locale

locale.setlocale(locale.LC_CTYPE, 'chinese')


# 地点
# area 家0  村1  村out2
# recommend 表示活动地点
# state 无0 阴1 阳2
class Item:
    def __init__(self):
        self.t = -1
        self.route = ''
        self.area = 0  # area 家0  村1  村out2
        self.recommend = ''  # recommend 表示活动地点
        self.points = []
        self.state = -1  # state 无0 阴1 阳2
        self.symptem = ''


def parseRoute(item, lastitem):  # 分析行径
    item.route = re.sub('一直', '', item.route)
    item.route = re.sub('(持续)|，|(期间)|((其余时)?间)|(参加活动)|(患者)|([上下]午)|(晚上)|(凌晨)', '', item.route)
    # 删除无关字符
    t6 = re.search('周[日一二三四五六]', item.route)
    while t6:
        # print(item.route)
        t7 = re.match(r'[^周]*周([日一二三四五六])[和、]?每?周([日一二三四五六])([^周]*)(.*)', item.route)
        # 匹配 周几 每周几 周几和周几
        if t7:
            wday1 = wday2int(t7.group(1))  # 汉字切换到数字 一：1
            wday2 = wday2int(t7.group(2))
            wday0 = day2wday(item.t)  # 通过t计算周几
            if wday0 == wday1:
                item.route = ''
                if t7.group(3):
                    item.route = t7.group(3)
            elif wday0 == wday2:
                item.route = ''
                if t7.group(3):
                    item.route = t7.group(3)
            else:
                item.route = ''
                if t7.group(4):
                    item.route = t7.group(4)

        else:
            t7 = re.match(r'[^周]*周([日一二三四五六])[至到]每?周([日一二三四五六])([^周]*)(.*)', item.route)
            if t7:
                wday0 = day2wday(item.t)
                wday1 = wday2int(t7.group(1))
                wday2 = wday2int(t7.group(2))
                if wday0 in range(wday1, wday2):
                    item.route = ''
                    if t7.group(3):
                        item.route = t7.group(3)
                else:
                    item.route = ''
                    if t7.group(4):
                        item.route = t7.group(4)
            else:
                t7 = re.match(r'[^周]*周([日一二三四五六])([^周]*)(.*)', item.route)
                wday0 = day2wday(item.t)
                wday1 = wday2int(t7.group(1))
                if wday0 == wday1:
                    item.route = ''
                    if t7.group(2):
                        item.route = t7.group(2)
                else:
                    item.route = ''
                    if t7.group(3):
                        item.route = t7.group(3)
        t6 = re.search('周[日一二三四五六]', item.route)

    # 居家
    t1 = re.search(r'[居在]家', item.route)
    if t1:
        # print(item.route)
        item.recommend = '在家'
        item.route = re.sub(r'，?(长期)?[居在]家((隔离)|([无未]外出))?', '', item.route)

    t2 = re.search(r'[在居].*?本?村.*?', item.route)
    if t2:
        if item.area < 1:
            item.area = 1
            item.recommend = '在村'
        item.route = re.sub(r'[居在]本?村内?', '', item.route)
        item.route = re.sub(r'[无未]外出', '', item.route)
        item.route = re.sub(r'(患者)?(一直)?(以来)?(后)?，?', '', item.route)

    t2 = re.search(r'[无未]外出', item.route)
    t2 = re.search(r'去', item.route)
    if t2:
        pass

    t2 = re.search(r'[去到在经营住前往至从经]', item.route)
    if t2:
        t3 = re.search(
            r'[去到在经营住前往至从过达回和、]([^去到在观经核今营确赶由住、状前为病往至从过进和上住下午返乘]{2,}[信誉楼超市麦当劳区校影美食公司村店场院学社馆铺苑府所厅寓点地房站虾堡系厂堂镇庄街路诊])(.*)',
            item.route)
        # print(item.route)
        while t3:
            if t3.group(1):
                # 居住
                if re.search(r'(附近)|某|(本村)|(无外出)|(隔离)|(儿科)|(住院)|(同一)|(自家)|(省二院)|(村诊所)|(采样点)|(就诊)|(发热门诊)', t3.group(1)):
                    pass
                elif re.match(r'(沙发厂)|(药房二楼)|(木村村内向村)|(小区第12幢楼朋友家会)|(小区内超市)|(同村)|(门诊)|(拆车场)', t3.group(1)):
                    pass
                else:
                    item.area = 2
                    item.points.append(t3.group(1))
                    # print("***"+t3.group(1))
                item.route = ''
            if t3.group(2):
                item.route = t3.group(2)
            t3 = re.search(
                r'[去到在经营住前往至从过达回和、]([^去到在状观由经确核今赶住前为、病往至从过进和上住下午返乘]{2,}[园诊信誉楼超市麦当劳区校影美食公司府村店场院馆学社铺苑所厅点地房站虾堡系厂堂寓镇庄街路会诊])(.*)',
                item.route)

    t3 = re.search(r'阴性?', item.route)
    if t3:
        item.state = 1

    t4 = re.search(r'(阳性)|(确诊)', item.route)
    if t4:
        item.state = 2

    if lastitem:
        if lastitem.state == 2:
            item.state = 2

    # t5 = re.search('无症状',item.route)
    # if t5:
    #     item.symptem = '无症状'
    #     item.route = re.sub('无症状','', item.route)

    # print(str(day2wday(item.t))+":"+item.route)


def wday2int(wday):
    if wday == '一':
        return 0
    elif wday == '二':
        return 1
    elif wday == '三':
        return 2
    elif wday == '四':
        return 3
    elif wday == '五':
        return 4
    elif wday == '六':
        return 5
    elif wday == '日':
        return 6
    else:
        return 7


# 南桥寨 第七中学
# open file
# 家0 村1
def openFile():
    fo = open(os.path.dirname(__file__) + "/cases", "r", encoding="utf-8")
    txt = fo.read()
    txt = re.sub(r',', '，', txt)
    txt = re.sub(r'\.', '。', txt)
    txt = re.sub(r'38。7', '38.7', txt)
    txt = re.sub(r'月龄', '个月', txt)
    txt = re.sub(r'田某某，', '', txt)
    txt = re.sub(r'佐', '庄', txt)
    txt = re.sub(r'石家庄市', '石家庄', txt)
    return txt


# parse txt 分析
def getCases(txt):
    m = []
    for i in range(1, 870):
        m1 = re.match(r'(.*)病例' + i.__str__() + '(.*)', txt, re.S)
        txt = m1.group(1)
        m.append(m1.group(2))
    return m


# parse Time
def parseTime(time0, during):
    t = re.match(r'[^0-9]*(([0-9]*)年)?(([0-9]*)月)?(([0-9]*)日)?([0-9]*)?[—至](([0-9]*)年)?(([0-9]*)月)?(([0-9]*)日)(.*)',
                 during)
    if t:
        if t.group(2):
            if len(t.group(2)) >= 1:
                time0['year'] = int(t.group(2))
        if t.group(4):
            if len(t.group(4)) >= 1:
                time0['month'] = int(t.group(4))
                if int(t.group(4)) <= 4:
                    time0['year'] = 2021
        if t.group(6):
            if len(t.group(6)) >= 1:
                time0['day'] = int(t.group(6))
        elif t.group(7):
            if len(t.group(7)) >= 1:
                time0['day'] = int(t.group(7))

        day1 = time2day(res2time(time0))

        if t.group(9):
            if len(t.group(9)) >= 1:
                time0['year'] = int(t.group(9))
        if t.group(11):
            if len(t.group(11)) >= 1:
                time0['month'] = int(t.group(11))
                if int(t.group(11)) <= 4:
                    time0['year'] = 2021
        if t.group(13):
            if len(t.group(13)) >= 1:
                time0['day'] = int(t.group(13))
        elif t.group(15):
            if len(t.group(15)) >= 1:
                time0['day'] = int(t.group(15))
        day2 = time2day(res2time(time0))
        # print(time2)
        return (day1, day2)


def res2time(res):
    s = str(res['year']) + '年' + str(res['month']) + '月' + str(res['day']) + '日'
    t = time.strptime(s, "%Y年%m月%d日")
    return t


# 规定 12月1日 day = 1
def time2day(t):
    t0 = time.mktime(time.strptime("2020年12月1日", "%Y年%m月%d日"))
    d = int((time.mktime(t) - t0) / 86400)
    return d + 1


def day2time(day):
    t0 = time.mktime(time.strptime("2020年12月1日", "%Y年%m月%d日"))
    t1 = t0 + (day - 1) * 86400
    t2 = time.localtime(t1)
    date = time.strftime("%Y年%m月%d日", t2)
    return date


def day2wday(day):
    t0 = time.mktime(time.strptime("2020年12月1日", "%Y年%m月%d日"))  # 初始时间开始的秒数 strptime按格式拆成元组
    t1 = t0 + (day - 1) * 86400  # t1时间的秒数
    t2 = time.localtime(t1)  # 格式化时间戳为本地的时间
    return t2.tm_wday  # tm_wday 周0-6


# 和 、
def parseAndtime(s, day0, items):
    days = []
    time0 = {}
    e = re.compile(r'([^0-9]*)(([0-9]*)年)?(([0-9]*)月)?(([0-9]*)日)')
    r = time.strptime(day2time(day0), "%Y年%m月%d日")
    time0['year'] = r.tm_year
    time0['month'] = r.tm_mon
    time0['day'] = r.tm_mday

    while e.search(s):
        t = e.search(s)
        if t:
            if t.group(3):
                if len(t.group(3)) >= 1:
                    time0['year'] = int(t.group(3))
            if t.group(5):
                if len(t.group(5)) >= 1:
                    time0['month'] = int(t.group(5))
                    if int(t.group(5)) <= 4:
                        time0['year'] = 2021
            if t.group(7):
                if len(t.group(7)) >= 1:
                    time0['day'] = int(t.group(7))
        days.append(time2day(res2time(time0)))
        s = re.sub(e.search(s).group(0), '', s)
    for day in days:
        flag = 0
        for item in items:
            if item.t == day:
                flag = 1
                item.route = item.route + s
                break
        if flag == 0:
            a = Item()
            a.t = day
            a.route = s
            items.append(a)
    if len(days) >= 1:
        return days[len(days) - 1]
    else:
        return day0
    # print(days)
    # print(s)


# parse Case
def parseCase(Case, count):
    temp = {}  # 信息 结构体 Item型的
    add = {}  # 现住址
    native = {}  # 出生地
    relationship = {}
    items = []

    temp['count'] = count
    m1 = re.match(r'(.*?)。(.*)', Case, re.S)  # 分离第一个句号
    s1 = m1.group(1)  # 第一句包含的个人信息
    s2 = m1.group(2)  # 行程信息
    e1 = re.compile(r'.*?([0-9]+。[0-9]*)')  # 无用 e1

    # while e1.match(s2):
    #     print(e1.match(s2).group(1))
    #     s = e1.match(s2).group(1).replace('。', '.')
    #     s2 = s2.replace(e1.match(s2).group(1), s)

    s2 = re.sub('除此之外，', '', s2)  # 删 除此之外
    e = re.compile(r'.*?(，[^，；。]*\d+)[^路.0-9℃]+')  # \d：十进制数

    while e.match(s2):
        s = e.match(s2).group(1).replace('，', '；')
        s2 = s2.replace(e.match(s2).group(1), s)  #

    s2 = re.sub(r'[当该]日', '今日', s2)
    s2 = re.sub('。', '；', s2)
    s2 = re.sub(';', '；', s2)
    s2 = s2.split('；')  # 通过指定分隔符对字符串进行切片，
    # 如果参数 num 有指定值，则分隔 num+1 个子字符串

    # 日期 年月日至年月日
    DateP1 = re.compile(
        r'[^0-9年月日]*((([0-9]*)年)?(([0-9]*)月)?(([0-9]*)日)?([0-9]*)?[—至](([0-9]*)年)?(([0-9]*)月)?(([0-9]*)日))(.*)')
    # DateP1 构成正则表达式格式
    res = {'year': 2020, 'month': 12, 'day': 1, 'hour': 0, 'minute': 0}
    day0 = 1
    for s in s2:  # 每一句切片 进行分析
        d = DateP1.search(s)  # 按照DataP1格式进行匹配
        if d:
            # print(s)
            # print(d.group(1))
            day1, day2 = parseTime(res, d.group(1))
            s = re.sub(d.group(1), '', s)  # 日期提取并删除
            for day in range(day1, day2 + 1):  # 时间范围内循环
                flag = 0
                for item in items:
                    if item.t == day:
                        flag = 1
                        item.route = item.route + s
                        break
                if flag == 0:
                    a = Item()
                    a.t = day
                    a.route = s
                    items.append(a)
            day0 = day2

        else:
            # pass
            d = re.match(r'[^0-9年月日]*((([0-9]*)年)?(([0-9]*)月)?(([0-9]*)日)?[前][^0-9]*([0-9]*)天)(.*)', s)
            if d:
                if d.group(3):
                    if len(d.group(3)) >= 1:
                        res['year'] = int(d.group(3))
                if d.group(5):
                    if len(d.group(5)) >= 1:
                        res['month'] = int(d.group(5))
                        if int(d.group(5)) <= 4:
                            res['year'] = 2021
                if d.group(7):
                    if len(d.group(7)) >= 1:
                        res['day'] = int(d.group(7))
                if d.group(8):
                    if len(d.group(8)) >= 1:
                        gday = int(d.group(8))
                # print(d.group(1))
                s = re.sub(d.group(1), '', s)
                day2 = time2day(res2time(res))
                day0 = day2
                day1 = day2 - gday
                for day in range(day1, day2 + 1):
                    flag = 0
                    for item in items:
                        if item.t == day:
                            flag = 1
                            item.route = item.route + s
                            break
                    if flag == 0:
                        a = Item()
                        a.t = day
                        a.route = s
                        items.append(a)
            else:
                d = re.search(
                    r'[^0-9年月日]*(([0-9]*)年)?(([0-9]*)月)?(([0-9]*)日)([和、](([0-9]*)年)?(([0-9]*)月)?(([0-9]*)日))+', s)
                if d:
                    parseAndtime(s, day0, items)
                    # print(s)
                # print(s)
                else:
                    d = re.search(r'[^0-9年月日]*(([0-9]*)年)?(([0-9]*)月)?(([0-9]+)日)(.*)', s)
                    if d:
                        day0 = parseAndtime(s, day0, items)
                    else:
                        flag = 0
                        for item in items:
                            if item.t == day0:
                                item.route = item.route + s
                                flag = 1
                        if flag == 0:
                            pass
    temp['route'] = items

    # s1 性别，年龄，村人，现住，病例关系
    # match gender
    gender = re.match(r'([男女])，(.*)', s1)
    if gender:
        temp['gender'] = gender.group(1)
        s1 = gender.group(2)
        # print(gender.group(1))
    else:
        temp['gender'] = None
        # print(None)

    # match age
    age = re.match(r'(([0-9]*岁)?([0-9]*个月)?(零[0-9]*天)?)，(.*)', s1)
    if age:
        temp['age'] = age.group(1)
        s1 = age.group(5)
        # print(age.group(1))
    else:
        temp['age'] = None
        # print(s1)

    # s1 村人，现住，病例关系
    s1 = re.sub(r'村民', '人', s1)
    s1 = re.sub(r'现住', '@@@', s1)
    s1 = re.sub(r'现居住', '@@@', s1)
    s1 = re.sub(r'居住', '@@@', s1)
    s1 = re.sub(r'住', '@@@', s1)
    s1 = re.sub(r'\n', '', s1)

    # match native
    n = re.match(r'([^@病，]*)?，?(.*)', s1)
    # s1 区 镇 村 人
    s1 = n.group(1)
    if s1:
        # n1 = re.match(r'(石家庄)?(.*市)?(.*县)?(.*区)?(.*镇)?(.*村)?(.*庄)?人', s1)
        n1 = re.match(
            r'(石家庄)?([^县区镇村]*?市)?(.*?县)?(正定)?([^小]*?区)?([^乡]*?镇)?(.*?乡)?(.*街道)?(.*路)?(吴村铺村)?(.*?村)?([^石家]*?庄)?([^人居民学生职工]*)?(.*)',
            s1)
        # 市
        if n1.group(1):
            native['市'] = n1.group(1) + '市'
        if n1.group(2):
            native['市'] = n1.group(2)
        # 县/区
        if n1.group(3):
            native['县/区'] = n1.group(3)
        if n1.group(4):
            native['县/区'] = n1.group(4) + '县'
        if n1.group(5):
            native['县/区'] = n1.group(5)
        # 镇
        if n1.group(6):
            native['镇/乡'] = n1.group(6)
        if n1.group(7):
            native['镇/乡'] = n1.group(7)
        # 街道
        if n1.group(8):
            native['街道/路'] = n1.group(8)
        if n1.group(9):
            native['街道/路'] = n1.group(9)
        # 村/庄
        if n1.group(10):
            native['村/庄'] = n1.group(10)
        if n1.group(11):
            native['村/庄'] = n1.group(11)
        if n1.group(12):
            native['村/庄'] = n1.group(12)
        # 详细
        if n1.group(13):
            if len(n1.group(13)) <= 1:
                native['详细'] = n1.group(13)

    # match add
    # s1 现住址 关系
    if n.group(2):
        s1 = n.group(2)
        s1 = re.sub(r'[于在]', '', s1)
        n2 = re.match(r'@@@([^，]*)，?(.*)', s1)
        if n2:
            n3 = re.match(
                r'(石家庄)?([^县区镇村]*?市)?(.*?县)?(正定)?([^小]*?区)?([^乡]*?镇)?(.*?乡)?(.*街道)?(.*大道)?(.*大街)?(.*路)?(吴村铺村)?(.*?村)?([^石家]*?庄)?(.*)',
                n2.group(1))
            # 市
            if n3.group(1):
                add['市'] = n3.group(1) + '市'
            if n3.group(2):
                add['市'] = n3.group(2)
            # 县/区
            if n3.group(3):
                add['县/区'] = n3.group(3)
            if n3.group(4):
                add['县/区'] = n3.group(4) + '县'
            if n3.group(5):
                add['县/区'] = n3.group(5)
            # 镇
            if n3.group(6):
                add['镇/乡'] = n3.group(6)
            if n3.group(7):
                add['镇/乡'] = n3.group(7)
            # 街道
            if n3.group(8):
                add['街道/路'] = n3.group(8)
            if n3.group(9):
                add['街道/路'] = n3.group(9)
            if n3.group(10):
                add['街道/路'] = n3.group(10)
            if n3.group(11):
                add['街道/路'] = n3.group(11)
            # 村/庄
            if n3.group(12):
                add['村/庄'] = n3.group(12)
            if n3.group(13):
                add['村/庄'] = n3.group(13)
            if n3.group(14):
                add['村/庄'] = n3.group(14)
            if n3.group(15):
                add['详细'] = n3.group(15)
        else:
            # print(s1)
            n4 = re.match(r'.*?(([0-9]*)月([0-9]*)[日号]).*?([0-9]*)[号例].*', s1)
            if n4:
                # print(n4.group(1)+":"+ n4.group(4))
                date = re.sub('号', '日', n4.group(1))
                t = time.strptime("2021年" + date, r'%Y年%m月%d日')
                relationship['time'] = t
                num1 = int(n4.group(2))
                relationship = num1
            else:
                n5 = re.match(r'.*今日.*第([0-9]*)号.*', s1)
                if n5:
                    relationship['time'] = '今日'
                    relationship['num1'] = int(n5.group(1))
                    # print(s1)
                else:
                    n6 = re.match(r'[^0-9]*([0-9]+).*', s1)
                    if n6:
                        relationship['count'] = int(n6.group(1))
                        # print(n6.group(1))
                    # else:
                    # print(s1)

    temp['add'] = add
    temp['native'] = native
    temp['relationship'] = relationship
    temp['route'] = items
    return temp


def getresult(Cases):
    result = []
    resultOne = []
    for case in Cases:
        if case['gender']:
            resultOne.append(case['gender'])
        else:
            resultOne.append('NoGender')

        if case['age']:
            resultOne.append(case['age'])
        else:
            resultOne.append('NoGender')
        n = ''
        if case['add']:
            if '市' in case['add'].keys():
                n = n + case['add']['市']
            if '县/区' in case['add'].keys():
                n = n + case['add']['县/区']
            if '镇/乡' in case['add'].keys():
                n = n + case['add']['镇/乡']
            if '街道/路' in case['add'].keys():
                n = n + case['add']['街道/路']
            if '村/庄' in case['add'].keys():
                n = n + case['add']['村/庄']
            if '详细' in case['add'].keys():
                n = n + case['add']['详细']

        elif case['native']:
            if '市' in case['native'].keys():
                n = n + case['native']['市']
            if '县/区' in case['native'].keys():
                n = n + case['native']['县/区']
            if '镇/乡' in case['native'].keys():
                n = n + case['native']['镇/乡']
            if '街道/路' in case['native'].keys():
                n = n + case['native']['街道/路']
            if '村/庄' in case['native'].keys():
                n = n + case['native']['村/庄']

        else:
            n = ["No address"]
        resultOne.append(n)
        r0 = []
        for route in case['route']:
            r = []
            r.append(case['count'])
            r.append(route.t)
            r.append(route.state)
            r.append(route.area)
            r.append(route.points)
            # print(r)
            r0.append(r)
        # print(r0)
        resultOne.append(r0)
        # print(resultOne)
        result.append(resultOne)
        resultOne = []
    return result


# def getLocation(addr):
#     headers = {
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36'}
#     url = 'http://api.map.baidu.com/geocoder/v2/?output=json&ak=1XjLLEhZhQNUzd93EjU5nOGQ&address=' + "河北省石家庄市" + addr
#     print(url)
#     r = requests.get(url, headers=headers)
#     if r.status_code != 200:
#         print(r.status_code)
#         print('get location failed')
#         return ""
#     return str(json.loads(r.text).get('result').get('location'))

def getUrl(*address):
    '''
调⽤地图API获取待查询地址专属url
最⾼查询次数30w/天，最⼤并发量160/秒
    '''
    ak = 'rx0CAKzmGnslr0zZhP1w2BAwNg3ScSx4'
    if len(address) < 1:
        return None
    else:
        for add in address:
            add = "河北省石家庄市" + add
            url = 'http://api.map.baidu.com/geocoding/v3/?address={inputAddress}&output=json&ak={myAk}'.format(inputAddress=add,myAk=ak)
            yield url

def getPosition(url):
    '''返回经纬度信息'''
    res = requests.get(url)
    json_data = json.loads(res.text)
    if json_data['status'] == 0:
        lat = json_data['result']['location']['lat'] #纬度
        lng = json_data['result']['location']['lng'] #经度
    else:
        lat = -1
        lng = -1
        print("Error output!")
    return lat, lng


import matplotlib.pyplot as plt

if __name__ == "__main__":
    Cases = []
    txt = openFile()
    m = getCases(txt)  # 读文件，读到 m
    count = 1  # 计数
    for case in m[0:]:  # 从m[0]开始循环 直到列表最后
        case = case.replace("\n", "")  # 删除换行
        temp = parseCase(case, count)  # 读取文件 依次存到temp
        Cases.append(temp)  # 将提取信息后的temp 依次连接到cases后
        count += 1
    lastitem = None  # 保存item实时数据
    for case in Cases:  # 循环 整理后的数据
        lastitem = None
        for item in case['route']:  # 分析路径 并存到route
            if lastitem:
                parseRoute(item, lastitem)
            else:
                parseRoute(item, None)
            lastitem = item
    result = getresult(Cases)  # 获得文档整理结果 严谨格式化
    # print(result[868])  # ？？？？

    locMap = []
    sta = []  # 每日新增
    stb = []  # 累计确诊
    stc = []  # 每日外出活跃程度
    loc = {}
    sunday = {}
    binglihao = [[], []]
    for i in range(65):
        stc.append(0)

    for c in result:
        tl = []
        if c[3] and c[3][0]:
            pass
        else:
            continue
        tl.append(c[3][0][0])
        for d in c[3]:
            if d[3] == 2 and d[1] >= 0 and d[1] < 65:
                stc[d[1]] += 1
            if d[2] == 2:
                if d[1] == 1:
                    binglihao[0].append(d[0])
                if d[1] == 20:
                    binglihao[1].append(d[0])
                sunday[d[0]] = d[1]
                tl.append(d[1])
                break
        if tl and len(tl) == 2:
            locMap.append(tl)

    for c in result:
        if c[3] and c[3][0]:
            pass
        else:
            continue
        for d in c[3]:
            if d[2] == 2:
                break
            if d[3] == 2 and d[1] >= 0 and d[1] < 65 and d[0] in sunday and sunday[d[0]] - d[1] <= 14:
                for i in d[4]:
                    if i in loc:
                        loc[i] += 1
                    else:
                        loc[i] = 1
    loctemp = {}
    # locMap2 = []
    # for i in loc:
    #     if not re.search(r'[医院诊科]', i):
    #         loctemp[i] = loc[i]
    #         t = getLocation(i)
    #         if t != "":
    #             locMap2.append([t, loc[i]])
    #         time.sleep(0.1)
    # newMap = {}
    #
    # for i in locMap2:
    #     if i[0] in newMap:
    #         newMap[i[0]] += i[1]
    #     else:
    #         newMap[i[0]] = i[1]

    locMap.sort(key=lambda x: x[-1])
    for i in range(65):
        sta.append(0)
        stb.append(0)
    for i in locMap:
        if i[-1] >= 0 and i[-1] < 65:
            sta[i[-1]] += 1
    for i in range(len(sta)):
        if i == 0:
            stb[i] = sta[i]
        else:
            stb[i] = stb[i - 1] + sta[i]

    plt.plot(sta, color='red', label='Infected')
    plt.plot(stb, color='blue', label='Cumulation')
    plt.plot(stc, color='yellow', label='Out')
    plt.xlabel('Day')
    plt.ylabel('Number')
    plt.title('Statistical chart of epidemic data')
    plt.legend()
    plt.show()

    Locmap = []
    for c in result:
        if c[3] and c[3][0]:
            pass
        else:
            continue
        for d in c[3]:
            if d[3] < 2:
                Locmap.append(c[2])
            else:
                for l in d[4]:
                    Locmap.append(l)
    # print(Locmap)
    # locMap = ['上海市嘉定区科贸路8号', '苏州市虎丘区青花路9号', '沈阳辉⼭农业⾼新技术开发区宏业街73号', '⼴东省佛⼭市魁奇⼀路9号', '四川省成都市锦江区中纱帽街8号']

    file = open('C:\\Users\\86187\\Desktop\\exp\\data.txt', mode='w', encoding='UTF-8')
    txt = ""
    # Locmap = ['超市', '苏州市虎丘区青花路9号', '沈阳辉⼭农业⾼新技术开发区宏业街73号', '⼴东省佛⼭市魁奇⼀路9号', '四川省成都市锦江区中纱帽街8号']
    Locmap = list(set(Locmap))
    print(Locmap)

    Len = len(Locmap)
    # print(Len)

    for i in range(Len):
        add = Locmap[i]
        add_url = list(getUrl(add))[0]
        print(add_url)
        lat, lng = getPosition(add_url)
        print("河北省石家庄市：{0}|经度:{1}|纬度:{2}.".format(add, lng, lat))
        if lat == -1 and lng == -1:
            continue
        else:
            txt += str(lat) + ',' + str(lng) + ';\n'

    file.write('{' + txt[:-2] + '}')
    file.close()

    # for c in result:
    #     if c[3] and c[3][0]:
    #         pass
    #     else:
    #         continue
    #     for d in c[3]:
    #         if d[3] < 2:
    #             locMap.append(c[2])
    #         else:
    #             for l in d[4]:
    #                 locMap.append(l)
    # # locMap = list(set(locMap))
    #
    # tl = []
