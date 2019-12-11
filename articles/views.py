from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.views.generic import ListView, DetailView
from django.views.generic.edit import UpdateView, DeleteView, CreateView
from django.urls import reverse_lazy

from .models import Article

import os
from django.http import HttpResponse, Http404


def download_file_view(request, pk):
    article = Article.objects.get(pk=pk)
    pred_path = article.get_pred_path()
    if os.path.exists(pred_path):
        with open(pred_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="None")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(pred_path)
            return response
    return Http404


class ArticleListView(LoginRequiredMixin, ListView):
    model = Article
    template_name = 'article_list.html'
    login_url = 'login' # redirect to OUR CUSTOM login url


class ArticleDetailView(LoginRequiredMixin, DetailView):
    model = Article
    template_name = 'article_detail.html'
    login_url = 'login' # redirect to OUR CUSTOM login url


class ArticleUpdateView(LoginRequiredMixin, UpdateView):
    model = Article
    template_name = 'article_edit.html'
    login_url = 'login' # redirect to OUR CUSTOM login url
    fields = ('title', 'body') # allow updating these

    def dispatch(self, request, *args, **kwargs):
        # Disable non-authors to update article
        obj = self.get_object()
        if obj.author != self.request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class ArticleDeleteView(LoginRequiredMixin, DeleteView):
    model = Article
    template_name = 'article_delete.html'
    login_url = 'login' # redirect to OUR CUSTOM login url
    success_url = reverse_lazy('article_list')

    def dispatch(self, request, *args, **kwargs):
        # Disable non-authors to update article
        obj = self.get_object()
        if obj.author != self.request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class ArticleCreateView(LoginRequiredMixin, CreateView):
    model = Article
    template_name = 'article_new.html'
    fields = ('title', 'body', 'flair', 't1', 't1ce', 't2')
    login_url = 'login' # redirect to OUR CUSTOM login url

    def form_valid(self, form): # automatically set author
        form.instance.author = self.request.user # requires user field
        return super().form_valid(form) # so anonymous --> error
