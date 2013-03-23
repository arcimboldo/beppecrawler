# Scrapy settings for beppegrillo project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#

BOT_NAME = 'beppegrillo'

SPIDER_MODULES = ['beppegrillo.spiders']
NEWSPIDER_MODULE = 'beppegrillo.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
LOG_LEVEL='INFO'
# ITEM_PIPELINES=['beppegrillo.pipelines.BeppegrilloPipelineMongoStore',]
ITEM_PIPELINES=['beppegrillo.sqlpipe.SqlPipeline']

SQLDB_URI="sqlite:///beppegrillo.db"
