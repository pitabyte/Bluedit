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

final_list = []
child_check = []

# Create your views here.
def index(request):
    posts = Post.objects.all()
    votelist = []
    comment_count = []
    post_type = []
    user_id = request.user.id
    if request.user.is_authenticated:
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
    touple = return_date(posts)
    datelist = touple[0]
    timeunit = touple[1] 
    touple = return_date(post)
    for post in posts:
        count = Comment.objects.filter(post=post).count()
        comment_count.append(count)
        if post.image != None:
            x = 'image'
            post_type.append(x)
        else:
            x = 'text'
            post_type.append(x)
    zipped = zip(posts, votelist, datelist, timeunit, comment_count, post_type)
    zipped = post_list(posts)
    return render(request, 'bluedit/index.html', {
            'posts': posts,
            'votelist': votelist,
            'zipped': zipped,
    })

def register(request):
    if request.method == 'GET':
        return render(request, 'bluedit/register.html')
    else:
        username = request.POST['username']
        check = User.objects.filter(username=username).exists()
        if check:
            message = 'This username already exists!'
            return render(request, 'bluedit/register.html', {
                'message': message
            })
        email = request.POST['email']
        password = request.POST['password']
        repassword = request.POST['repassword']
        if password != repassword:
            message = 'Passwords must be identical!'
            return render(request, 'bluedit/register.html', {
                'message': message
            })
        new = User.objects.create_user(username, email, password)
        new.save()
        login(request, new)
        return HttpResponseRedirect(reverse("index"))

def login_view(request):
    if request.method == 'GET':
        return render(request, 'bluedit/login.html')
    else:
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            message = 'Incorrect username or password!'
            return render(request, 'bluedit/login.html', {
                'message': message
            })

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))

@login_required(login_url='/login')
def submit(request):
    if request.method == 'GET':
        form = PostForm()
        return render(request, 'bluedit/submit.html', {
            'form': form
        })
    elif request.method == 'POST':
        f = PostForm(request.POST)
        if f.is_valid():
            post = f.save(commit=False)
            user_id = request.user.id
            user = User.objects.get(pk=user_id)
            post.user = user
            post.save()
            return render(request, 'bluedit/index.html', {
                'f': f,
                'post': post
            })
        else:
            print(f.errors.as_text())

def post(request, post_id):
    commentf = CommentForm()
    comments = Comment.objects.filter(post=post_id, tree_level=0)
    try:
        post = Post.objects.get(pk=post_id)
    except Post.DoesNotExist:
        message = "Sorry, this page doesn't exist"
        return render(request, 'bluedit/post3.html', {
            'message': message
        }
        )
    user_id = request.user.id
    if post.image != None:
        post_type = 'image'
    else:
        post_type = 'text'
    votelist = []
    final_list.clear()
    comments = comment_list(comments)
    for comment in comments:
        if request.user.is_authenticated:
            user = User.objects.get(pk=user_id)
            if user.votes.filter(comment=comment).exists():
                vote_type = user.votes.get(comment=comment).vote_type
                votelist.append(vote_type)
            else:
                votelist.append(False)
        else:
            votelist.append(False)
    touple = return_date(comments)
    datelist = touple[0]
    timeunit = touple[1]
    zipped = zip(comments, votelist, datelist, timeunit)
    touple = return_date(post)
    date_post = touple[0][0]
    timeunit_post = touple[1][0]
    if request.user.is_authenticated:
        user = User.objects.get(pk=user_id)
        if user.votes.filter(post=post).exists():
            vote_type_post = user.votes.get(post=post).vote_type
        else:
            vote_type_post = False
    else:
            vote_type_post = False
    comment_count = Comment.objects.filter(post=post).count()
    
    return render(request, 'bluedit/post4.html', {
            'post': post,
            'post_type': post_type,
            'commentf': commentf,
            'comments': comments,
            'votelist': votelist,
            'zipped': zipped,
            'vote_type_post': vote_type_post,
            'date_post': date_post,
            'timeunit_post': timeunit_post,
            'comment_count': comment_count
        })

