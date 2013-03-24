#!/usr/bin/env python
# -*- coding: utf-8 -*-# 
# @(#)sqlpipe.py
# 
# 
# Copyright (C) 2013, GC3, University of Zurich. All rights reserved.
# 
# 
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

__docformat__ = 'reStructuredText'

# Generic imports
from datetime import datetime

# SQLAlchemy imports
import sqlalchemy as sqla
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# scrapy imports
from scrapy import log

# beppegrillo's import
from beppegrillo.items import BeppeGrilloCommentItem, BeppeGrilloPostItem
from beppegrillo.settings import SQLDB_URI

Base = declarative_base()

def log_debug(msg):
    log.msg(msg, level=log.DEBUG)

def log_info(msg):
    log.msg(msg, level=log.INFO)

def log_warning(msg):
    log.msg(msg, level=log.WARNING)

def log_error(msg):
    log.msg(msg, level=log.ERROR)

def log_critical(msg):
    log.msg(msg, level=log.CRITICAL)


class SqlComment(Base):
    """
    Object used to store a comment in a DB
    """
    __tablename__ = 'comments'
    id = sqla.Column(sqla.String, primary_key=True)
    nid = sqla.Column(sqla.Integer)
    comment_text = sqla.Column(sqla.String)
    comment_signature = sqla.Column(sqla.String)
    posting_date = sqla.Column(sqla.DateTime)
    post_url = sqla.Column(sqla.String)
    votes = sqla.Column(sqla.Integer)
    last_seen = sqla.Column(sqla.DateTime)
    desaparecido = sqla.Column(sqla.Boolean)
    false_desaparecido = sqla.Column(sqla.Boolean)
    when_desaparecido = sqla.Column(sqla.DateTime)
    
    def __init__(self, item):
        self.nid = item['_id']
        self.comment_text = item.get('testo')
        self.comment_signature = item.get('firma')
        self.posting_date = item.get('data')
        self.post_url = item.get('post')
        self.votes = item.get('voti')
        self.last_seen = datetime.now()
        self.desaparecido=False
        self.false_desaparecido=False
        self.id = "%s+%s" % (self.post_url, self.nid)


class SqlDowngradedComment(Base):
    __tablename__ = 'downgraded_comments'
    nid = sqla.Column(sqla.Integer, primary_key=True)
    id = sqla.Column(sqla.String)
    comment_id = sqla.Column(sqla.String, sqla.ForeignKey('comments.id'))
    inserted = sqla.Column(sqla.DateTime)
    old_votes = sqla.Column(sqla.Integer)
    cur_votes = sqla.Column(sqla.Integer)

    def __init__(self, comment, old_votes):
        self.id = comment.id
        self.comment_id = comment.id
        self.inserted = datetime.now()
        self.old_votes = int(old_votes)    
        self.cur_votes = int(comment.votes)    

    
class SqlPost(Base):
    """
    Object used to store a post in a DB
    """
    __tablename__ = 'posts'
    url = sqla.Column(sqla.String, primary_key=True, nullable=False)
    # posting_date = sqla.Column(sqla.DateTime)    
    last_seen = sqla.Column(sqla.DateTime)
    
    def __init__(self, item):
        self.url = item['url']
        # posting_date = item['data']
        self.last_seen = datetime.now()


class SqlPipeline(object):
    def open_spider(self, spider):
        """
        This pipeline will store all items on a sql db using SQLAlchemy.
        """
        self.engine = sqla.create_engine(SQLDB_URI)
        # Create tables
        SqlPost.metadata.create_all(self.engine)
        SqlComment.metadata.create_all(self.engine)
        SqlDowngradedComment.metadata.create_all(self.engine)

        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        desaparecidos = self.session.query(
            SqlComment.id,
            SqlComment.post_url).filter_by(desaparecido=False).all()
        self.desaparecido_ids = [des.id for des in desaparecidos]
        self.crawled_posts = []

    def process_item(self, item, spider):
        if isinstance(item, BeppeGrilloPostItem):
            post = SqlPost(item)
            self.crawled_posts.append(post.url)
            sqlpost = self.session.query(SqlPost.url).filter_by(url=post.url).first()
            if not sqlpost:
                # No post with this url, add it to the db
                self.session.add(post)

        elif isinstance(item, BeppeGrilloCommentItem):
            comment = SqlComment(item)
            sqlcomment = self.session.query(
                SqlComment.id,
                SqlComment.votes,
                SqlComment.desaparecido,
                SqlComment.false_desaparecido).filter_by(id=comment.id).first()
            if not sqlcomment:
                # No comment found with this id, add id.
                self.session.add(comment)
            elif sqlcomment.desaparecido:
                if sqlcomment.false_desaparecido:
                    log_error("Comment %s is a *flipping* desaparecido: was considered desaparecido and found again already." % comment.id)
                else:
                    log_error("Comment %s was considered desaparecido but it's not. Updating." % comment.id)
                    cmt.false_desaparecido=True
                cmt = self.session.query(SqlComment).filter_by(id=comment.id)
                cmt.desaparecido=False
                if comment.id in self.desaparecido_ids:
                    self.desaparecido_ids.remove(comment.id)
            else:
                if comment.id in self.desaparecido_ids:
                    self.desaparecido_ids.remove(comment.id)
                # Check votes.
                if int(comment.votes) < int(sqlcomment.votes):
                    # Uh-ho, we have a downgrade!
                    log_info("Comment %s was downgraded: had %d votes, now it has %d" % (comment.id, sqlcomment.votes, comment.votes))
                    downgraded = SqlDowngradedComment(comment, sqlcomment.votes)
                    self.session.add(downgraded)

    def close_spider(self, spider):
        # self.session.query(SqlComment).filter(SqlComment.id.in_(self.desaparecidos)).update(
        #     values={SqlComment.desaparecido: True,
        #             SqlComment.when_desaparecido: datetime.now()},
        #     synchronize_session=False)
        # Uh-oh, it seems that we have too many desaparecidos... something is wrong.
        desaparecidos_found = 0
        for des in self.desaparecido_ids:
            comment = self.session.query(SqlComment).filter_by(id=des).first()
            if comment.post_url in self.crawled_posts:
                comment.desaparecido = True
                comment.when_desaparecido = datetime.now()
                desaparecidos_found += 1
        
        log_info("%d desaparecidos found." % desaparecidos_found)
        # Finally, commit the session
        self.session.commit()
