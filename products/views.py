from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from tempfile import mkdtemp
from django.core.files.storage import FileSystemStorage
from django.core.files import File
from decouple import config
import os
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
import requests
from django.core.files.storage import default_storage
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db import close_old_connections
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from .models import Category, SubCategory, SubSubCategory, Product, ProductImage, Wishlist, Cart, Order, OrderItem, Sale
from .forms import ProductBasicInfoForm, ProductCategoryForm, ProductFinalDetailsForm, ProductImageForm, ProductUpdateForm
import logging

logger = logging.getLogger(__name__)
TEMP_IMAGE_STORAGE = FileSystemStorage(location=mkdtemp())

@login_required
def create_product(request):
    if request.GET.get('reset') or 'product_data' not in request.session:
        request.session['product_data'] = {
            'step1': {'temp_images': []},
            'step2': {},
            'step4': {}
        }
        request.session['current_step'] = 1
        request.session.modified = True
        logger.info("Session initialized/reset")

    current_step = request.session.get('current_step', 1)
    product_data = request.session['product_data']

    try:
        if request.method == 'POST':
            if 'previous_step' in request.POST:
                current_step = max(1, current_step - 1)
                request.session['current_step'] = current_step
                request.session.modified = True
                logger.info(f"Moving to previous step: {current_step}")
                return redirect('products:create_product')

            if current_step == 1:
                return process_step1(request, product_data)
            elif current_step == 2:
                return process_step2(request, product_data)
            elif current_step == 4:
                return process_step4(request, product_data)

        if current_step == 1:
            return render_step1(request, product_data)
        elif current_step == 2:
            return render_step2(request, product_data)
        elif current_step == 4:
            return render_step4(request, product_data)

    except Exception as e:
        logger.error(f"Error in create_product: {str(e)}", exc_info=True)
        cleanup_failed_process(request)
        base_url = reverse('products:create_product')
        return HttpResponseRedirect(f"{base_url}?reset=1")

def cleanup_failed_process(request):
    if 'product_data' in request.session:
        temp_images = request.session['product_data'].get('step1', {}).get('temp_images', [])
        for temp_path in temp_images:
            try:
                if TEMP_IMAGE_STORAGE.exists(temp_path):
                    TEMP_IMAGE_STORAGE.delete(temp_path)
                    logger.info(f"Deleted temp image: {temp_path}")
            except Exception as e:
                logger.error(f"Failed to delete temp image {temp_path}: {str(e)}")
        request.session.pop('product_data', None)
        request.session.pop('current_step', None)
        request.session.modified = True
        logger.info("Cleaned up failed process")

def process_step1(request, product_data):
    form = ProductBasicInfoForm(request.POST, prefix='step1')
    image_form = ProductImageForm(request.POST, request.FILES, prefix='images')

    if form.is_valid() and image_form.is_valid():
        step1_data = {
            'name': form.cleaned_data['name'],
            'description': form.cleaned_data['description']
        }
        product_data['step1'].update(step1_data)

        if 'images-images' in request.FILES:
            product_data['step1']['temp_images'] = []
            for f in request.FILES.getlist('images-images'):
                original_name = f.name
                clean_name = os.path.basename(original_name)
                clean_name = default_storage.get_valid_name(clean_name)
                temp_path = TEMP_IMAGE_STORAGE.save(f"temp_{clean_name}", f)
                product_data['step1']['temp_images'].append(temp_path)

        request.session['current_step'] = 2
        request.session.modified = True
        return redirect('products:create_product')

    return render_step1(request, product_data, form, image_form)

def process_step2(request, product_data):
    form = ProductCategoryForm(
        request.POST or None,
        prefix='step2',
        initial={
            'category': product_data['step2'].get('category_id'),
            'subcategory': product_data['step2'].get('subcategory_id'),
            'subsubcategory': product_data['step2'].get('subsubcategory_id')
        }
    )
    
    if form.is_valid():
        step2_data = {
            'category_id': form.cleaned_data['category'].id,
            'subcategory_id': form.cleaned_data['subcategory'].id if form.cleaned_data['subcategory'] else None,
            'subsubcategory_id': form.cleaned_data['subsubcategory'].id if form.cleaned_data['subsubcategory'] else None
        }
        product_data['step2'] = step2_data

        # Skip step 3 (attributes) and go directly to step 4
        request.session['current_step'] = 4
        request.session.modified = True
        return redirect('products:create_product')

    selected_category = request.POST.get('step2-category')
    selected_subcategory = request.POST.get('step2-subcategory')

    return render_step2(request, product_data, form, selected_category, selected_subcategory)

