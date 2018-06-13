from django import forms
from blog.models import Topic, Post

class TopicForm(forms.ModelForm):
	message = forms.CharField(widget=forms.Textarea(), max_length=4000)

	class Meta:
		model = Topic
		fields = ['subject', 'message']

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('message',)
    