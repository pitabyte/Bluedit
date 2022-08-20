from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register', views.register, name='register'),
    path('login', views.login_view, name='login'),
    path('logout', views.logout_view, name='logout'),
    path('submit', views.submit, name='submit'),
    path('<str:sub_name>/submit', views.submit, name='submit'),
    path('post/<str:post_id>', views.post, name='post'),
    path('comment/<str:post_id>', views.comment, name='comment'),
    path('edit/<str:comment_id>', views.edit, name='edit'),
    path('vote/<str:type>/<str:id>/<str:vote_type>', views.vote, name='vote'),
    path('vote/<str:type>/<str:id>/<str:vote_type>/<str:no_tree>', views.vote, name='vote'),
    path('b/<str:name>', views.subbluedit, name='subbluedit'),
    path('subcreate', views.subcreate, name='subcreate'),
    path('join/<str:sub_id>/<str:type>', views.join, name='join'),
    path('reply/<str:comment_id>', views.reply, name='reply'),
    path('search', views.search, name='search'),
    path('submit_option/<str:option>', views.submit_option, name='submit_option'),
    path('submit_option/<str:option>/<str:sub_name>', views.submit_option, name='submit_option'),
    path('user/<str:username>', views.user, name='user'),
    path('user_option/<str:username>/<str:option>', views.user_option, name='user_option'),
    path('delete/<str:id>/<str:name>', views.delete, name='delete'),
]