@transaction.atomic
def process_step4(request, product_data):
    form = ProductFinalDetailsForm(request.POST, prefix='step4')
    
    if form.is_valid():
        try:
            product = Product.objects.create(
                user=request.user,
                name=product_data['step1']['name'],
                description=product_data['step1']['description'],
                category_id=product_data['step2']['category_id'],
                subcategory_id=product_data['step2']['subcategory_id'],
                subsubcategory_id=product_data['step2']['subsubcategory_id'],
                **form.cleaned_data
            )

            temp_images = product_data['step1'].get('temp_images', [])
            for idx, temp_path in enumerate(temp_images):
                filename = os.path.basename(temp_path)
                with TEMP_IMAGE_STORAGE.open(temp_path) as f:
                    django_file = File(f, name=filename)
                    ProductImage.objects.create(
                        product=product,
                        image=django_file,
                        is_primary=(idx == 0)
                    )
                TEMP_IMAGE_STORAGE.delete(temp_path)

            request.session.pop('product_data', None)
            request.session.pop('current_step', None)

            return redirect('products:product_details', pk=product.pk)

        except Exception as e:
            logger.error(f"Transaction failed - DETAILS: {str(e)}", exc_info=True)
            transaction.set_rollback(True)
            raise

    return render_step4(request, product_data, form)

def render_step1(request, product_data, form=None, image_form=None):
    if form is None:
        form = ProductBasicInfoForm(prefix='step1', initial={
            'name': product_data['step1'].get('name', ''),
            'description': product_data['step1'].get('description', '')
        })
    if image_form is None:
        image_form = ProductImageForm(prefix='images')
    return render(request, 'products/step1_basic_info.html', {
        'form': form,
        'image_form': image_form,
        'current_step': 1,
        'total_steps': 3  # changed from 4 to 3 steps now
    })

def render_step2(request, product_data, form=None, selected_category=None, selected_subcategory=None):
    categories = Category.objects.all()
    
    if form is None:
        initial_data = {
            'category': product_data['step2'].get('category_id'),
            'subcategory': product_data['step2'].get('subcategory_id'),
            'subsubcategory': product_data['step2'].get('subsubcategory_id')
        }
        form = ProductCategoryForm(prefix='step2', initial=initial_data)
        if initial_data['category']:
            form.fields['subcategory'].queryset = SubCategory.objects.filter(category_id=initial_data['category'])
        if initial_data['subcategory']:
            form.fields['subsubcategory'].queryset = SubSubCategory.objects.filter(subcategory_id=initial_data['subcategory'])
    
    if selected_category is None:
        selected_category = form['category'].value()
    if selected_subcategory is None:
        selected_subcategory = form['subcategory'].value()
    
    subcategories = SubCategory.objects.filter(category_id=selected_category) if selected_category else []
    subsubcategories = SubSubCategory.objects.filter(subcategory_id=selected_subcategory) if selected_subcategory else []
    
    return render(request, 'products/step2_category.html', {
        'form': form,
        'categories': categories,
        'subcategories': subcategories,
        'subsubcategories': subsubcategories,
        'selected_category': selected_category,
        'selected_subcategory': selected_subcategory,
        'current_step': 2,
        'total_steps': 3
    })

def render_step4(request, product_data, form=None):
    if form is None:
        form = ProductFinalDetailsForm(prefix='step4', initial=product_data.get('step4', {}))
    return render(request, 'products/step4_final_details.html', {
        'form': form,
        'current_step': 3,  # step 4 is now step 3
        'total_steps': 3
    })


