from django.db import models
from django.contrib.auth.models import AbstractUser
from django.forms import ModelForm
from django import forms

# Create your models here.
class User(AbstractUser):
    pass

class Subbluedit(models.Model):
    name = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=128)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    members = models.ManyToManyField(User, default=None, related_name='subs')
    member_count = models.IntegerField(default=0)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
         return self.name


class Post(models.Model):
    title = models.CharField(max_length=64)
    description = models.CharField(max_length=512, null=True)
    image = models.URLField(null=True)
    date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    subbluedit = models.ForeignKey(Subbluedit, on_delete=models.CASCADE, related_name='posts')
    vote_count = models.IntegerField(default=0)
    class Meta:
        ordering = ['-date']

class Comment(models.Model):
    text = models.CharField(max_length=512)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    date = models.DateTimeField(auto_now_add=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    vote_count = models.IntegerField(default=0)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, related_name='child', null=True, blank=True)
    tree_level = models.IntegerField(default=0, null=True, blank=True)
    class Meta:
        ordering = ['-date']

class Vote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='votes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, related_name='voters')
    vote_type = models.CharField(max_length=4, default=0)

class SubblueditForm(ModelForm):
    class Meta:
        model = Subbluedit
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Description'}),
            'name': forms.TextInput(attrs={'placeholder': 'Subbluedit name'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].label = ''
        self.fields['description'].label = ''

class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'description', 'subbluedit', 'image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Description...'}),
            'title': forms.TextInput(attrs={'placeholder': 'Title...'}),
            'image': forms.URLInput(attrs={'placeholder': 'Image url...'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].label = ''
        self.fields['description'].label = ''
        self.fields['image'].label = ''
        self.fields['subbluedit'].label = ''

class PostSubForm(ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'description', 'subbluedit', 'image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Description...'}),
            'title': forms.TextInput(attrs={'placeholder': 'Title...'}),
            'image': forms.URLInput(attrs={'placeholder': 'Image url...'}),
            'subbluedit': forms.TextInput(attrs={'hidden': True})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].label = ''
        self.fields['description'].label = ''
        self.fields['image'].label = ''
        self.fields['subbluedit'].label = ''

class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control col-lg-6', 'rows': 5, 'placeholder': 'Your comment...'})
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].label = ''
        
class ReplyForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control col-lg-6', 'rows': 5, 'placeholder': 'Your reply...'})
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].label = ''
