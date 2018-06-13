from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from blog.models import Board, Topic, Post
from blog.forms import TopicForm, PostForm
from django.db.models import Count
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import UpdateView, ListView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# Create your views here.

# # 主页，列出所有版块
# def home(request):
# 	boards = Board.objects.all()
# 	return render(request, 'home.html', {'boards': boards})

# # 列出当前版块所有主题
# def board_topic(request, pk):
# 	board = get_object_or_404(Board, pk=pk)
# 	# annotate 产生新的一列（但不存入数据库），即新的属性
# 	# 这里产生的是 replies 属性，值为该 topic 拥有的 post 数目-1
# 	# -1 是除去发布者的那一个 post
# 	queryset = board.topics.order_by('last_updated').annotate(replies=Count('posts')-1)
# 	page = request.GET.get('page', 1)
# 	paginator = Paginator(queryset, 10)
# 	try:
# 		topics = paginator.page(page)
# 	except EmptyPage:
# 		topics = paginator.page(1)
# 	except PageNotAnInteger:
# 		topics = paginator.page(1)

# 	return render(request, 'topics.html', {'board': board, 'topics': topics})

# 新增主题
@login_required
def new_topic(request, pk):
	board = get_object_or_404(Board, pk=pk)
	if request.method == 'POST':
		form = TopicForm(request.POST)
		if form.is_valid():
			topic = form.save(commit=False)
			topic.board = board
			topic.starter = request.user
			topic.save()

			post = Post.objects.create(
				message = form.cleaned_data.get('message'),
				topic = topic,
				created_by = request.user)
			
			# 这里的 redirect 第一个属性就是 url 里面的 name 属性
			return redirect('topic_posts', pk=board.pk, topic_pk=topic.pk)
	else:
		form = TopicForm()
	return render(request, 'new_topic.html', {'board': board, 'form': form})

# # 列出当前主题所有回复
# def topic_posts(request, pk, topic_pk):
# 	topic = get_object_or_404(Topic, board_id=pk, pk=topic_pk)
# 	topic.views += 1
# 	topic.save()
# 	return render(request, 'topic_posts.html', {'topic': topic})

# 新增回复
@login_required
def reply_topic(request, pk, topic_pk):
	topic = get_object_or_404(Topic, board_id=pk, pk=topic_pk)
	if request.method == 'POST':
		form = PostForm(request.POST)
		if form.is_valid():
			post = form.save(commit=False)
			post.topic = topic
			post.created_by = request.user
			post.save()

			topic.last_updated = timezone.now()
			topic.save()
			return redirect('topic_posts', pk=pk, topic_pk=topic_pk)
	else:
		form = PostForm()
	return render(request, 'reply_topic.html', {'topic': topic, 'form': form})


# GCBV 基于类的通过视图
# 主页，列出所有版块
class BoardListView(ListView):
	model = Board
	template_name = 'home.html'
	context_object_name = 'boards'


# GCBV 基于类的通过视图
# 主题页，列出版块下所有主题（分页）
class TopicListView(ListView):
	model = Topic 						# 当前操作数据模块
	template_name = 'topics.html'		# 渲染文件
	context_object_name = 'topics'		# HTML 渲染时调用变量名
	paginate_by = 10					# 每页显示数目

	def get_context_data(self, **kwargs):
		kwargs['board'] = self.board
		return super().get_context_data(**kwargs)

	def get_queryset(self):
		self.board = get_object_or_404(Board, pk=self.kwargs.get('pk'))
		queryset = self.board.topics.order_by('-last_updated').annotate(replies=Count('posts')-1)
		return queryset


# GCBV 基于类的通过视图
# 回复页，列出主题下所有回复（分页）
class PostListView(ListView):
	model = Post
	template_name = 'topic_posts.html'
	context_object_name = 'posts'
	paginate_by = 2

	def get_context_data(self, **kwargs):
		session_key = 'viewed_topic_{}'.format(self.topic.pk)
		if not self.request.session.get(session_key, False):
			self.topic.views += 1
			self.topic.save()
			self.request.session[session_key] = True

		kwargs['topic'] = self.topic
		return super().get_context_data(**kwargs)

	def get_queryset(self):
		# self.kwargs.get('pk') 和 self.kwargs.get('topic_pk') 中的 'pk'、'topic_pk'是路由中指定的变量
		self.topic = get_object_or_404(Topic, board_id=self.kwargs.get('pk'), pk=self.kwargs.get('topic_pk'))
		queryset = self.topic.posts.order_by('created_at')
		return queryset


# GCBV 基于类的通过视图
# 回复重新编辑
@method_decorator(login_required, name='dispatch')
class PostUpdateView(UpdateView):
    model = Post
    template_name = "edit_post.html"
    fields = ['message',]
    pk_url_kwarg = 'post_pk'
    context_object_name = 'post'	# HTML 模板里面调用的变量名

    def get_queryset(self):
    	queryset = super().get_queryset()		# 调用父类的 get_queryset() 方法
    	return queryset.filter(created_by=self.request.user)

    def form_valid(self, form):
    	post = form.save(commit=False)
    	post.updated_by = self.request.user
    	post.updated_at = timezone.now()
    	post.save()

    	return redirect('topic_posts', pk=post.topic.board.pk, topic_pk=post.topic.pk)

