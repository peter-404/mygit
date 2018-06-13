from django.contrib import admin
from blog.models import Board, Topic, Post

# Register your models here.
admin.site.register(Board)
admin.site.register(Topic)
admin.site.register(Post)