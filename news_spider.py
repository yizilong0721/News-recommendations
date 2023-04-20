import time
import requests
from bs4 import BeautifulSoup
from app.models import News
from app import db
import pymysql


def get_spider_sina_info(i):
    '''爬取新浪新闻'''

    #  这个URL是新浪新闻客户端中“天翼”栏目的API接口，用于获取该栏目下的新闻内容。其中，V4表示版本号为4。
    url = "https://feeds.sina.cn/api/v4/tianyi"
    if i == 0:
        '''
        action：请求的类型，0 表示第一页，1 表示后续页。
        up：上一页最后一条新闻的 ID。
        down：下一页第一条新闻的 ID。
        length：每页返回的新闻数量。20
        cre：请求的来源。
        mod：请求的模块。
        statics：是否返回统计信息。
        merge：是否合并数据。
        language：请求的语言。
        cnt：请求的内容。
        ad：广告相关参数。
        cateid：新闻分类 ID。
        zhiding：是否只返回置顶新闻。
        tm：请求的时间戳。
        filters：需要过滤掉的字段。
        '''
        querystring = {"action": "0", "up": "0", "down": "0", "length": "20", "cre": "tianyi", "mod": "wnews",
                       "statics": "1", "merge": "3", "language": "zh-CN",
                       "cnt": "{\"caller\":\"crmjs\",\"traceid\":\"crmjs_1670607629980\"}",
                       "ad": "{\"rotate_count\":172,\"page_url\":\"https://news.sina.cn/?from=wap\",\"platform\":\"wap\",\"v\":\"*\",\"timestamp\":1670607629980,\"net\":null,\"channel\":\"131250\"}",
                       "cateid": "1o", "zhiding": "1", "tm": "1489716199",
                       "filters": "url,wapurl,thumbs,thumbscount,title,intro,style,media,type,videos,picscount,dataid,showtags,commentcount"}
    else:
        querystring = {"action": "1", "up": f"{i}", "down": "0", "length": "20", "cre": "tianyi", "mod": "wnews",
                       "statics": "1",
                       "merge": "3", "language": "zh-CN",
                       "cnt": "{\"caller\":\"crmjs\",\"traceid\":\"crmjs_1670607629980\"}",
                       "ad": "{\"rotate_count\":172,\"page_url\":\"https://news.sina.cn/?from=wap\",\"platform\":\"wap\",\"v\":\"*\",\"timestamp\":1670607629980,\"net\":null,\"channel\":\"131250\"}",
                       "cateid": "1o", "zhiding": "1", "tm": "1489716199",
                       "filters": "url,wapurl,thumbs,thumbscount,title,intro,style,media,type,videos,picscount,dataid,showtags,commentcount"}
    payload = ""
    headers = {
        "cookie": "ustat=__111.31.102.210_1670607615_0.01222900; genTime=1670607615; Apache=697876743388.3615.1670607616451; SINAGLOBAL=697876743388.3615.1670607616451; ULV=1670607616455%3A1%3A1%3A1%3A697876743388.3615.1670607616451%3A; historyRecord=%7B%22href%22%3A%22https%3A%2F%2Fnews.sina.cn%2F%22%2C%22refer%22%3A%22%22%7D; recent_visited=%255B%257B%2522t%2522%253A1670607616457%252C%2522u%2522%253A%2522https%253A%2F%2Fnews.sina.cn%2F%2522%257D%255D; vt=4",
        "Host": "feeds.sina.cn",
        "Connection": "keep-alive",
        "Content-Length": "0",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1",
        "Content-Language": "",
        "Origin": "https://news.sina.cn",
        "Referer": "https://news.sina.cn/?from=wap",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9"
    }

    response = requests.request("POST", url, data=payload, headers=headers, params=querystring,verify=False)
    # 从response对象中获取一个JSON格式的数据，然后从中取出键名为'result'的字典，再从'result'字典中取出键名为'data'的值，最后将其赋值给变量ret。
    ret = response.json()['result']['data']
    result = []
    for r in ret:
        try:
            info = r['info']
            title = info['title']
            url = r['base']['base']['url']
            media = info['mediaInfo']['name']
            # 从一个字典对象info中获取点赞数count。如果info字典中的'interactionInfo'键对应的字典中没有'likeInfo'键或者'likeInfo'键对应的字典中没有'count'键，
            # 则将count赋值为0；否则，将'likeInfo'键对应的字典中的'count'键对应的值赋值给count。
            count = 0 if 'count' not in info['interactionInfo']['likeInfo'] else info['interactionInfo']['likeInfo'][
                'count']
            show_time = info['showTime']   #时间戳
            # 时间戳转化为时间字符串  time.strftime()函数用于将时间元组转换为指定格式的时间字符串
            t = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(show_time)))
            sub_response = requests.get(url)
            # 使用Python的BeautifulSoup库，将sub_response对象中获取到的HTML文档解析成一个BeautifulSoup对象。
            # html.parser是Python内置的HTML解析器进行解析，这是BeautifulSoup库的默认解析器。
            sub_soup = BeautifulSoup(sub_response.text, 'html.parser')
            #  从BeautifulSoup对象sub_soup中，查找class属性为'art_pic_card'的section元素，并获取该元素的文本内容。
            content = sub_soup.find('section', class_='art_pic_card').text    #  .encode('utf-8')
            # if title.find('习近平') > 0:
            #     continue
            news_tag = ['资讯', '法治', '日报', '环球', '晚报', '财经', '人民', '娱乐', '青年', '健康']
            for i, category in enumerate(news_tag,start=1):
                if category in media:
                    tag_id=i
                    break
                tag_id = 11

            print([title, url, media, count, t, content,tag_id])
            result.append((title, url, media, count, t, content,tag_id))
            # time.sleep(1)
        # 如果在try语句块中发生了异常，则执行except语句块中的代码，直接跳过当前循环，继续下一次循环。
        except Exception as e:
            pass
    return result


def spider_sina():
    results = []
    for i in range(30):  # i代表指定爬取的页数
        ret = get_spider_sina_info(i)
        results.extend(ret)
    return results


if __name__ == '__main__':
    # connect = pymysql.Connect(
    #     host='localhost',
    #     port=3306,
    #     user='root',
    #     passwd='123456',
    #     db='news_db',
    #     charset='utf8'
    # )
    # cursor = connect.cursor()
    #
    # basesql = "INSERT INTO news(title,link,media,commentnum,addtime,info) VALUES ( '%s',%s,'%s', '%s', '%s','%s')"

    for i in range(10000):
        datalist = []
        data = spider_sina()
        datalist.extend(data)

        # cursor.executemany(basesql, datalist)
        # connect.commit()
        # print(datalist)
        objs = []
        for dd in datalist:
            if len(dd) > 5:
                news = News(
                    title=dd[0],
                    link=dd[1],
                    media=dd[2],
                    commentnum=dd[3],
                    addtime=dd[4],
                    info=dd[5],
                    tag_id=dd[6],
                    logo="123456.jpg"
                )
                objs.append(news)

        if (len(objs) > 0):
            db.session.bulk_save_objects(objs)
            db.session.commit()
