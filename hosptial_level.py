from tkinter import X
from playwright.async_api import async_playwright, TimeoutError
import asyncio
import time
from lxml import etree
import pandas as pd
import os 
import re
from bs4 import BeautifulSoup


def hospital_level_judge(answer):
    if "三级甲等" in answer or "三甲" in answer:
        return "三级甲等"
    if "三级乙等"  in answer or "三乙" in answer:
        return "三级乙等"
    if "二级甲等"  in answer or "二甲" in answer:
        return "二级甲等"
    if "二级乙等"  in answer or "二乙" in answer:
        return "二级乙等"
    if "三级"  in answer:
        return "三级"
    if "二级" in answer:
        return "二级"
    if "一级" in answer:
        return "一级"
    return 'None'

def html_to_string(element):
    element_string = etree.tostring(element, encoding='unicode')
    final_string = BeautifulSoup(element_string, "html.parser")
    final_string = final_string.get_text()

    return final_string

async def baidu_search(keyword):
    async with async_playwright() as p:
            browser = await p.chromium.launch(headless = False,slow_mo=1000)
            
            ##创建独立环境
            context = await browser.new_context()
            page = await context.new_page()

            
            await page.add_init_script(
                """
                    Object.defineProperties(navigator, {
                        webdriver:{
                            get:()=>undefined
                        }
                    });
                """
            )
            await page.goto("https://www.baidu.com/",wait_until="domcontentloaded")

            fill_box= '//*[@id="kw"]'
            await page.fill(fill_box,keyword)
            element = await page.wait_for_selector('//*[@id="su"]', state='visible') 
            if element.is_visible():
                await element.click()
            else:
                 return None
            
            await page.wait_for_load_state(state='domcontentloaded')
            time.sleep(2)
       
            html = await page.content()
            content = etree.HTML(html)
            full_info_list = []
            for id in range(1,12):
                element = content.xpath(f'//*[@id="{id}"]')
                for x in element:
                    title = x.xpath('./div/div[1]/h3/a')
                    for x_1 in title:
                        title = html_to_string(x_1)
                    info = x.xpath('.//span[@class="content-right_8Zs40"]')
                    new_info=''
                    for y in info:
                        string_info = html_to_string(y)
                        new_info = new_info+string_info
                    full_info_list.append([title,new_info])
            return full_info_list

async def google_search(keyword):
    async with async_playwright() as p:
            browser = await p.firefox.launch(headless = False,slow_mo=1000)
            
            
            context = await browser.new_context()
            page = await context.new_page()

            
            
            await page.add_init_script(
                """
                    Object.defineProperties(navigator, {
                        webdriver:{
                            get:()=>undefined
                        }
                    });
                """
            )
            await page.goto("https://www.google.com/",wait_until="domcontentloaded")

            fill_box= '//*[@id="APjFqb"]'
            await page.fill(fill_box,keyword)
            await page.press(fill_box,'Enter')

            await page.wait_for_load_state(state='domcontentloaded')
            time.sleep(2)
            
            html = await page.content()
            content = etree.HTML(html)
            elements = content.xpath('//div[@class="MjjYud"]')
            full_info_list = []
            for element in elements:
                title = element.xpath('.//a/h3/text()')
                title = ' '.join(title)
                info = element.xpath('./div/div/div[2]/div/span')
                new_info=''
                for y in info:
                    element_string = etree.tostring(y, encoding='unicode')
                    final_string = BeautifulSoup(element_string, "html.parser")
                    final_string = final_string.get_text()
                    new_info = new_info+final_string
                full_info_list.append([title,new_info])
            return full_info_list
    

def main():
    os.chdir("D:\\Machine learning\\research assistant\\hospital work 2\\hospital_check_second\\hospital_check_second")
    df = pd.read_csv('hospital_data.csv',encoding='gbk')
    save_df = pd.read_csv('hospital_search.csv')
    name_list = df['hospital'].tolist()
    for element in name_list[5379:]:
        retries = 0
        max_retries = 5
        while retries <= max_retries:
            try:
                google_info_list = asyncio.run(google_search(element))
                google_answer_list = []
                for x in google_info_list:
                    if element in x[0] or element in x[1]:
                        google_answer_list.append(x[1])
                google_answer = '//'.join(google_answer_list)
                google_final_answer = hospital_level_judge(google_answer)

                baidu_info_list = asyncio.run(baidu_search(element))
                baidu_answer_list = []
                for x in baidu_info_list:
                    if element in x[0] or element in x[1]:
                        baidu_answer_list.append(x[1])
                baidu_answer = '//'.join(baidu_answer_list)
                baidu_final_answer = hospital_level_judge(baidu_answer)
                new_data = [element, google_final_answer, google_answer,baidu_final_answer,baidu_answer]
                save_df.loc[len(save_df.index)] = new_data
                print({"hospital":element,"google_hospital_level":google_final_answer,"google_hospital_info":google_answer,"baidu_hospital_level":baidu_final_answer,"baidu_hospital_info":baidu_answer})
                break

            except TimeoutError:
                retries += 1
                print('retries')
            except Exception as e:
                print(f"Error:{e}")
                break
        
        time.sleep(2)
        save_df.to_csv('hospital_search.csv', index=False,encoding="utf-8")

main()