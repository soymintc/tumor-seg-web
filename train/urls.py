from django.urls import path

from .views import (
    TrainCreateView, 
    train_detail_view, 
    train_kill_view,
    train_log_view,
)

urlpatterns = [
    path('new/', TrainCreateView.as_view(), name='train_new'),
    path('<int:pk>/detail', train_detail_view, name='train_detail'),
    path('<int:pk>/kill', train_kill_view, name='train_kill'),
    path('<int:pk>/log', train_log_view, name='train_log'),
]
