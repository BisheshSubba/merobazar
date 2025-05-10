from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='user_register'),
    path('login/', views.login_view, name='user_login'),
    path('', views.user_dashboard, name='user_dashboard'),
    path('logout/', views.logout_view, name='logout'),

]
 