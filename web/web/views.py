#!/usr/bin/env python
# -*- coding: utf-8 -*-# 
# @(#)views.py
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

# django imports
from django.http import HttpResponse
from django.utils.http import urlquote, urlunquote

# django templates
from django.template.loader import get_template
from django.template import Context

import sqlalchemy as sqla
from sqlalchemy.orm import sessionmaker

from beppegrillo.settings import SQLDB_OFFLINE_URI
from beppegrillo.sqlpipe import SqlComment, SqlDowngradedComment, SqlPost

def make_session():
    engine = sqla.create_engine(SQLDB_OFFLINE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session

def list_posts(request):
    template = get_template('list_posts.html')
    session = make_session()
    posts = session.query(SqlPost, sqla.func.count(SqlComment.nid)).join(SqlComment, SqlComment.post_url==SqlPost.url).group_by(SqlPost.url).all()
    posts = [{'title': post[0].title, 'url': post[0].url, 'quotedurl': urlquote(post[0].url), 'ncomments':  post[1]} for post in posts]
    html = template.render(Context({'posts': posts, 'baseurl': request.path }))
    return HttpResponse(html)


def get_post(request):

    template = get_template('show_post.html')
    url = urlunquote(request.REQUEST['url'])
    session = make_session()
    desaparecidos = session.query(SqlComment).filter_by(desaparecido=True,false_desaparecido=False, post_url=url).all()
    post = session.query(SqlPost).filter_by(url=url).first()

    context = {'title': post.title,
               'url': post.url,
               'ndesap': len(desaparecidos),
               'baseurl': request.build_absolute_uri(request.path + '?url=' + request.REQUEST['url'])}

    comments = [{'pdate': comment.posting_date.strftime("%d/%m/%Y, %H:%M"),
                 'votes': comment.votes,
                 'when_dis': comment.when_desaparecido.strftime("%d/%m/%Y, %H:%M"),
                 'signature': comment.comment_signature,
                 'text': comment.comment_text,} for comment in desaparecidos]

    slicen = int(request.REQUEST.get('page', 1))-1
    start = slicen*50
    end=start+50
    context['comments'] = comments[start:end]
    context['page'] = slicen+1
    context['numpages'] = len(comments)/50+1
    context['pages'] = range(1, context['numpages']+1)
    if context['page'] < context['numpages']:
        context['nextpage'] = slicen+2

    html = template.render(Context(context))

    downgraded = session.query(SqlComment, SqlDowngradedComment).join(SqlDowngradedComment, SqlDowngradedComment.comment_id==SqlComment.id)
    context['downgraded'] = []
    n = 0
    for comment in downgraded:
        if comment.SqlComment.votes >= comment.SqlDowngradedComment.old_votes:
            # If comment is not downgraded anymore, we should fix it.
            session.delete(comment.SqlDowngradedComment)
            continue
        n += 1
        context['downgraded'].append(
            {'pdate': comment.SqlComment.posting_date.strftime("%d/%m/%Y, %H:%M"),
             'votes': comment.SqlComment.votes,
             'old_votes': comment.SqlDowngradedComment.old_votes,
             'cur_votes': comment.SqlDowngradedComment.cur_votes,
             'signature': comment.SqlComment.comment_signature,
             'text': comment.SqlComment.comment_text,
             })
    context['ndown'] = n
    session.commit()

    return HttpResponse(html)