def comment(request, post_id):
    if request.method == 'POST':
        f = CommentForm(request.POST)
        if f.is_valid():
            data = QueryDict(request.body)
            text = data.get('text')
            user_id = request.user.id
            user = User.objects.get(pk=user_id)
            post = Post.objects.get(pk=post_id)
            comment = Comment(post=post, user=user, text=text)
            comment.save()
            return render(request, 'bluedit/comment.html', {
                'comment': comment,


            })
    else:
        message = "Sorry, this page doesn't exist"
        return render(request, 'bluedit/apology.html', {
            'message': message
        }
        )
def edit(request, comment_id):
    comment = Comment.objects.get(pk=comment_id)
    if request.method == 'GET':
        form = CommentForm(instance=comment)
        return render(request, 'bluedit/edit.html', {
            'comment': comment,
            'form': form
        })
    if request.method == 'PUT':
        put = QueryDict(request.body)
        text = put.get('text')
        comment.text = text
        comment.save()
        return render(request, 'bluedit/edit.html', {
            'comment': comment,
        })


def vote(request, type, id, vote_type):
    user_id = request.user.id
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        print('error')
    if request.method == 'PUT':
        if type == 'comment':
            comment = Comment.objects.get(pk=id)
            check = Vote.objects.filter(comment=comment, user=user).exists()
            if check:
                vote = Vote.objects.get(comment=comment, user=user)
                Vote.objects.filter(comment=comment, user=user).delete()
                if vote.vote_type == 'up':
                    if vote_type == 'up':
                        comment.vote_count -= 1
                        vote_type = 'middle'
                    else:
                        comment.vote_count -= 2
                        vote_type = 'down'
                        check = Vote.objects.create(comment=comment, user=user, vote_type='down')
                        check.save()
                else:
                    if vote_type == 'up':
                        comment.vote_count += 2
                        vote_type = 'up'
                        check = Vote.objects.create(comment=comment, user=user, vote_type='up')
                        check.save()
                    else:
                        comment.vote_count += 1
                        vote_type = 'middle'
                comment.save()
                return render(request, 'bluedit/vote.html', {
                    'comment': comment,
                    'vote_type': vote_type
                })
            elif vote_type == 'up':
                check = Vote.objects.create(comment=comment, user=user, vote_type='up')
                comment.vote_count += 1
            else:
                check = Vote.objects.create(comment=comment, user=user, vote_type='down')
                comment.vote_count -= 1
            comment.save()
            check.save()
            print(user.votes.all())
            return render(request, 'bluedit/vote.html', {
                'comment': comment,
                'vote_type': vote_type
            })
        if type == 'post':
            post = Post.objects.get(pk=id)
            check = Vote.objects.filter(post=post, user=user).exists()
            if check:
                vote = Vote.objects.get(post=post, user=user)
                Vote.objects.filter(post=post, user=user).delete()
                if vote.vote_type == 'up':
                    if vote_type == 'up':
                        post.vote_count -= 1
                        vote_type = 'middle'
                    else:
                        post.vote_count -= 2
                        vote_type = 'down'
                        check = Vote.objects.create(post=post, user=user, vote_type='down')
                        check.save()
                else:
                    if vote_type == 'up':
                        post.vote_count += 2
                        vote_type = 'up'
                        check = Vote.objects.create(post=post, user=user, vote_type='up')
                        check.save()
                    else:
                        post.vote_count += 1
                        vote_type = 'middle'
                post.save()
                return render(request, 'bluedit/vote-post.html', {
                'post': post,
                'vote_type': vote_type
            })
            elif vote_type == 'up':
                check = Vote.objects.create(post=post, user=user, vote_type='up')
                post.vote_count += 1
            else:
                check = Vote.objects.create(post=post, user=user, vote_type='down')
                post.vote_count -= 1
            post.save()
            check.save()
            return render(request, 'bluedit/vote-post.html', {
                'post': post,
                'vote_type': vote_type
            })

    else:
        message = "Sorry, this page doesn't exist"
        return render(request, 'bluedit/apology.html', {
            'message': message
        })

