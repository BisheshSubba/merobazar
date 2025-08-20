from django.urls import path
from . import views

urlpatterns = [
    path('track-interaction/', views.track_interaction, name='track_interaction'),
    path('recommendations/', views.get_recommendations, name='get_recommendations'),
    path('similar-products/<int:product_id>/', views.get_similar_products, name='get_similar_products'),
    path('popular-products/', views.get_popular_products, name='get_popular_products'),
]