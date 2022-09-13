from django.shortcuts import render
from django.urls import reverse
from .models import User, Post, PostForm, CommentForm, Comment, Vote, Subbluedit, SubblueditForm, ReplyForm
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import QueryDict
from django.db.models.query import QuerySet
import datetime
from datetime import timezone, timedelta

def sub_list(request):
    try:
        user_id = request.user.id
        user = User.objects.get(pk=user_id)
        sub_list = user.subs.all()
        subs = []
        for sub in sub_list:
            subs.append(sub.name)
    except User.DoesNotExist:
        sub_list = []
    sub_list = subs
    return {
        'sub_list': sub_list
    }