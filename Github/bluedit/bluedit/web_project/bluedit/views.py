from django.shortcuts import render, redirect
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
from bluedit.helpers import time_passed, comment_list, post_list, get_comment, join_or_leave, comment_list, date_to_time, search_by_letter, is_special
from random import randint



# Create your views here.
def index(request):
    posts = Post.objects.all()
    votelist = []
    comment_count = []
    post_type = [] #image or text post
    zipped = post_list(request, posts) #post_list is defined in helpers.py
    subs = Subbluedit.objects.all().order_by('-member_count')[:5]
    subs_all = Subbluedit.objects.all()
    paginator = Paginator(posts, 5)
    page_number = request.GET.get('page')
    if not page_number:
        page_number = 1
    page_obj = paginator.get_page(page_number)
    return render(request, 'bluedit/index.html', {
            'zipped': zipped,
            'subs': subs,
            'page_number': page_number,
            'page_obj': page_obj,
            'subs_all': subs_all
    })

def register(request):
    if request.method == 'GET':
        return render(request, 'bluedit/register.html')
    else:
        username = request.POST['username']
        if is_special(username) == True:
            message = "'Username' must contain only letters and numbers"
            return render(request, 'bluedit/register.html', {
                'message': message
            })
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
        new = User.objects.create_user(username=username, password=password)
        new.save()
        login(request, new)
        next_url = request.POST['next']
        print(next_url)
        if next_url:
            return HttpResponseRedirect(next_url)
        else:
            return HttpResponseRedirect(reverse("index"))
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
            next_url = request.POST['next']
            print(next_url)
            if next_url:
                return HttpResponseRedirect(next_url)
            else:
                return HttpResponseRedirect(reverse("index"))
        else:
            message = 'Incorrect username or password!'
            return render(request, 'bluedit/login.html', {
                'message': message
            })

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

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
            message = 'Sorry, something went wrong'
            return render(request, 'bluedit/apology.html', {
            'message': message
        }
        )

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
    list_of_two = time_passed(comments)
    datelist = list_of_two[0]
    timeunit = list_of_two[1]
    zipped = zip(comments, votelist, datelist, timeunit)
    list_of_two = time_passed(post)
    date_post = list_of_two[0][0]
    timeunit_post = list_of_two[1][0]
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
        return HttpResponse("Very cheeky!")
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
        data = QueryDict(request.body)
        text = data.get('text')
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
        data = QueryDict(request.body)
        description = data.get('description')
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
            list_of_two = time_passed(comment)
            date = list_of_two[0][0]
            timeunit = list_of_two[1][0]
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
                if no_tree == 'True': #no_tree means that comment is displayed (e.g. user's profile) where their .tree_level is not taken into account
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

@login_required(login_url='/login')
def subcreate(request):
    form = SubblueditForm()
    if request.method == 'GET':
        return render(request, 'bluedit/subcreate.html', {
                    'form': form,
                })
    else:
        f = SubblueditForm(request.POST)
        if f.is_valid():
            name = request.POST['name']
            if is_special(name) == True:
                message = "'Subbluedit name' must contain only letters and numbers"
                return render(request, 'bluedit/subcreate.html', {
                    'message': message,
                    'form': form,
                })
            sub = f.save(commit=False)
            user_id = request.user.id
            user = User.objects.get(pk=user_id)
            sub.user = user
            sub.save()
            sub.members.add(user)
            sub.member_count += 1
            sub.save()
            return HttpResponseRedirect(reverse("subbluedit", args=[sub.name]))


def subbluedit(request, name):
    check = Subbluedit.objects.filter(name=name).exists()
    if check:
        votelist = []
        comment_count = []
        post_type = []
        sub = Subbluedit.objects.get(name=name)
        posts = sub.posts.all()
        if posts.count() == 0:
            message = True
        else:
            message = False
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
        paginator = Paginator(posts, 5)
        page_number = request.GET.get('page')
        if not page_number:
            page_number = 1
        page_obj = paginator.get_page(page_number)
        member_count = sub.members.all().count()
        return render(request, 'bluedit/subbluedit.html', {
                    'sub': sub,
                    'posts': posts,
                    'type': type,
                    'zipped': zipped,
                    'member_count': member_count,
                    'message': message,
                    'page_number': page_number,
                    'page_obj': page_obj,
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
        try:
            tree_level = Comment.objects.get(pk=comment_id).tree_level + 1
        except Comment.DoesNotExist:
            return HttpResponse('Very cheeky!')
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
            return render(request, 'bluedit/blocks/comment-block-reply.html', {
                    'comment': reply,
                    'vote_type': vote_type,
                    'date': date,
                    'timeunit': timeunit,
                    'comment_id': comment_id
                })
        
        else:
            print(f.errors)

def search(request):
    if request.method == 'POST':
        sub_list = Subbluedit.objects.all()
        member_count_list = []
        sub_list_names = []
        results = []
        data = QueryDict(request.body)
        search = data.get('search')
        for sub in sub_list:
            sub_list_names.append(sub.name)
        for sub_name in sub_list_names:
            if search_by_letter(search, sub_name):
                results.append(sub_name)
        action = 'search'
        if search == '':
            final_results = Subbluedit.objects.all().order_by('-member_count')[:4]
        else:
            final_results = Subbluedit.objects.filter(name__in=results).order_by('-member_count')[:4]
            for result in final_results:
                print(result.name)
        return render(request, 'bluedit/htmx/search-box.html', {
            'action': action,
            'final_results': final_results
        })
    elif request.method == 'GET':
        print('hello')
        print(request.GET.get('search'))
        action = 'close'
        return render(request, 'bluedit/htmx/search-box.html', {
            'action': action
        })
    else:
        print(f.errors)

@login_required(login_url='/login')
def submit_option(request, option, sub_name=None): #returns text or image html form for htmx call
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
    date_time_list = time_passed(comments)
    datelist = date_time_list[0]
    timeunit = date_time_list[1]
    zipped = zip(comments, votelist, datelist, timeunit)
    date = profile_user.date_joined.date()
    post_count = profile_user.posts.all().count()
    comment_count = profile_user.comments.all().count()
    list_of_two = date_to_time(profile_user.last_login)
    time = list_of_two[0]
    unit = list_of_two[1]
    unit.strip()
    return render(request, 'bluedit/user2.html', {
        'comments': comments,
        'profile_user': profile_user,
        'zipped': zipped,
        'date': date,
        'post_count': post_count,
        'comment_count': comment_count,
        'time': time,
        'unit': unit
    })

def user_option(request, username, option): #returns user's posts or comments in html format as response to htmx call
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
        list_of_two = time_passed(comments)
        datelist = list_of_two[0]
        timeunit = list_of_two[1]
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

def random(request):
    post_count = Post.objects.all().count()
    posts = Post.objects.all()
    id_list = []
    for post in posts:
        id_list.append(post.id)
    post_id = id_list[randint(0, (len(id_list)-1))]
    return HttpResponseRedirect(reverse("post", args=[post_id]))
