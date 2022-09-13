from django.shortcuts import render
from django.urls import reverse
from .models import User, Post, PostForm, CommentForm, Comment, Vote, Subbluedit, SubblueditForm, ReplyForm, PostSubForm
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import QueryDict
from django.db.models.query import QuerySet
import datetime
from django.core.paginator import Paginator
from datetime import timezone, timedelta


final_list = []

def time_passed(comments):
    value_list = [] #list of raw values of time that passed since the comment was created
    unit_list = [] 
    now = datetime.datetime.now(timezone.utc)
    #check if 'comments' argument is actually a single post or a comment. Then a 'dummy' list is created
    #so it can be treated like a list of comments without wrtiting the same code twice for a single post
    if isinstance(comments, QuerySet) == False and isinstance(comments, list) == False:
        temp = []
        temp.append(comments)
        temp.append('dummy')
        comments = temp
    for comment in comments:
        if comment == 'dummy':
            continue
        date = comment.date
        difference = (now - date).total_seconds()
        m = datetime.timedelta(minutes=1).total_seconds()
        h = datetime.timedelta(hours=1).total_seconds()
        d = datetime.timedelta(days=1).total_seconds()
        month = datetime.timedelta(weeks=4).total_seconds()
        y = datetime.timedelta(weeks=52).total_seconds()
        if difference < m:
            value_list.append(int(difference))    
            unit = 'second'
            unit_list.append(unit) 
        elif difference < h:
            difference = int(difference / 60)
            value_list.append(difference)
            unit = 'minute'
            unit_list.append(unit) 
        elif difference < d:
            difference = int(difference / 3600)
            value_list.append(difference)
            unit = 'hour'
            unit_list.append(unit) 
        elif difference < month:
            difference = int(difference / 86400)
            value_list.append(difference)
            unit = 'day'
            unit_list.append(unit) 
        elif difference < y:
            difference = int(difference / 2630000)
            value_list.append(difference)
            unit = 'month'
            unit_list.append(unit) 
        else:
            difference = int(difference / 31536000)
            value_list.append(difference)
            unit = 'year'
            unit_list.append(unit) 
    return value_list, unit_list

def comment_list(base): #takes list of comments with no parents and creates a list of all comments to be displayed under a post in a correct order
    if isinstance(base, QuerySet) == False:
        if base.child.all():
            final_list.append(base)
            for child in base.child.all():
                comment_list(child)
        else:
            final_list.append(base)
    else:
        for comment in base:
            if comment.child.all():
                final_list.append(comment)
                for child in comment.child.all():
                    comment_list(child)
            else:
                final_list.append(comment)
    return final_list

def post_list(request, posts):
    votelist = []
    comment_count = []
    post_type = []
    if request.user.is_authenticated:
        user_id = request.user.id
        user = User.objects.get(pk=user_id)
        for post in posts:
            if user.votes.filter(post=post).exists(): 
                vote_type = user.votes.get(post=post).vote_type
                votelist.append(vote_type)
            else:
                votelist.append(False)
    else:
        for post in posts:
            votelist.append(False)
    list_of_two = time_passed(posts)
    value_list = list_of_two[0]
    unit_list = list_of_two[1]
    for post in posts:
        count = Comment.objects.filter(post=post).count()
        comment_count.append(count)
        if post.image != None:
            x = 'image'
            post_type.append(x)
        else:
            x = 'text'
            post_type.append(x)
    page_number = request.GET.get('page')
    if not page_number:
        page_number = 1
    templist = [] #a list of lists to iterate over so paginator can be applied to each
    templist.append(posts)
    templist.append(votelist)
    templist.append(value_list)
    templist.append(unit_list)
    templist.append(comment_count)
    templist.append(post_type)
    newlist = []
    for list_object in templist:
            paginator = Paginator(list_object, 3) # Show 3 posts per page.
            x = paginator.get_page(page_number)
            newlist.append(x)
    zipped = zip(newlist[0], newlist[1], newlist[2], newlist[3], newlist[4], newlist[5]) #zip is used so every characteristic of a post can be displayed at the same time during iteration
    return zipped

def get_comment(request, comment):
    user_id = request.user.id
    votelist = []
    if request.user.is_authenticated:
        user = User.objects.get(pk=user_id)
        if user.votes.filter(comment=comment).exists():
            vote_type = user.votes.get(comment=comment).vote_type
        else:
            vote_type = False
    else:
        vote_type = False
    list_of_two = time_passed(comment)
    date = list_of_two[0][0]
    unit_list = list_of_two[1][0]
    
    return vote_type, date, unit_list

def join_or_leave(request, name):
    check = Subbluedit.objects.filter(name=name).exists()
    if check:
        sub = Subbluedit.objects.get(name=name)
        user_id = request.user.id
        if request.user.is_authenticated:
            user = User.objects.get(pk=user_id)
            if user not in sub.members.all():
                status = 'join'
            else:
                status = 'leave'
        else:
            status = 'join'
        return status
    else:
        return False

def comment_list(base): #For nested comments. Takes list of comments with no parents and creates a list of all comments to be displayed under a post in a correct order.
    if isinstance(base, QuerySet) == False:
        if base.child.all():
            final_list.append(base)
            for child in base.child.all():
                comment_list(child)
        else:
            final_list.append(base)
    else:
        #this iteration happens only once and is the first iteration that's why final_list (global variable) can be cleared here
        final_list.clear()
        for comment in base:
            if comment.child.all():
                final_list.append(comment)
                for child in comment.child.all():
                    comment_list(child)
            else:
                final_list.append(comment)
    return final_list

def date_to_time(date):
    now = datetime.datetime.now(timezone.utc)
    difference = (now - date).total_seconds()
    m = datetime.timedelta(minutes=1).total_seconds()
    h = datetime.timedelta(hours=1).total_seconds()
    d = datetime.timedelta(days=1).total_seconds()
    month = datetime.timedelta(weeks=4).total_seconds()
    y = datetime.timedelta(weeks=52).total_seconds()
    if difference < m:
        difference = int(difference)
        unit = 'second'
    elif difference < h:
        difference = int(difference / 60)
        unit = 'minute' 
    elif difference < d:
        difference = int(difference / 3600)
        unit = 'hour'
    elif difference < month:
        difference = int(difference / 86400)
        unit = 'day'
    elif difference < y:
        difference = int(difference / 2630000)
        unit = 'month'
    else:
        difference = int(difference / 31536000)
        unit = 'year'
    return difference, unit

def search_by_letter(query, base):
    if len(query) > len(base):
        return False
    letter_counter = 0
    while letter_counter < len(query):
        if query[letter_counter].lower() != base[letter_counter].lower():
            return False
        letter_counter += 1
        if letter_counter == len(query):
            return base
        

