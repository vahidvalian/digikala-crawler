import sys,config,logging,sqlite3,requests,json,signal
from bs4 import BeautifulSoup
from unidecode import unidecode
class crawler:
	def __init__(self):
		signal.signal(signal.SIGINT, self.signal_handler)
		self.log_config()
		self.logger.info('crawler started')
		self.db_open()
		self.db_init()
		
		for i in range(1,100000):
			print(i)
		# self.manage_pages()
	
	def signal_handler(self, signal, frame):
	  self.generate_output()
	  sys.exit(0)

	def get_pages_count(self):
		target_url = config.target_url + 'pageno=1'
		self.logger.info("get totol page count from: {0}".format(target_url))
		page = requests.get(target_url)
		soup = BeautifulSoup(page.content,"html.parser")
		page_link = soup.find("a",{"class":"c-pager__next"})
		page_count = int(page_link['data-page'])
		self.logger.info("totol page count is: {0}".format(page_count))
		return page_count

	def manage_pages(self):
		last_page = self.get_pages_count() + 1
		pages = range(1,last_page)
		for i in pages:
			self.get_offers(i)

	def get_offers(self, page=1):
		target_url = config.target_url + 'pageno={page}'.format(page=page)
		self.logger.info("getting offers from page: {0}, url: {1}".format(page,target_url))
		page = requests.get(target_url)
		soup = BeautifulSoup(page.content,"html.parser")
		items = soup.find_all("div",{"class":"c-product-box"})
		for item in items:
			attr = json.loads(item['data-enhanced-ecommerce'])
			info_div = item.find("div", {"class":"c-price__value"})

			try:
				dkid = attr['id']
				dkname = attr['name']
				dkcat = attr['category']
				dkprice = int(attr['price'])/10
				dkimage = item.find("img")['src']
				dkdiscount = int(unidecode(item.find("div", {"class":"c-price__discount-oval"}).text.strip()).replace("%",""))
				dkorgprice = int(unidecode(info_div.find("del").text.replace(",","").strip()))
			except Exception as e:
				self.logger.error(str(e))
				continue
			if dkdiscount >= config.discount and dkprice <= config.max_price and dkcat not in config.exclude_category:
				sql = 'replace into products values({dkid},"{dkname}", "{dkcat}", {dkprice}, {dkorgprice}, {dkdiscount}, "{dkimage}", datetime("now"),datetime("now"))'.format(dkid=dkid, dkname=dkname, dkcat=dkcat, dkprice=dkprice, dkorgprice=dkorgprice, dkdiscount=dkdiscount, dkimage=dkimage)
				self.db_query(sql)
	
	def generate_output(self):
		rows = self.db_select('*','products','1', 'discount DESC, price ASC')
		
		if not rows:
			exit(0)

		result = "<html dir='rtl'><head><title>Digikala Promotions</title><meta name='language' content='farsi'/><meta charset='utf-8'/><head><body><style>img {width: 150px;height:auto} body * { font-size: 18px }</style><table>"
		f = open('index.html', "w+")
		f.write(result)
		for row in rows:
			result = "<tr>"
			result += "<td><a target='_blank' href='{0}'><img src='{0}' /></a></td>".format(row[6])
			result += "<td>"
			result += "{0}".format(row[1])
			result += "<br/>"
			result += "Price: {0} => {1}".format(row[4], row[3])
			result += "<br/>"
			result += "Discount: {0}%".format(row[5])
			result += "<br/>"
			result += "URL: <a target='_blank' href='https://www.digikala.com/product/dkp-{0}'>https://www.digikala.com/product/dkp-{0}</a>".format(row[0])
			result += "<br/>"
			result += row[7]
			result += "<br/>"
			result += "</td>"
			result += "</tr>"
			f.write(result)
		result = "</table></body></html>"
		f.write(result)
		f.close()

	def db_open(self):
		self.conn = sqlite3.connect(config.db_name);
		self.cursor = self.conn.cursor()

		self.logger.info("database opened: {0}".format(config.db_name))

	def db_close(self):
		if self.conn:
			self.conn.commit()
			self.cursor.close()
			self.conn.close()
			self.logger.info("database closed: {0}".format(config.db_name))

	def db_query(self, sql):
		self.cursor.execute(sql)
		self.conn.commit()
		self.logger.info("query executed: {0}".format(sql))

	def db_select(self, columns, table, where='1', orderby='created desc'):
		sql = 'SELECT {0} FROM {1} WHERE {2} ORDER BY {3}'.format(columns, table, where, orderby)
		self.cursor.execute(sql)
		self.logger.info("query executed: {0}".format(sql))
		rows =  self.cursor.fetchall()
		return rows

	def db_init(self):
		sql = """CREATE TABLE IF NOT EXISTS "products"(
		"id" Integer,
		"title" Text,
		"category" Text,
		"price" Integer NOT NULL,
		"oldprice" Integer NOT NULL,
		"discount" Integer NOT NULL,
		"img_url" Text,
		"created" DateTime NOT NULL,
		"updated" DateTime NOT NULL,
		CONSTRAINT "unique_id" UNIQUE ( "id" ) );"""
		self.db_query(sql)
		
	def log_config(self):
		self.logger = logging.getLogger(__name__)
		level = logging.getLevelName('INFO')
		handler = logging.FileHandler("crawler.log")
		formatter = logging.Formatter('%(asctime)s-%(levelname)s-(line%(lineno)d): %(message)s')
		handler.setFormatter(formatter)
		self.logger.setLevel(20)
		self.logger.disabled = False
		self.logger.addHandler(handler)    
if __name__ == '__main__':
	crawler()

