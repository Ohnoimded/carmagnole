from datetime import datetime, timezone, UTC
from django.conf import settings

import json 
import redis
import html
import re

from rest_framework.response import Response
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from utils.models import FrequentData

redis_client = redis.Redis(connection_pool=settings.REDIS["default"]["POOL"],decode_responses=True)

def create_mail(pls_return=True):
    featured_articles_ids  = json.loads(redis_client.get("featured_articles_ids"))[:5]
    
    article_data = FrequentData.objects.filter(id__in=featured_articles_ids).values("id","wordcount","section","publishdate","slug","headline","htmlbody","imageurl") 
    
    go_to_vert_or_horz=True ## refer the mjml doc in templats
    context = {}
    vert_news = []
    horz_news = []
    
    
    for article in article_data:
        article_id = article['id']
        imageurl = article['imageurl']
        # title = article['headline']
        title = article['headline'][:90]+"..." if len(article['headline'])>100 else article['headline']
        try:
            
            content = html.unescape(article['htmlbody']).replace("'", '"').replace('&amp;','&')
            content = re.sub(r'(<p>)(.*?)(</p>)',lambda m: m.group(1) + m.group(2).replace('"', '\u201C', 1).replace('"', '\u201D', 1) + m.group(3), content).replace("'", '"').replace('\\', '\\\\')
            content = re.sub(r'<[^>]+>', '',content)
            content = json.loads(content)[0]
        except:
            return Response(data=article_id)
        content = content[:300] if len(content)>=300 else content
        url = "https://carmagnole.ohnoimded.com/article/"+ article['section'] + "/" + datetime.strftime(article['publishdate'],"%Y/%m/%d/")+ article['slug']
        
        processed_article = {'id':article_id,'imageurl':imageurl,"title":title,"content":content,"url":url}
        if go_to_vert_or_horz:
            vert_news.append(processed_article)
            if len(horz_news) >=2:
                go_to_vert_or_horz =True
            else:
                go_to_vert_or_horz = False
        elif len(horz_news)<=2:
            horz_news.append(processed_article)
            go_to_vert_or_horz = not go_to_vert_or_horz
        
    context['vert_news'] = vert_news
    context['horz_news'] = horz_news
                   

    html_content = render_to_string(template_name="mail_templates/newsletter.mjml", context=context)
    text_content = strip_tags(html_content)
    redis_client.set('daily_newsletter',html_content, ex=2*60*60)
    if pls_return==True:
        return html_content,text_content