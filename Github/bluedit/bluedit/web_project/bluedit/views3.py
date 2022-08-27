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
child_check = []

# Create your views here.
def index(request):
    posts = Post.objects.all()
    votelist = []
    comment_count = []
    post_type = []
    zipped = post_list(request, posts)
    subs = Subbluedit.objects.all().order_by('-member_count')[:5]
    page_number = request.GET.get('page')
    return render(request, 'bluedit/index.html', {
            'zipped': zipped,
            'subs': subs,
            'page_number': page_number,
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
        password = request.POST['password']
        repassword = request.POST['repassword']
        if password != repassword:
            message = 'Passwords must be identical!'
            return render(request, 'bluedit/register.html', {
                'message': message
            })
        new = User.objects.create_user(username, password)
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
def submit(request, sub_name=None):
    if request.method == 'GET':
        if not sub_name:
            form = PostForm(initial={'image': 'http://www.dummy.url'})
            return render(request, 'bluedit/submit.html', {
                'form': form
            })
        else:
            sub = Subbluedit.objects.get(name=sub_name)
            form = PostSubForm(initial={'subbluedit': sub, 'image': 'http://www.dummy.url'})
            return render(request, 'bluedit/submit.html', {
                'form': form,
                'sub_name': sub_name
            })
    elif request.method == 'POST':
        f = PostForm(request.POST)
        if f.is_valid():
            post = f.save(commit=False)
            user_id = request.user.id
            user = User.objects.get(pk=user_id)
            post.user = user
            if post.image == 'http://www.dummy.url':
                post.image = None
            elif post.description == 'http://www.dummy.url':
                post.description = None
            post.save()
            return HttpResponseRedirect(reverse("post", args=[post.id]))
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
    page = 'post'
    sub = Subbluedit.objects.get(pk=post.subbluedit.id)
    type = join_or_leave(request, sub.name)
    member_count = post.subbluedit.members.all().count()
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
            'comment_count': comment_count,
            'page': page,
            'type': type,
            'member_count': member_count,
            'sub': sub
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
            data = get_comment(request, comment)
            vote_type = data[0]
            date = data[1]
            timeunit = data[2]
            return render(request, 'bluedit/blocks/comment-block-new.html', {
                    'comment': comment,
                    'vote_type': vote_type,
                    'date': date,
                    'timeunit': timeunit
                })
            return render(request, 'bluedit/comment-block-new.html', {
                'comment': comment,
            })
    else:
        message = "Sorry, this page doesn't exist"
        return render(request, 'bluedit/apology.html', {
            'message': message
        }
        )
def edit(request, comment_id):
    try:
        comment = Comment.objects.get(pk=comment_id)
    except Comment.DoesNotExist:
        message = "Sorry, this page doesn't exist"
        return render(request, 'bluedit/apology.html', {
            'message': message
        }
        )
    if request.method == 'GET':
        if request.user.is_authenticated:
            if request.user.id == comment.user.id:
                form = CommentForm(instance=comment)
                return render(request, 'bluedit/edit.html', {
                    'comment': comment,
                    'form': form
                })
            else:
                message = "Error 403 - Forbidden"
                return render(request, 'bluedit/apology.html', {
                    'message': message
                })
        else:
            message = "Error 403 - Forbidden"
            return render(request, 'bluedit/apology.html', {
                'message': message
            })
    if request.method == 'PUT':
        put = QueryDict(request.body)
        text = put.get('text')
        comment.text = text
        comment.save()
        return render(request, 'bluedit/edit.html', {
            'comment': comment,
        })


def edit_post(request, post_id):
    try:
        post = Post.objects.get(pk=post_id)
    except Post.DoesNotExist:
        message = "Sorry, this page doesn't exist"
        return render(request, 'bluedit/apology.html', {
            'message': message
        }
        )
    if request.method == 'GET':
        if request.user.is_authenticated:
            if request.user.id == post.user.id:
                form = PostForm(instance=post)
                return render(request, 'bluedit/edit-post.html', {
                    'post': post,
                    'form': form
                })
            else:
                message = "Error 403 - Forbidden"
                return render(request, 'bluedit/apology.html', {
                    'message': message
                })
        else:
            message = "Error 403 - Forbidden"
            return render(request, 'bluedit/apology.html', {
                'message': message
            })
    if request.method == 'PUT':
        put = QueryDict(request.body)
        description = put.get('description')
        print(description)
        post.description = description
        post.save()
        return render(request, 'bluedit/edit-post.html', {
            'post': post,
        })

def vote(request, type, id, vote_type, no_tree=None):
    user_id = request.user.id
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        message = "Sorry, you need to log in first"
        return render(request, 'bluedit/apology.html', {
            'message': message
        })
    if request.method == 'PUT':
        if type == 'comment':
            comment = Comment.objects.get(pk=id)
            touple = return_date(comment)
            date = touple[0][0]
            timeunit = touple[1][0]
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
                if no_tree == 'True':
                    return render(request, 'bluedit/blocks/comment-block-no-tree.html', {
                        'comment': comment,
                        'vote_type': vote_type,
                        'date': date,
                        'timeunit': timeunit,
                    })
                else:
                    return render(request, 'bluedit/blocks/comment-block.html', {
                        'comment': comment,
                        'vote_type': vote_type,
                        'date': date,
                        'timeunit': timeunit,
                    })
            elif vote_type == 'up':
                check = Vote.objects.create(comment=comment, user=user, vote_type='up')
                comment.vote_count += 1
            else:
                check = Vote.objects.create(comment=comment, user=user, vote_type='down')
                comment.vote_count -= 1
            comment.save()
            check.save()
            if no_tree == 'True':
                return render(request, 'bluedit/blocks/comment-block-no-tree.html', {
                    'comment': comment,
                    'vote_type': vote_type,
                    'date': date,
                    'timeunit': timeunit,
                })
            else:
                return render(request, 'bluedit/blocks/comment-block.html', {
                    'comment': comment,
                    'vote_type': vote_type,
                    'date': date,
                    'timeunit': timeunit,
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
        votelist = []
        comment_count = []
        post_type = []
        sub = Subbluedit.objects.get(name=name)
        posts = sub.posts.all()
        user_id = request.user.id
        if request.user.is_authenticated:
            user = User.objects.get(pk=user_id)
            if user not in sub.members.all():
                type = 'join'
            else:
                type = 'leave'
        else:
            type = 'join'
        zipped = post_list(request, posts)
        member_count = sub.members.all().count()
        return render(request, 'bluedit/subbluedit.html', {
                    'sub': sub,
                    'posts': posts,
                    'type': type,
                    'zipped': zipped,
                    'member_count': member_count
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
            sub.member_count += 1
            sub.save()
            type = 'leave'
            member_count = sub.members.all().count()
            return render(request, 'bluedit/join.html', {
                'post': post,
                'type': type,
                'sub': sub,
                'member_count': member_count
            })
        else:
            message = "You are already a member of this subbluedit"
            return render(request, 'bluedit/apology.html', {
                'message': message
            })
    elif type == 'leave':
        if user in sub.members.all():
            sub.members.remove(user)
            sub.member_count -= 1
            sub.save()
            type = 'join'
            member_count = sub.members.all().count()
            return render(request, 'bluedit/join.html', {
                'post': post,
                'type': type,
                'sub': sub,
                'member_count': member_count
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
            data = get_comment(request, reply)
            vote_type = data[0]
            date = data[1]
            timeunit = data[2]
            return render(request, 'bluedit/blocks/comment-block.html', {
                    'comment': reply,
                    'vote_type': vote_type,
                    'date': date,
                    'timeunit': timeunit
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
def submit_option(request, option, sub_name=None):
    if option == 'text':
        if not sub_name:
            form = PostForm(initial={'image': 'http://www.dummy.url'})
        else:
            sub = Subbluedit.objects.get(name=sub_name)
            form = PostSubForm(initial={'subbluedit': sub, 'image': 'http://www.dummy.url'})
        return render(request, 'bluedit/htmx/submit-text.html', {
            'form': form,
            'sub_name': sub_name
        })
    elif option == 'image':
        if not sub_name:
            form = PostForm(initial={'description': 'http://www.dummy.url'})
        else:
            sub = Subbluedit.objects.get(name=sub_name)
            form = PostSubForm(initial={'subbluedit': sub, 'description': 'http://www.dummy.url'})
        return render(request, 'bluedit/htmx/submit-img.html', {
            'form': form,
            'sub_name': sub_name
        })

def user(request, username):
    profile_user = User.objects.get(username=username)
    user_id = request.user.id
    comments = profile_user.comments.all()
    votelist = []
    try:
        user = User.objects.get(pk=user_id)
        for comment in comments:
            if user.votes.filter(comment=comment).exists():
                vote_type = user.votes.get(comment=comment).vote_type
                votelist.append(vote_type)
            else:
                votelist.append(False)
    except User.DoesNotExist:
        for comment in comments:
            votelist.append(False)
    date_time_list = return_date(comments)
    datelist = date_time_list[0]
    timeunit = date_time_list[1]
    zipped = zip(comments, votelist, datelist, timeunit)
    return render(request, 'bluedit/user2.html', {
        'comments': comments,
        'profile_user': profile_user,
        'zipped': zipped
    })

def user_option(request, username, option):
    profile_user = User.objects.get(username=username)
    user_id = request.user.id
    if option == 'comments':
        comments = profile_user.comments.all()
        votelist = []
        try:
            user = User.objects.get(pk=user_id)
            for comment in comments:
                if user.votes.filter(comment=comment).exists():
                    vote_type = user.votes.get(comment=comment).vote_type
                    votelist.append(vote_type)
                else:
                    votelist.append(False)
        except User.DoesNotExist:
            for comment in comments:
                votelist.append(False)
        touple = return_date(comments)
        datelist = touple[0]
        timeunit = touple[1]
        zipped = zip(comments, votelist, datelist, timeunit)
        return render(request, 'bluedit/htmx/user-comment.html', {
            'comments': comments,
            'zipped': zipped,
            'profile_user': profile_user
        })
    elif option == 'posts':
        posts = profile_user.posts.all()
        votelist = []
        comment_count = []
        post_type = []
        zipped = post_list(request, posts)
        return render(request, 'bluedit/htmx/user-post.html', {
                'posts': posts,
                'votelist': votelist,
                'zipped': zipped,
        })

def delete(request, id, name):
    if request.method == 'DELETE':
        if request.user.is_authenticated:
            if name == 'post':
                user_id = request.user.id
                user = User.objects.get(pk=user_id)
                post = Post.objects.get(pk=id)
                if user == post.user:
                    post.delete()
                    return render(request, 'bluedit/htmx/deleted.html')
                else:
                    message = "Error 403 - Forbidden"
                    return render(request, 'bluedit/apology.html', {
                        'message': message
                    })
            if name == 'comment':
                user_id = request.user.id
                user = User.objects.get(pk=user_id)
                comment = Comment.objects.get(pk=id)
                if user == comment.user:
                    comment.delete()
                    return render(request, 'bluedit/htmx/deleted.html')
                else:
                        message = "Error 403 - Forbidden"
                        return render(request, 'bluedit/apology.html', {
                            'message': message
                        })
        else:
                    message = "Error 403 - Forbidden"
                    return render(request, 'bluedit/apology.html', {
                        'message': message
                    })
    else:
        message = "This site doesn't exist"
        return render(request, 'bluedit/apology.html', {
            'message': message
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
    touple = return_date(posts)
    datelist = touple[0]
    timeunit = touple[1]
    for post in posts:
        count = Comment.objects.filter(post=post).count()
        comment_count.append(count)
        if post.image != None:
            x = 'image'
            post_type.append(x)
        else:
            x = 'text'
            post_type.append(x)
    oldlist = list(zip(posts, votelist, datelist, timeunit, comment_count, post_type))
    page_number = request.GET.get('page')
    if not page_number:
        page_number = 1
    newlist = []
    newlist.clear()
    for list_object in oldlist:
        paginator = Paginator(list_object, 3) # Show 3 posts per page.
        x = paginator.get_page(page_number)
        newlist.append(x)
    zipped = zip(newlist[0], newlist[1], newlist[2], newlist[3], newlist[4], newlist[5])
    #zipped = zip(posts, votelist, datelist, timeunit, comment_count, post_type)
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
    touple = return_date(comment)
    date = touple[0][0]
    timeunit = touple[1][0]
    
    return vote_type, date, timeunit

def join_or_leave(request, name):
    check = Subbluedit.objects.filter(name=name).exists()
    if check:
        sub = Subbluedit.objects.get(name=name)
        user_id = request.user.id
        if request.user.is_authenticated:
            user = User.objects.get(pk=user_id)
            if user not in sub.members.all():
                type = 'join'
            else:
                type = 'leave'
        else:
            type = 'join'
        return type
    else:
        return False