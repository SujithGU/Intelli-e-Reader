from selenium import webdriver
from selenium.webdriver.support.ui import Select
import csv

'''
Scrape the English profile site
'''
url = 'https://www.englishprofile.org/wordlists/evp'

driver = webdriver.Chrome(executable_path='C:\\Users\Suji\\Downloads\\chromedriver_win32\\chromedriver.exe')
page = driver.get(url)
drp = Select(driver.find_element_by_id("limit"))
drp.select_by_visible_text("All")

st1 = '//*[@id="reportList"]/tbody/tr['
st2 = ']'

data = {}

file = open('../data_files/english_profile_scrape.csv', 'w', newline='')

writer = csv.writer(file)
writer.writerow(['word','pos','cefr'])

length = driver.find_element_by_xpath('//*[@id="filter-bar"]/div[1]')
num = str(length.text).split(" ")[5]
print(num)
for val in range(1,int(num)+1):
    st = st1+str(val)+st2
    text = st+"/td[1]"
    cef = st+"/td[3]"
    pos = st+"/td[4]"
    tex = driver.find_element_by_xpath(text)
    po = driver.find_element_by_xpath(pos)
    cfr = driver.find_element_by_xpath(cef)
    writer.writerow([str(tex.text).strip(),str(po.text).strip(),str(cfr.text).strip()])
    print(tex.text)

file.close()