def products_by_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products_list = Product.objects.filter(category=category, is_active=True)
    
    # Filtering logic
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort_by', 'newest')  # Default to newest first
    search_query = request.GET.get('search')
    
    if min_price:
        products_list = products_list.filter(price__gte=min_price)
    if max_price:
        products_list = products_list.filter(price__lte=max_price)
    if search_query:
        products_list = products_list.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # Sorting mapping
    sort_mapping = {
        'price_asc': 'price',
        'price_desc': '-price',
        'newest': '-created_at',
        'oldest': 'created_at',
    }
    order_by = sort_mapping.get(sort_by, '-created_at')
    products_list = products_list.order_by(order_by)
    
    paginator = Paginator(products_list, 12)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    
    context = {
        'page_title': category.name,
        'current_category': category,
        'products': products,
        'subcategories': category.subcategories.all(),
        'subcategory_url_name': 'products:products_by_subcategory',
        'breadcrumbs': [],
        'current_sort': order_by,  # Actual field name for display
        'applied_filters': {
            'min_price': min_price,
            'max_price': max_price,
            'search': search_query,
        }
    }
    return render(request, 'products/category_view.html', context)

def products_by_subcategory(request, subcategory_id):
    subcategory = get_object_or_404(SubCategory, id=subcategory_id)
    products_list = Product.objects.filter(subcategory=subcategory, is_active=True)
    
    # Filtering logic
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort_by', 'newest')
    search_query = request.GET.get('search')
    
    if min_price:
        products_list = products_list.filter(price__gte=min_price)
    if max_price:
        products_list = products_list.filter(price__lte=max_price)
    if search_query:
        products_list = products_list.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # Sorting mapping
    sort_mapping = {
        'price_asc': 'price',
        'price_desc': '-price',
        'newest': '-created_at',
        'oldest': 'created_at',
    }
    order_by = sort_mapping.get(sort_by, '-created_at')
    products_list = products_list.order_by(order_by)
    
    paginator = Paginator(products_list, 12)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    
    context = {
        'page_title': subcategory.name,
        'current_category': subcategory,
        'products': products,
        'subcategories': subcategory.subsubcategories.all(),
        'subcategory_url_name': 'products:products_by_subsubcategory',
        'breadcrumbs': [
            {'name': subcategory.category.name, 'url': reverse('products:products_by_category', args=[subcategory.category.id])}
        ],
        'current_sort': order_by,
        'applied_filters': {
            'min_price': min_price,
            'max_price': max_price,
            'search': search_query,
        }
    }
    return render(request, 'products/category_view.html', context)

def products_by_subsubcategory(request, subsubcategory_id):
    subsubcategory = get_object_or_404(SubSubCategory, id=subsubcategory_id)
    products_list = Product.objects.filter(subsubcategory=subsubcategory, is_active=True)
    
    # Filtering logic
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort_by', 'newest')
    search_query = request.GET.get('search')
    
    if min_price:
        products_list = products_list.filter(price__gte=min_price)
    if max_price:
        products_list = products_list.filter(price__lte=max_price)
    if search_query:
        products_list = products_list.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # Sorting mapping
    sort_mapping = {
        'price_asc': 'price',
        'price_desc': '-price',
        'newest': '-created_at',
        'oldest': 'created_at',
    }
    order_by = sort_mapping.get(sort_by, '-created_at')
    products_list = products_list.order_by(order_by)
    
    paginator = Paginator(products_list, 12)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    
    context = {
        'page_title': subsubcategory.name,
        'current_category': subsubcategory,
        'products': products,
        'subcategories': None,
        'breadcrumbs': [
            {'name': subsubcategory.subcategory.category.name, 'url': reverse('products:products_by_category', args=[subsubcategory.subcategory.category.id])},
            {'name': subsubcategory.subcategory.name, 'url': reverse('products:products_by_subcategory', args=[subsubcategory.subcategory.id])}
        ],
        'current_sort': order_by,
        'applied_filters': {
            'min_price': min_price,
            'max_price': max_price,
            'search': search_query,
        }
    }
    return render(request, 'products/category_view.html', context)
def get_category_from_subcategory(request):
    subcategory_id = request.GET.get('subcategory_id')
    try:
        subcategory = SubCategory.objects.get(id=subcategory_id)
        return JsonResponse({'category_id': subcategory.category.id})
    except SubCategory.DoesNotExist:
        return JsonResponse({'error': 'Subcategory not found'}, status=404)

def get_subcategories(request):
    category_id = request.GET.get('category_id')
    subcategories = SubCategory.objects.filter(category_id=category_id).order_by('name')
    data = [{'id': sub.id, 'name': sub.name} for sub in subcategories]
    return JsonResponse(data, safe=False)