def subcreate(request):
    if request.method == 'GET':
        form = SubblueditForm()
        return render(request, 'bluedit/subcreate.html', {
                    'form': form,
                })
    else:
        f = SubblueditForm(request.POST)
        if f.is_valid():
            sub = f.save(commit=False)
            user_id = request.user.id
            user = User.objects.get(pk=user_id)
            sub.user = user
            sub.save()
            sub.members.add(user)
            sub.save()
            return render(request, 'bluedit/subbluedit.html', {
                'sub': sub,
            })


def subbluedit(request, name):
    check = Subbluedit.objects.filter(name=name).exists()
    if check:
        sub = Subbluedit.objects.get(name=name)
        posts = sub.posts.all()
        user_id = request.user.id
        user = User.objects.get(pk=user_id)
        if user not in sub.members.all():
            type = 'join'
        else:
            type = 'leave'
        return render(request, 'bluedit/subbluedit.html', {
                    'sub': sub,
                    'posts': posts,
                    'type': type
                })
    else:
        message = "Sorry, this page doesn't exist"
        return render(request, 'bluedit/apology.html', {
            'message': message
        })

def join(request, sub_id, type):
    user_id = request.user.id
    user = User.objects.get(pk=user_id)
    sub = Subbluedit.objects.get(id=sub_id)
    if type == 'join':
        if user not in sub.members.all():
            sub.members.add(user)
            sub.save()
            type = 'leave'
            return render(request, 'bluedit/join.html', {
                'post': post,
                'type': type,
                'sub': sub
            })
        else:
            message = "You are already a member of this subbluedit"
            return render(request, 'bluedit/apology.html', {
                'message': message
            })
    elif type == 'leave':
        if user in sub.members.all():
            sub.members.remove(user)
            type = 'join'
            return render(request, 'bluedit/join.html', {
                'post': post,
                'type': type,
                'sub': sub
            })
        else:
            message = "You are not a member of this subbluedit"
            return render(request, 'bluedit/apology.html', {
                'message': message
            })

def reply(request, comment_id):
    if request.method == 'GET':
        commentf = ReplyForm()
        tree_level = Comment.objects.get(pk=comment_id).tree_level + 1
        return render(request, 'bluedit/reply-form.html', {
            'comment_id': comment_id,
            'commentf': commentf,
            'tree_level': tree_level
        })
    elif request.method == 'POST':
        f = ReplyForm(request.POST)
        if f.is_valid():
            data = QueryDict(request.body)
            text = data.get('text')
            user_id = request.user.id
            user = User.objects.get(pk=user_id)
            parent = Comment.objects.get(pk=comment_id)
            tree_level = parent.tree_level + 1
            reply = Comment(text=text, user=user, parent=parent, post=parent.post, tree_level=tree_level)
            reply.save()
            return render(request, 'bluedit/reply.html', {
                'reply': reply,
                'comment_id': comment_id
            })
        else:
            print(f.errors)

def search(request):
    if request.method == 'POST':
        sub_list = Subbluedit.objects.all()
        sub_list_names = []
        results = []
        data = QueryDict(request.body)
        search = data.get('search')
        print(search)
        for sub in sub_list:
            sub_list_names.append(sub.name)
        print(sub_list_names)
        for sub_name in sub_list_names:
            if search in sub_name:
                results.append(sub_name)
        print(results)
        return
    else:
        print(f.errors)

@login_required(login_url='/login')
def submit_option(request, option):
    form = PostForm()
    if option == 'text':
        return render(request, 'bluedit/htmx/submit-text.html', {
            'form': form
        })
    elif option == 'image':
        return render(request, 'bluedit/htmx/submit-img.html', {
            'form': form
        })

