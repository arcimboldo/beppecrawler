# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.

from datetime import datetime
import pytz
import re

from scrapy import log
from scrapy.spider import BaseSpider
from scrapy.selector import HtmlXPathSelector, XmlXPathSelector
from scrapy.http import Request
from scrapy.utils.url import canonicalize_url

from beppegrillo.items import BeppeGrilloCommentItem, BeppeGrilloPostItem

rome_timezone = pytz.timezone('Europe/Rome')
mesi = ['Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno', 'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre' ]

def link_extractor_workaround(value):
  return value.strip()

class BeppeGrilloSpider(BaseSpider):
  name = 'beppegrillo'
  allowed_domains = ['www.beppegrillo.it']

  def __init__(self):
    self.start_urls = [ 'http://feeds.feedburner.com/beppegrillo/atom' ]

  def parse(self, response):
    """
    Main parser
    """
    xxs = XmlXPathSelector(response)
    xxs.register_namespace('feedburner', "http://rssnamespace.org/feedburner/ext/1.0")
    # For each blog post we have:
    #
    # * A main url like: http://www.beppegrillo/YYYY/MM/page_name/index.html
    #   this contains the blog post and the "commenti piu' votati" section
    #
    # * A javascript page http://www.beppegrillo/YYYY/MM/page_name.js
    #   which contains a list of URLs pointing to pages containing
    #   subsets of the comments.
    #
    # Therefore, we have to return a request for each page, and a
    # request for each one of these subpages containing a subset of
    # the comments for later parsing, made by specific methods.
    for url in xxs.select('//feedburner:origLink/text()').extract():
      yield Request(url, callback=self.parse_page)
      yield Request(url.replace('/index.html', '.js'), callback=self.parse_javascript)

  def parse_javascript(self, response):
    """
    Look in the `js` page for the first page containing the comments
    ordered by date.

    This usually looks like::

        document.write("<div id='capages'>Pagine:<span name='page_1' id='page_1'><a href='http://www.beppegrillo.it/2013/03/boldrini_e_gras.html#page_1' >1</a></span> <span name='page_2' id='page_2'><a href='http://www.beppegrillo.it/2013/03/boldrini_e_gras_3.html#page_2' >2</a></span> <span name='page_3' id='page_3'><a href='http://www.beppegrillo.it/2013/03/boldrini_e_gras_2.html#page_3' >3</a></span> <span name='page_4' id='page_4'><a href='http://www.beppegrillo.it/2013/03/boldrini_e_gras_1.html#page_4' >4</a></span> <span name='page_5' id='page_5'><a href='http://www.beppegrillo.it/2013/03/boldrini_e_gras_0.html#page_5' >5</a></span><br><span class='capagesdicitura'>Ogni pagina contiene 250 commenti con i relativi sottocommenti.</span></div>");
    """
    fragment = re.search('document\.write\(\"(.*)\"\)', response.body).group(1)
    hxs = HtmlXPathSelector(text = fragment)
    for url in hxs.select('//a/@href').extract():
      yield Request(canonicalize_url(url), callback=self.parse_page)

  def parse_page(self, response):
    """
    Parse a blog page containing a subset of the comments.
    """
    crawl_time = datetime.strptime(response.headers['Date'], '%a, %d %b %Y %H:%M:%S GMT')

    hxs = HtmlXPathSelector(response)

    post_canonical_url = hxs.select('//html/head/link[@rel="canonical"]/@href').extract()[0]

    ### parse post
    post = BeppeGrilloPostItem()
    post['crawl_time'] = crawl_time
    post['titolo'] = hxs.select('//h1/text()').extract()[0]
    post['url'] = post_canonical_url

    # parsing della data
    # ERROR: this can cause an exception
    day, month, year = hxs.select('//p[@id="commenti"]').re('(\d+) (\w+) (\d+)')
    year = int(year) + 2000 # assuming all dates are after 2000
    hour, minute = hxs.select('//p[@id="commenti"]').re('(\d+):(\d+)')
    post['data'] = datetime(year, mesi.index(month) + 1, int(day), int(hour), int(minute), tzinfo=rome_timezone)
    post['commenti'] = hxs.select('//p[@id="commenti"]').re('Commenti \((\d+)\)')[0]

    yield post

    ### tutti i commenti

    for node in hxs.select('//div[@class="comment-posted"]'):
      comment = BeppeGrilloCommentItem()
      comment['crawl_time'] = crawl_time
      comment['post'] = post_canonical_url
      comment['_id'] = int(node.select('.//div[@class="vota"]/@id').re('\d+')[0])
      comment['testo'] = '\n'.join(node.select('preceding::p[1]/text()').extract()).strip()
      # Prevent an error if the regexp does not match anything
      votes = node.select('.//td[@class="numvote"]').re('\d+')
      comment['voti'] = int(votes[0]) if votes else 0

      testo_firma = (node.select('.//td/b/a/text()') or node.select('.//td/b/text()'))[0].extract()

      # rimuove la data dalla firma
      testo_firma = re.sub('\d{2}\.\d{2}\.\d{2} \d{2}:\d{2}\|', '', testo_firma).strip()

      comment['firma'] = testo_firma
      day, month, year, hour, minute = map(int, node.re('(\d{2})\.(\d{2})\.(\d{2}) (\d{2}):(\d{2})\|'))
      year = year + 2000 # assuming all dates are after 2000
      comment['data'] = datetime(year, month, day, hour, minute, tzinfo=rome_timezone)

      if hxs.select("//h3[contains(., \"Commenti piu' votati\")]"):
        comment['piu_votato'] = 'si'
      else:
        comment['piu_votato'] = 'no'

      yield comment
