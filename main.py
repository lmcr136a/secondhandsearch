from flask import Flask, request
import requests
import pandas as pd
import json
import asyncio
import pyppeteer
from bs4 import BeautifulSoup
from requests_html import HTMLSession, AsyncHTMLSession


# def get_bs(url):
#     session = HTMLSession()
#     resp = session.get(url)
#     resp.html.render(sleep = 1)
#     return resp

async def get_bs(url):
    session = AsyncHTMLSession()
    browser = await pyppeteer.launch({
        'ignoreHTTPSErrors': True,
        'headless': True,
        'handleSIGINT': False,
        'handleSIGTERM': False,
        'handleSIGHUP': False
    })
    session._browser = browser

    resp = await session.get(url)
    await resp.html.arender()
    await session.close()
    return resp


def get_shs(cls_names, url):
    resp = asyncio.run(get_bs(url))
    bs = BeautifulSoup(resp.html.raw_html, 'html.parser')
    
    df = pd.DataFrame(columns=CLS_NAME)
    for i, cls in enumerate(cls_names[:2]):
        df[CLS_NAME[i]] = list(map(lambda x: x.get_text(), bs.find_all(*cls)[:NUM_FROM_A_SITE]))
    df[CLS_NAME[2]] = list(map(lambda x: x['src'], bs.find_all('img', alt=cls_names[2])[:NUM_FROM_A_SITE]))
    df[CLS_NAME[3]] = url
    return df


def get_new_from_naver(cls_names, url):
    resp = asyncio.run(get_bs(url))
    bs = BeautifulSoup(resp.html.raw_html, 'html.parser')

    df = pd.DataFrame(columns=CLS_NAME)
    for i, cls in enumerate(cls_names[:2]):
        df[CLS_NAME[i]] = list(map(lambda x: x.get_text(), bs.find_all(*cls)[:NUM_FROM_A_SITE]))

    imgs = list(map(lambda x: x['src'], bs.find_all('a',alt=df[CLS_NAME[0]])))
    if len(imgs) > NUM_FROM_A_SITE:
        df[CLS_NAME[2]] = imgs[:NUM_FROM_A_SITE]
    df[CLS_NAME[3]] = url
    return df


def get_new_from_coupang(cls_names, url):
    page = requests.get(url)
    bs = BeautifulSoup(page.text, 'html.parser')
    df = pd.DataFrame(columns=CLS_NAME)
    for i, cls in enumerate(cls_names[:2]):
        df[CLS_NAME[i]] = list(map(lambda x: x.get_text(), bs.find_all(*cls)[:NUM_FROM_A_SITE]))

    df[CLS_NAME[2]] = list(map(lambda x: x['src'], bs.find_all(*cls_names[2])[:NUM_FROM_A_SITE]))
    df[CLS_NAME[3]] = url
    return df


def string_price_to_num(str_price):
    str_price = str_price.strip().strip("원").split(",")
    s = ''
    for string in str_price:
        s += string
    return int(s)


def alysis_dfs(df1, df2):
    df = pd.concat([df1, df2], axis=0)
    df = df.fillna('')

    df['price'] = list(map(string_price_to_num, df['price']))  # 가격 숫자로
    df = df.sort_values('price')[:TOTAL_NUM].reset_index()  # 가격 정렬
    items = []
    for sh in list(df.iterrows()):
        items.append({
            'title': sh[1]['title'],
            'price': sh[1]['price'],
            'image': sh[1]['image'],
            'link': sh[1]['link']
        })
    return items



TOTAL_NUM = 10
NUM_FROM_A_SITE = 20

CLS_NAME = ['title', 'price', 'image', 'link']
CLS_SH1 = [['div', 'sc-fcdeBU iVCsji'], ['div', 'sc-gmeYpB iBMbn'], '상품 이미지']
CLS_SH2 = [['span', 'ProductItemV2_title__1KDby'], ['p', 'ProductItemV2_price__1a5yb mt3'], '이미지']
CLS_NEW1 = [['div', 'basicList_title__3P9Q7'], ['span', 'price_num__2WUXn']]
CLS_NEW2 = [['div', 'name'], ['strong', 'price-value'], ['img', 'search-product-wrap-img']]


app = Flask(__name__)

@app.route('/sample/<keyword>')
def main(keyword):
    url_sh1 = f'https://m.bunjang.co.kr/search/products?q={keyword}'  # 번개장터
    url_sh2 = f'https://m.joongna.com/search-list/product?searchword={keyword}'  # 중고나라
    url_new1 = f'https://search.shopping.naver.com/search/all?query={keyword}'  # 네이버쇼핑
    url_new2 = f'https://www.coupang.com/np/search?component=&q={keyword}'  # 쿠팡

    ## 번개장터
    sh_df = get_shs(CLS_SH1, url_sh1)

    ## 중고나라
    sh_df_ = get_shs(CLS_SH2, url_sh2)
    sh_items = alysis_dfs(sh_df, sh_df_)

    ## 네이버쇼핑
    new_df = get_new_from_naver(CLS_NEW1, url_new1)

    ## 쿠팡
    new_df_ = get_new_from_coupang(CLS_NEW2, url_new2)
    new_items = alysis_dfs(new_df, new_df_)

    res = json.dumps({
        "new":new_items,
        "sh":sh_items
        })
    return res

@app.route('/')
def home():
    return 'Hello, world'

if __name__ == "__main__":
    app.run()
