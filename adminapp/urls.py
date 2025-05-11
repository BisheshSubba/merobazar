from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.admin_login, name='admin_login'),
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('logout/', views.admin_logout, name='admin_logout'),
    path('users/', views.manage_users, name='manage_users'),
    path('users/toggle-status/<int:pk>/', views.toggle_user_status, name='toggle_user_status'),
    path('users/delete/<int:pk>/', views.delete_user, name='delete_user'),
    path('categories/', views.manage_categories, name='manage_categories'),
    path('categories/add/', views.add_category, name='add_category'),
    path('categories/edit/<int:pk>/', views.edit_category, name='edit_category'),
    path('categories/delete/<int:pk>/', views.delete_category, name='delete_category'),
   
    path('subcategories/', views.manage_subcategories, name='manage_subcategories'),
    path('subcategories/add/', views.add_subcategory, name='add_subcategory'),
    path('subcategories/edit/<int:pk>/', views.edit_subcategory, name='edit_subcategory'),
    path('subcategories/delete/<int:pk>/', views.delete_subcategory, name='delete_subcategory'),

    path('subsubcategories/', views.manage_subsubcategories, name='manage_subsubcategories'),
    path('subsubcategories/add/', views.add_subsubcategory, name='add_subsubcategory'),
    path('subsubcategories/edit/<int:pk>/', views.edit_subsubcategory, name='edit_subsubcategory'),
    path('subsubcategories/delete/<int:pk>/', views.delete_subsubcategory, name='delete_subsubcategory'),
]
