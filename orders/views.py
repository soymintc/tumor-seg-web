from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.views.generic import ListView, DetailView
from django.views.generic.edit import UpdateView, DeleteView, CreateView
from django.urls import reverse_lazy

from .models import Order

import os
from django.http import HttpResponse, Http404


def download_file_view(request, pk):
    order = Order.objects.get(pk=pk)
    pred_path = order.get_pred_path()
    if os.path.exists(pred_path):
        with open(pred_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="None")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(pred_path)
            return response
    return Http404


class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'order_list.html'
    login_url = 'login' # redirect to OUR CUSTOM login url


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'order_detail.html'
    login_url = 'login' # redirect to OUR CUSTOM login url


class OrderUpdateView(LoginRequiredMixin, UpdateView):
    model = Order
    template_name = 'order_edit.html'
    login_url = 'login' # redirect to OUR CUSTOM login url
    fields = ('title', 'body') # allow updating these

    def dispatch(self, request, *args, **kwargs):
        # Disable non-authors to update order
        obj = self.get_object()
        if obj.author != self.request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class OrderDeleteView(LoginRequiredMixin, DeleteView):
    model = Order
    template_name = 'order_delete.html'
    login_url = 'login' # redirect to OUR CUSTOM login url
    success_url = reverse_lazy('order_list')

    def dispatch(self, request, *args, **kwargs):
        # Disable non-authors to update order
        obj = self.get_object()
        if obj.author != self.request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class OrderCreateView(LoginRequiredMixin, CreateView):
    model = Order
    template_name = 'order_new.html'
    fields = ('title', 'body', 'flair', 't1', 't1ce', 't2')
    login_url = 'login' # redirect to OUR CUSTOM login url

    def form_valid(self, form): # automatically set author
        form.instance.author = self.request.user # requires user field
        return super().form_valid(form) # so anonymous --> error
