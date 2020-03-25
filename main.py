import requests, json,sys,os
from bs4 import BeautifulSoup
from unidecode import unidecode
from datetime import datetime
import config, signal

def signal_handler(sig, frame):
    generate_html()
    sys.exit(0)

def generate_html():
	result = "<html dir='rtl'><head><title>Digikala Promotions</title><meta name='language' content='farsi'/><meta charset='utf-8'/><head>"
	result += "<body><style>img {width: 150px;height:auto} body * { font-size: 18px }</style>"
	result += "<table>"
	f = open(os.path.dirname(__file__) + '/output/index.html', "w+")
	f.write(result)
	lists = os.listdir(os.path.dirname(__file__) + '/output')
	lists = lists[::-1]
	for file in lists:
	    ff = open(os.path.dirname(__file__) + '/output/' + file, "r")
	    f.write(ff.read())
	    # os.remove(os.path.dirname(__file__) + '/output/' + file)
	result = "</table></body></html>"
	f.write(result)
	f.close()

def get_last_page():
	target_url = config.target_url + 'pageno=1'
	page = requests.get(target_url)
	soup = BeautifulSoup(page.content,"html.parser")
	page_link = soup.find("a",{"class":"c-pager__next"})
	return int(page_link['data-page'])

def get_page(page_num=1):
	target_url = config.target_url + 'pageno={page_num}'.format(page_num=page_num)
	print target_url
	page = requests.get(target_url)
	soup = BeautifulSoup(page.content,"html.parser")
	items = soup.find_all("div",{"class":"c-product-box"})
	return items

def parse_page(items):
	for item in items:
		try:
			attr = json.loads(item['data-enhanced-ecommerce'])
			info_div = item.find("div", {"class":"c-price__value"})
			dkid = attr['id']
			dkname = attr['name']
			dkcat = attr['category']
			dkprice = int(attr['price'])/10
			dkimage = item.find("img")
			dkdiscount = int(unidecode(item.find("div", {"class":"c-price__discount-oval"}).text.strip()).replace("%",""))
			dkorgprice = int(unidecode(info_div.find("del").text.replace(",","").strip()))
			if dkdiscount >= config.discount and dkprice <= config.max_price and dkcat not in config.exclude_category:
				result = "<tr>"
				result += "<td><a href='{dkimageurl}'>{dkimage}</a></td>".format(dkimage=dkimage,dkimageurl=dkimage["src"])
				result += "<td>"
				result += "{dkname}".format(dkname=dkname)
				result += "<br/>"
				result += "Price: {dkorgprice} => {dkprice}".format(dkorgprice=dkorgprice, dkprice=dkprice)
				result += "<br/>"
				result += "Discount: {dkdiscount}%".format(dkdiscount=dkdiscount)
				result += "<br/>"
				result += "URL: <a href='https://www.digikala.com/product/dkp-{dkid}'>https://www.digikala.com/product/dkp-{dkid}</a>".format(dkid=dkid)
				result += "<br/>"
				result += "</td>"
				result += "</tr>"
				f = open(os.path.dirname(__file__) + '/output/'+str(dkdiscount)+'.txt', "a+")
				f.write(result)
				f.close()
		except Exception as e:
			# print "dkid: {dkid} has problem".format(dkid=dkid)
			exc_type, exc_obj, exc_tb = sys.exc_info()
			fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
			print str(e)
			print(exc_type, fname, exc_tb.tb_lineno)
			continue
def main():
	page_count = range(1,get_last_page()+1)
	for i in page_count:
		items = get_page(i)
		parse_page(items)
	generate_html()

def remove_old(dir_name):
	test = os.listdir(dir_name)
	for item in test:
	    if item.endswith(".txt") or item.endswith(".html"):
	        os.remove(os.path.join(dir_name, item))

signal.signal(signal.SIGINT, signal_handler)
if __name__ == '__main__':
	reload(sys)
	sys.setdefaultencoding('utf8')
	remove_old(os.path.dirname(__file__) +'/output')
	# remove_old('by-cat')
	now = datetime.now()
	dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
	print "started at {d1}".format(d1=dt_string)
	main()
	now = datetime.now()
	dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
	print "ended at {d1}".format(d1=dt_string)
