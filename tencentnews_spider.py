#! /usr/local/python3/bin/python3
#coding=utf-8

'''
抓取腾讯新闻，要闻分类的基本内容存储到数据库中 (只能获取99页数据，可用crontab定时执行）
数据库版本：MongoDB shell version v3.4.16
爬虫线路： requests - bs4
Python版本： 3.6
OS： ubuntu 16.04
'''

import sys, os, threading, multiprocessing
import requests, json, pymongo
import time, re, random
import useragent_pool, ip_pool

class Spider():
    def __init__(self, url):
        self.url = url

    #请求网页信息，返回json数据
    def get_html_json(self, url, page):
        try:
            header = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:55.0) Gecko/20100101 Firefox/55.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3",
                "Accept-Encoding": "gzip, deflate",
                "Referer": "https://news.sina.com.cn/society/",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }
            header['User-Agent'] = random.choice(useragent_pool.user_agents)
            proxy = random.choice(ip_pool.ip_pool)
            param = {"page": page}
            r = requests.get(url = url, proxies = proxy, headers = header, params = param, timeout=20)
            r.raise_for_status()
            r.encoding = 'utf-8'
            return r.json()
        except:
            raise BaseException

    #保存数据到mongodb中
    def insert_to_db(self, start_no, end_no):
        myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        mydb = myclient["spider"]
        mycol = mydb["tencentnews"]
        for i in range(start_no, end_no):
            try:
                html = self.get_html_json(self.url, i)
                datas = html["data"]
                for data in datas:
                    data['myinserttime'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    try:
                        mycol.insert_one(data)
                    except:
                        pass
                print("page%d insert seccessful." % i)
            except:
                print("page%d insert failed. ------------------stress--------------------" % i)
                pass

    #多进程执行
    def multi_process_execute(self, start, end):
        offset = (end - start) // 4
        single_num = offset // 5
        p = multiprocessing.Pool()
        for i in range(4):
            p.apply_async(self.multi_threading_execute, args=(start, offset*i, single_num,))
        p.close()
        p.join()
        print('All processes done.')
        print('Successful.')

    #多线程执行
    def multi_threading_execute(self, start, offset, single_num):
        threads = [threading.Thread(target=self.insert_to_db, args=(start+offset+x*single_num, start+offset+(x+1)*single_num)) for x in range(5)]
        for i in range(5):
            threads[i].start()
        for i in range(5):
            threads[i].join()

base_url = 'https://pacaio.match.qq.com/irs/rcd?cid=108&token=349ee24cdf9327a050ddad8c166bd3e3'

if __name__ == '__main__':
    print("**********execute time: " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "**********")
    time_start = time.time()
    s = Spider(base_url)
#    html = s.get_html_json(base_url, 1)
#    html = s.unicode_transform(html)
#    print(html)
#    print(html["result"]["data"])
#    s.insert_to_db(1, 21) #单线程
    #s.multi_process_execute(1, 1801)
    s.multi_process_execute(1, 101)
    time_end = time.time()
    print("time consuming: %.2fs." %(time_end-time_start))
    print("***************end-line***************")