def get_subsubcategories(request):
    subcategory_id = request.GET.get('subcategory_id')
    subsubcategories = SubSubCategory.objects.filter(subcategory_id=subcategory_id).order_by('name')
    data = [{'id': subsub.id, 'name': subsub.name} for subsub in subsubcategories]
    return JsonResponse(data, safe=False)

def product_details(request, pk):
    product = get_object_or_404(Product, pk=pk)
    related_products = Product.objects.filter(
        category=product.category
    ).exclude(id=product.id).order_by('?')[:4]
    
    # Get cart product IDs for the current user
    cart_product_ids = []
    if request.user.is_authenticated:
        cart_product_ids = request.user.cart_items.values_list('product_id', flat=True)
    
    return render(request, 'products/product_detail.html', {
        'product': product,
        'related_products': related_products,
        'cart_product_ids': cart_product_ids,
    })

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction

@login_required
def update_product(request, pk):
    product = get_object_or_404(Product, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = ProductUpdateForm(request.POST, instance=product)
        if form.is_valid():
            updated_product = form.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('products:product_details', pk=updated_product.id)
    else:
        form = ProductUpdateForm(instance=product)
    
    context = {
        'form': form,
        'product': product
    }
    return render(request, 'products/update_product.html', context)

@login_required
@require_POST
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk, user=request.user)
    
    try:
        # Delete the product and its related data
        product.delete()
        messages.success(request, 'Product deleted successfully!')
        return redirect('profile')  # Redirect to user profile after deletion
    except Exception as e:
        logger.error(f"Error deleting product {pk}: {str(e)}")
        messages.error(request, 'Failed to delete product. Please try again.')
        return redirect('products:product_details', pk=pk)

@login_required
@require_POST
def toggle_wishlist(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )
        
        if not created:
            wishlist_item.delete()
            
        return JsonResponse({
            'status': 'added' if created else 'removed',
            'in_wishlist': created,
            'wishlist_count': request.user.wishlist_items.count()
        })
    except Product.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Product not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
@login_required
def check_wishlist(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
        in_wishlist = Wishlist.objects.filter(
            user=request.user,
            product=product
        ).exists()
        return JsonResponse({'in_wishlist': in_wishlist})
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)
    
@login_required
@require_POST
def add_to_cart(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
        # Simply create the cart item if it doesn't exist
        Cart.objects.get_or_create(
            user=request.user,
            product=product
        )
        
        return JsonResponse({
            'status': 'success', 
            'message': 'Product added to cart',
            'cart_count': request.user.cart_items.count()
        })
    except Product.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Product not found'}, status=404)

@login_required
def cart_view(request):
    cart_items = request.user.cart_items.select_related('product').all()
    total = sum(item.product.price for item in cart_items)  # Sum all product prices
    
    return render(request, 'products/cart.html', {
        'cart_items': cart_items,
        'total': total
    })

@login_required
@require_POST
def update_cart_item(request, item_id):
    try:
        cart_item = Cart.objects.get(id=item_id, user=request.user)
        action = request.POST.get('action')
        
        if action == 'increase':
            if cart_item.quantity < cart_item.product.stock:
                cart_item.quantity += 1
                cart_item.save()
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()
                
        return JsonResponse({
            'status': 'success',
            'cart_count': request.user.cart_items.count()
        })
    except Cart.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Item not found'}, status=404)

@login_required
@require_POST
def remove_cart_item(request, item_id):
    try:
        cart_item = Cart.objects.get(id=item_id, user=request.user)
        cart_item.delete()
        return JsonResponse({
            'status': 'success',
            'cart_count': request.user.cart_items.count()
        })
    except Cart.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Item not found'}, status=404)
@login_required
def check_cart_status(request, product_id):
    in_cart = request.user.cart_items.filter(product_id=product_id).exists()
    return JsonResponse({'in_cart': in_cart})
@login_required
def wishlist_count(request):
    count = request.user.wishlist_items.count()
    return JsonResponse({'count': count})

@login_required
def cart_count(request):
    count = request.user.cart_items.count()
    return JsonResponse({'count': count})
@login_required
def wishlist_view(request):
    wishlist_items = request.user.wishlist_items.select_related('product').all()
    return render(request, 'products/wishlist.html', {
        'wishlist_items': wishlist_items
    })


def mark_as_sold(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id, user=request.user)
        
        # Mark product as inactive
        product.is_active = False
        product.save()
        
        # Create a sale record
        Sale.objects.create(
            product=product,
            buyer=None,
            sold_price=product.price,
            notes="Marked as sold by seller"
        )
        
        messages.success(request, f'"{product.name}" has been marked as sold.')
        return redirect('user_products')
    
    return redirect('user_products')

@login_required
def checkout_view(request):
    cart_items = request.user.cart_items.select_related('product')

    if not cart_items.exists():
        return redirect('products:cart_view')  # cart empty

    total_price = sum(item.product.price for item in cart_items)

    order = Order.objects.create(
        user=request.user,
        total_price=total_price,
        status='unpaid'
    )

    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            seller=item.product.user,  # or the correct attribute for the product seller
            price=item.product.price
        )

    cart_items.delete()

    return redirect('products:order_success', order_id=order.id)