def user(request, username):
    user = User.objects.get(username=username)
    comments = user.comments.all()
    print(comments)
    votelist = []
    for comment in comments:
        if user.votes.filter(comment=comment).exists():
            vote_type = user.votes.get(comment=comment).vote_type
            votelist.append(vote_type)
        else:
            votelist.append(False)
    date_time_list = return_date(comments)
    datelist = date_time_list[0]
    timeunit = date_time_list[1]
    zipped = zip(comments, votelist, datelist, timeunit)
    return render(request, 'bluedit/user.html', {
        'comments': comments,
        'user': user,
        'zipped': zipped
    })

def user_option(request, username, option):
    profile_user = User.objects.get(username=username)
    user_id = request.user.id
    if option == 'comments':
        comments = profile_user.comments.all()
        votelist = []
        final_list.clear()
        comments = comment_list(comments)
        try:
            user = User.objects.get(pk=user_id)
            for comment in comments:
                if user.votes.filter(comment=comment).exists():
                    vote_type = user.votes.get(comment=comment).vote_type
                    votelist.append(vote_type)
                else:
                    votelist.append(False)
        except User.DoesNotExist:
            for comment in comment:
                votelist.append(False)
        touple = return_date(comments)
        datelist = touple[0]
        timeunit = touple[1]
        zipped = zip(comments, votelist, datelist, timeunit)
        return render(request, 'bluedit/htmx/user-comment.html', {
            'comments': comments,
            'user': user,
            'zipped': zipped
        })
    elif option == 'posts':
        posts = profile_user.posts.all()
        votelist = []
        comment_count = []
        post_type = []
        try:
            user = User.objects.get(pk=user_id)
            for post in posts:
                if user.votes.filter(post=post).exists():
                    vote_type = user.votes.get(post=post).vote_type
                    votelist.append(vote_type)
                else:
                    votelist.append(False)
        except User.DoesNotExist:
            for post in posts:
                votelist.append(False)
        touple = return_date(posts)
        datelist = touple[0]
        timeunit = touple[1] 
        touple = return_date(post)
        for post in posts:
            count = Comment.objects.filter(post=post).count()
            comment_count.append(count)
            if post.image != None:
                x = 'image'
                post_type.append(x)
            else:
                x = 'text'
                post_type.append(x)
        zipped = zip(posts, votelist, datelist, timeunit, comment_count, post_type)
        return render(request, 'bluedit/htmx/user-post.html', {
                'posts': posts,
                'votelist': votelist,
                'zipped': zipped,
        })


def return_date(comments):
    datelist = []
    timeunit = []
    now = datetime.datetime.now(timezone.utc)
    #check if comments argument is actually a single Post
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
            datelist.append(int(difference))    
            unit = 'second'
            timeunit.append(unit) 
        elif difference < h:
            difference = int(difference / 60)
            datelist.append(difference)
            unit = 'minute'
            timeunit.append(unit) 
        elif difference < d:
            difference = int(difference / 3600)
            datelist.append(difference)
            unit = 'hour'
            timeunit.append(unit) 
        elif difference < month:
            difference = int(difference / 86400)
            datelist.append(difference)
            unit = 'day'
            timeunit.append(unit) 
        elif difference < y:
            difference = int(difference / 2630000)
            datelist.append(difference)
            unit = 'month'
            timeunit.append(unit) 
        else:
            difference = int(difference / 31536000)
            datelist.append(difference)
            unit = 'year'
            timeunit.append(unit) 
    return datelist, timeunit

def comment_list(base):
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

def post_list(posts):
        votelist = []
        comment_count = []
        post_type = []
        if request.user.is_authenticated:
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
        touple = return_date(posts)
        datelist = touple[0]
        timeunit = touple[1] 
        touple = return_date(post)
        for post in posts:
            count = Comment.objects.filter(post=post).count()
            comment_count.append(count)
            if post.image != None:
                x = 'image'
                post_type.append(x)
            else:
                x = 'text'
                post_type.append(x)
        zipped = zip(posts, votelist, datelist, timeunit, comment_count, post_type)
        return zipped