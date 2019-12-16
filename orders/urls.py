from django.urls import path

from .views import (
    OrderListView,
    OrderUpdateView,
    OrderDetailView,
    OrderDeleteView,
    OrderCreateView,
    download_file_view,
)

urlpatterns = [
    path('new/', OrderCreateView.as_view(), name='order_new'),
    path('<int:pk>/download/', download_file_view, name='order_download'),
    path('<int:pk>/edit/', OrderUpdateView.as_view(), name='order_edit'),
    path('<int:pk>/', OrderDetailView.as_view(), name='order_detail'),
    path('<int:pk>/delete/', OrderDeleteView.as_view(), name='order_delete'),
    path('', OrderListView.as_view(), name='order_list'),
]