@login_required
def order_success(request, order_id):
    order = Order.objects.get(id=order_id, user=request.user)
    return render(request, 'products/order_success.html', {'order': order})

@login_required
def cancel_order_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status != 'cancelled':
        order.status = 'cancelled'
        order.save()
        messages.success(request, f'Order #{order.id} has been cancelled.')
    else:
        messages.info(request, f'Order #{order.id} is already cancelled.')
    return redirect('my_orders')




@login_required
def initiate_khalti_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Compose a string of product names in the order
    product_names = ", ".join(item.product.name for item in order.items.all())
    if not product_names:
        product_names = f"Order #{order.id}"

    post_fields = {
        "return_url": request.build_absolute_uri('/products/payment-response/'),  # your callback URL
        "website_url": request.build_absolute_uri('/'),
        "amount": int(order.total_price * 100),  # amount in paisa
        "purchase_order_id": str(order.id),
        "purchase_order_name": product_names,
        "customer_info": {
            "name": request.user.username,
            "email": request.user.email,
            "phone": getattr(request.user, 'phone', 'N/A'),
        }
    }

    headers = {
        'Authorization': f"key {config('KHALTI_SECRET_KEY')}",
        'Content-Type': 'application/json',
    }

    response = requests.post('https://a.khalti.com/api/v2/epayment/initiate/', json=post_fields, headers=headers)
    data = response.json()

    if response.status_code == 200 and 'payment_url' in data:
        return redirect(data['payment_url'])
    else:
        messages.error(request, "Payment initiation failed. Please try again.")
        return redirect('products:order_success', order_id=order.id)
    
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from decouple import config
import requests
from .models import Sale, Order, OrderItem, Product

@csrf_exempt
@login_required
def payment_response(request):
    pidx = request.GET.get('pidx')
    purchase_order_id = request.GET.get('purchase_order_id')

    if not pidx or not purchase_order_id:
        messages.error(request, "Invalid payment response.")
        return redirect('my_orders')

    order = Order.objects.filter(id=purchase_order_id, user=request.user, status='unpaid').first()

    if not order:
        messages.error(request, "No unpaid order found.")
        return redirect('my_orders')

    headers = {
        'Authorization': f"key {config('KHALTI_SECRET_KEY')}",
        'Content-Type': 'application/json',
    }

    response = requests.post('https://a.khalti.com/api/v2/epayment/lookup/', json={"pidx": pidx}, headers=headers)
    data = response.json()

    if response.status_code == 200 and data.get('status') == 'Completed':
        # Mark order as paid
        order.status = 'paid'
        order.save()

        # For each item in the order:
        for item in order.items.all():
            # Mark the product as inactive (sold)
            product = item.product
            product.is_active = False
            product.save()

            # Create Sale record
            Sale.objects.create(
                product=product,
                buyer=order.user,
                sold_price=item.price,
                notes="Sold via Khalti payment"
            )

        messages.success(request, f"Payment successful. Order #{order.id} confirmed.")
    else:
        order.status = 'cancelled'
        order.save()
        messages.error(request, f"Payment failed or cancelled. Order #{order.id} cancelled.")

    return redirect('my_orders')
