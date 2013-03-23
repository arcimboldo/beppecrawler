# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/topics/items.html

from scrapy.item import Item, Field

class BeppeGrilloPostItem(Item):
    # define the fields for your item here like:
    crawl_time = Field()
    titolo = Field()
    url = Field()
    data = Field()
    commenti = Field()
    
class BeppeGrilloCommentItem(Item):
    # define the fields for your item here like:
    crawl_time = Field()
    post = Field()
    _id = Field()
    testo = Field()
    voti = Field()
    firma = Field()
    data = Field()
    piu_votato = Field()
