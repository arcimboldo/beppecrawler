# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/topics/item-pipeline.html

from beppegrillo.items import BeppeGrilloCommentItem, BeppeGrilloPostItem
from pymongo import MongoClient

class BeppegrilloPipelineMongoStore(object):
	def __init__(self):
		# this goes on a mongodb account on the cloud with 500Mb of space, it would work but it's too slow
		# I can only scrap 140-160 items/minute agaist 4300-5000 items a minute on a local database
		#self.connection = MongoClient('mongodb://scraper:Luphuhie8@ds049157.mongolab.com:49157/beppegrillo')

		# connect to local database
		self.connection = MongoClient()
		self.posts = self.connection.beppegrillo.posts
		self.comments = self.connection.beppegrillo.comments

	def process_item(self, item, spider):
		if isinstance(item, BeppeGrilloPostItem):
			self.posts.update(
				{
					'_id': item['url'],
				},
				{
					'$push': {
						'samples': {
							'commenti': item['commenti'],
							'time': item['crawl_time'],
						},
					},
				}, upsert=True)
		if isinstance(item, BeppeGrilloCommentItem):
			self.comments.update(
				{
					'_id': item['_id'],
					'data': item['data'],
					'firma': item['firma'],
					'testo': item['testo'],
					'post': item['post'],
				},
				{
					'$push': {
						'samples': {
							'piu_votato': item['piu_votato'],
							'voti': item['voti'],
							'time': item['crawl_time'],
						},
					},
				}, upsert=True)
