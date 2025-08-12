from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('subcategory/<int:subcategory_id>/', views.products_by_subcategory, name='products_by_subcategory'),
    path('category/<int:category_id>/', views.products_by_category, name='products_by_category'),
    path('subsubcategory/<int:subsubcategory_id>/', views.products_by_subsubcategory, name='products_by_subsubcategory'),
    path('get_category_from_subcategory/', views.get_category_from_subcategory, name='get_category_from_subcategory'),
    path('get-subcategories/', views.get_subcategories, name='get_subcategories'),
    path('get-subsubcategories/', views.get_subsubcategories, name='get_subsubcategories'),
    path('create/', views.create_product, name='create_product'),
    path('product/<int:pk>/update/', views.update_product, name='update_product'),
    path('delete/<int:pk>/', views.delete_product, name='delete_product'),
    path('product/<int:pk>/', views.product_details, name='product_details'),
    path('mark_as_sold/<int:product_id>/', views.mark_as_sold, name='mark_as_sold'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('wishlist/check/<int:product_id>/', views.check_wishlist, name='check_wishlist'),
    path('cart/', views.cart_view, name='cart_view'),
    path('wishlist/', views.wishlist_view, name='wishlist_view'),
    path('cart/check/<int:product_id>/', views.check_cart_status, name='check_cart_status'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_cart_item, name='remove_cart_item'),
    path('wishlist/count/', views.wishlist_count, name='wishlist_count'),
    path('cart/count/', views.cart_count, name='cart_count'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('order/success/<int:order_id>/', views.order_success, name='order_success'),
    path('order/<int:order_id>/cancel/', views.cancel_order_view, name='cancel_order'),
]