import sys,config,logging,sqlite3,requests,json,signal,re, os
from bs4 import BeautifulSoup
from unidecode import unidecode
class crawler:
	def __init__(self):
		signal.signal(signal.SIGINT, self.signal_handler)
		self.log_config()
		self.logger.info('crawler started')
		self.db_open()
		self.db_init()
		self.db_backup_product()
		self.manage_pages()
		self.generate_output()
	
	def signal_handler(self, signal, frame):
	  self.generate_output()
	  sys.exit(0)

	def path(self, filename):
		dirname = os.path.dirname(__file__)
		return os.path.join(dirname, filename)

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
			try:
				attr = json.loads(item['data-enhanced-ecommerce'])
				info_div = item.find("div", {"class":"c-price__value"})
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

			include_title = False
			if config.include_title:
				for search in config.include_title:
					if re.search(search, dkname):
						include_title = True

			exclude_title = False
			if config.exclude_title:
				for search in config.exclude_title:
					if re.search(search, dkname):
						exclude_title = True


			if (dkdiscount >= config.discount and dkprice <= config.max_price and dkcat not in config.exclude_category) or include_title == True and exclude_title == False:
				sql = 'replace into products values({dkid},"{dkname}", "{dkcat}", {dkprice}, {dkorgprice}, {dkdiscount}, "{dkimage}", NUlL, datetime("now", "localtime"),datetime("now", "localtime"))'.format(dkid=dkid, dkname=dkname, dkcat=dkcat, dkprice=dkprice, dkorgprice=dkorgprice, dkdiscount=dkdiscount, dkimage=dkimage)
				self.db_query(sql)
	
	def generate_output(self):
		self.db_labeling()
		rows = self.db_select('*','products','1', 'tag is NULL, discount DESC, price ASC')
		
		# print(rows)

		if not rows:
			exit(0)


		result = "<html dir='rtl'><head><title>Digikala Promotions</title><meta name='language' content='farsi'/><meta charset='utf-8'/><head><body><style>img {width: 150px;height:auto} body * { font-size: 18px }</style><table>"
		f = open(self.path('index.html'), "w+")
		f.write(result)
		for row in rows:
			label = '<div style="text-align:center;color:gray; font-size:smaller">قدیمی</div>'
			if row[7] == 'new':
				label = '<div style="text-align:center;color:red; font-size:smaller">جدید</div>'
			result = "<tr>"
			result += "<td><a target='_blank' href='{0}'><img src='{0}' /><br/>{1}</a></td>".format(row[6], label)
			result += "<td>"
			result += "{0}".format(row[1])
			result += "<br/>"
			result += "Price: {0} => {1}".format(row[4], row[3])
			result += "<br/>"
			result += "Discount: {0}%".format(row[5])
			result += "<br/>"
			result += "URL: <a target='_blank' href='https://www.digikala.com/product/dkp-{0}'>https://www.digikala.com/product/dkp-{0}</a>".format(row[0])
			result += "<br/>"
			result += row[8]
			result += "<br/>"
			result += "</td>"
			result += "</tr>"
			f.write(result)
		result = "</table></body></html>"
		f.write(result)
		f.close()

	def db_open(self):
		self.db_loc = self.path(config.db_name)

		self.conn = sqlite3.connect(self.db_loc)
		self.cursor = self.conn.cursor()

		self.logger.info("database opened: {0}".format(self.db_loc))

	def db_close(self):
		if self.conn:
			self.conn.commit()
			self.cursor.close()
			self.conn.close()
			self.logger.info("database closed: {0}".format(self.db_loc))

	def db_query(self, sql):
		self.cursor.execute(sql)
		self.conn.commit()
		self.logger.info("query executed: {0}".format(sql))

	def db_backup_product(self):
		self.db_query('DROP TABLE IF EXISTS `products_backup`');
		self.db_query('CREATE TABLE `products_backup` AS SELECT * FROM `products` WHERE 1');
		self.db_query('UPDATE `products_backup` SET `tag` = NULL');
		self.db_query('DELETE FROM `products`');

	def db_labeling(self):
		self.db_query("""update products set tag = 'new' where products.id in (SELECT A.id from products A
LEFt Join products_backup B
ON A.id = B.id
where B.id is NULL)""")

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
		"tag" Text,
		"created" DateTime NOT NULL,
		"updated" DateTime NOT NULL,
		CONSTRAINT "unique_id" UNIQUE ( "id" ) );"""
		self.db_query(sql)
		
	def log_config(self):
		self.logger = logging.getLogger(__name__)
		level = logging.getLevelName('ERROR')
		handler = logging.FileHandler(self.path('crawler.log'))
		formatter = logging.Formatter('%(asctime)s-%(levelname)s-(line%(lineno)d): %(message)s')
		handler.setFormatter(formatter)
		self.logger.setLevel(20)
		self.logger.disabled = False
		self.logger.addHandler(handler)    
if __name__ == '__main__':
	crawler()

