from django.contrib import admin

# Register your models here.
from .models import User, Post, Vote, Comment, Subbluedit

admin.site.register(User)
admin.site.register(Post)
admin.site.register(Vote)
admin.site.register(Comment)
admin.site.register(Subbluedit)