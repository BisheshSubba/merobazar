from django.urls import path
from . import views

urlpatterns = [
    path('activate/<uidb64>/<token>/', views.activate_view, name='activate'),
    path('register/', views.register_view, name='user_register'),
    path('login/', views.login_view, name='user_login'),
    path('', views.user_dashboard, name='user_dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/products/', views.user_products_view, name='user_products'),
    path('search/', views.search_products, name='search_products'),
    path('my-orders/', views.my_orders_view, name='my_orders'),
    path('orders-received/', views.orders_received_view, name='orders_received'),
    path('order/<int:order_id>/', views.order_detail_view, name='order_detail'),
    path('landing_page/', views.landing_page, name='landing'),
]
 