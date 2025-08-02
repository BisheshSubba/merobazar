from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from tempfile import mkdtemp
from django.core.files.storage import FileSystemStorage
from django.core.files import File
from django.core.signals import request_finished
from django.dispatch import receiver
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.contrib.sessions.models import Session
from django.db import close_old_connections
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from .models import Category, SubCategory, SubSubCategory, Attribute, Product, ProductAttribute, ProductImage, Wishlist, Cart
from .forms import ProductBasicInfoForm, ProductCategoryForm, ProductFinalDetailsForm, ProductImageForm, ProductAttributeForm,ProductUpdateForm
import logging

# Set up logging
logger = logging.getLogger(__name__)
TEMP_IMAGE_STORAGE = FileSystemStorage(location=mkdtemp())

@login_required
def create_product(request):
    # Initialize/reset session if needed
    if request.GET.get('reset') or 'product_data' not in request.session:
        request.session['product_data'] = {
            'step1': {'temp_images': []},
            'step2': {},
            'step3': {},
            'step4': {}
        }
        request.session['current_step'] = 1
        request.session.modified = True
        logger.info("Session initialized/reset")

    current_step = request.session.get('current_step', 1)
    product_data = request.session['product_data']

    try:
        # Handle POST requests
        if request.method == 'POST':
            if 'previous_step' in request.POST:
                current_step = max(1, current_step - 1)
                request.session['current_step'] = current_step
                request.session.modified = True
                logger.info(f"Moving to previous step: {current_step}")
                return redirect('products:create_product')

            # Process current step
            if current_step == 1:
                return process_step1(request, product_data)
            elif current_step == 2:
                return process_step2(request, product_data)
            elif current_step == 3:
                return process_step3(request, product_data)
            elif current_step == 4:
                return process_step4(request, product_data)

        # Render current step
        if current_step == 1:
            return render_step1(request, product_data)
        elif current_step == 2:
            return render_step2(request, product_data)
        elif current_step == 3:
            return render_step3(request, product_data)
        elif current_step == 4:
            return render_step4(request, product_data)

    except Exception as e:
        logger.error(f"Error in create_product: {str(e)}", exc_info=True)
        # Clean up session and temporary files
        cleanup_failed_process(request)
        # Redirect to start with fresh session - FIXED VERSION
        base_url = reverse('products:create_product')
        return HttpResponseRedirect(f"{base_url}?reset=1")

def cleanup_failed_process(request):
    """Clean up session and temporary files when process fails"""
    if 'product_data' in request.session:
        # Clean up temp images
        temp_images = request.session['product_data'].get('step1', {}).get('temp_images', [])
        for temp_path in temp_images:
            try:
                if TEMP_IMAGE_STORAGE.exists(temp_path):
                    TEMP_IMAGE_STORAGE.delete(temp_path)
                    logger.info(f"Deleted temp image: {temp_path}")
            except Exception as e:
                logger.error(f"Failed to delete temp image {temp_path}: {str(e)}")
        
        # Clear session data
        request.session.pop('product_data', None)
        request.session.pop('current_step', None)
        request.session.modified = True
        logger.info("Cleaned up failed process")

import os
from django.core.files.storage import default_storage

def process_step1(request, product_data):
    print("\n=== PROCESSING STEP 1 ===")
    form = ProductBasicInfoForm(request.POST, prefix='step1')
    image_form = ProductImageForm(request.POST, request.FILES, prefix='images')

    if form.is_valid() and image_form.is_valid():
        print("\nSTEP 1 FORM VALID")
        step1_data = {
            'name': form.cleaned_data['name'],
            'description': form.cleaned_data['description']
        }
        print(f"Saving step1 data: {step1_data}")
        product_data['step1'].update(step1_data)

        # Handle images with improved file handling
        if 'images-images' in request.FILES:
            print(f"\nProcessing {len(request.FILES.getlist('images-images'))} uploaded images")
            product_data['step1']['temp_images'] = []
            
            for f in request.FILES.getlist('images-images'):
                try:
                    # Sanitize the filename
                    original_name = f.name
                    clean_name = os.path.basename(original_name)  # Remove any path information
                    clean_name = default_storage.get_valid_name(clean_name)  # Get a safe filename
                    
                    print(f"Original filename: {original_name}, Cleaned filename: {clean_name}")
                    
                    # Save to temporary storage
                    temp_path = TEMP_IMAGE_STORAGE.save(f"temp_{clean_name}", f)
                    product_data['step1']['temp_images'].append(temp_path)
                    
                    print(f"Saved temp image: {temp_path}")
                except Exception as e:
                    print(f"Error processing image {f.name}: {str(e)}")
                    # Clean up any already saved temp images
                    for temp_path in product_data['step1']['temp_images']:
                        try:
                            if TEMP_IMAGE_STORAGE.exists(temp_path):
                                TEMP_IMAGE_STORAGE.delete(temp_path)
                        except:
                            pass
                    # Re-raise the error to be caught by the outer handler
                    raise

        request.session['current_step'] = 2
        request.session.modified = True
        print("\nSTEP 1 COMPLETE - MOVING TO STEP 2")
        print(f"Updated session data: {request.session['product_data']}")
        return redirect('products:create_product')

    print("\nSTEP 1 FORM INVALID")
    print("Basic info form errors:", form.errors)
    print("Image form errors:", image_form.errors if image_form else None)
    return render_step1(request, product_data, form, image_form)

def process_step2(request, product_data):
    print("\n=== PROCESSING STEP 2 ===")
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
        print("\nSTEP 2 FORM VALID")
        step2_data = {
            'category_id': form.cleaned_data['category'].id,
            'subcategory_id': form.cleaned_data['subcategory'].id if form.cleaned_data['subcategory'] else None,
            'subsubcategory_id': form.cleaned_data['subsubcategory'].id if form.cleaned_data['subsubcategory'] else None
        }
        print(f"Saving step2 data: {step2_data}")
        product_data['step2'] = step2_data

        request.session['current_step'] = 3
        request.session.modified = True
        print("\nSTEP 2 COMPLETE - MOVING TO STEP 3")
        return redirect('products:create_product')

    print("\nSTEP 2 FORM INVALID")
    print("Form errors:", form.errors)
    print("Cleaned data:", form.cleaned_data)
    
    # Get selected values from POST to repopulate form
    selected_category = request.POST.get('step2-category')
    selected_subcategory = request.POST.get('step2-subcategory')
    
    return render_step2(request, product_data, form, selected_category, selected_subcategory)

def process_step3(request, product_data):
    print("\n=== PROCESSING STEP 3 ===")
    step2_data = product_data['step2']
    content_type, object_id = get_content_type_and_id(step2_data)
    print(f"Content type: {content_type}, Object ID: {object_id}")

    attributes = Attribute.objects.filter(
        content_type=content_type,
        object_id=object_id
    ) if content_type and object_id else []
    print(f"Found {len(attributes)} attributes for this category")

    form = ProductAttributeForm(request.POST, prefix='step3', attributes=attributes)
    
    if form.is_valid():
        print("\nSTEP 3 FORM VALID")
        attributes_data = {}
        for attr in attributes:
            field_name = f'attribute_{attr.id}'
            attributes_data[str(attr.id)] = form.cleaned_data[field_name]
            print(f"  {attr.name}: {form.cleaned_data[field_name]}")

        product_data['step3'] = attributes_data
        request.session['current_step'] = 4
        request.session.modified = True
        print("\nSTEP 3 COMPLETE - MOVING TO STEP 4")
        print(f"Saved attributes: {attributes_data}")
        return redirect('products:create_product')

    print("\nSTEP 3 FORM INVALID")
    print("Form errors:", form.errors)
    print("Cleaned data:", form.cleaned_data)
    return render_step3(request, product_data, form, attributes)

@transaction.atomic
def process_step4(request, product_data):
    form = ProductFinalDetailsForm(request.POST, prefix='step4')
    
    if form.is_valid():
        print("\n=== ATTEMPTING PRODUCT CREATION ===")
        try:
            # Create product - add debug prints
            print("Creating product instance...")
            product = Product.objects.create(
                user=request.user,
                name=product_data['step1']['name'],
                description=product_data['step1']['description'],
                category_id=product_data['step2']['category_id'],
                subcategory_id=product_data['step2']['subcategory_id'],
                subsubcategory_id=product_data['step2']['subsubcategory_id'],
                **form.cleaned_data
            )
            print(f"Product created with ID: {product.id}")

            # Create attributes - add debug prints
            print("Creating attributes...")
            for attr_id, value in product_data['step3'].items():
                print(f"Processing attribute {attr_id} with value {value}")
                attribute = Attribute.objects.get(id=attr_id)
                ProductAttribute.objects.create(
                    product=product,
                    attribute=attribute,
                    **{f'value_{attribute.data_type}': value}
                )

            # Handle images - add debug prints
            print("Processing images...")
            temp_images = product_data['step1'].get('temp_images', [])
            for idx, temp_path in enumerate(temp_images):
                print(f"Processing image {temp_path}")
                try:
                    filename = os.path.basename(temp_path)
                    with TEMP_IMAGE_STORAGE.open(temp_path) as f:
                        django_file = File(f, name=filename)
                        ProductImage.objects.create(
                            product=product,
                            image=django_file,
                            is_primary=(idx == 0)
                        )
                    TEMP_IMAGE_STORAGE.delete(temp_path)
                except Exception as e:
                    print(f"IMAGE PROCESSING FAILED: {str(e)}")
                    raise

            # Explicit success check
            if not product.pk:
                raise ValueError("Product creation failed - no PK assigned")

            # Clean session only AFTER successful creation
            request.session.pop('product_data', None)
            request.session.pop('current_step', None)
            
            print("=== PRODUCT CREATION SUCCESSFUL ===")
            return redirect('products:product_details', pk=product.pk)

        except Exception as e:
            print(f"!!! PRODUCT CREATION FAILED: {str(e)}")
            logger.error(f"Transaction failed - DETAILS: {str(e)}", exc_info=True)
            transaction.set_rollback(True)
            raise  # Re-raise to see in console

    else:
        print("\nSTEP 4 FORM INVALID")
        print(form.errors)
    
    return render_step4(request, product_data, form)

def get_content_type_and_id(step2_data):
    if step2_data.get('subsubcategory_id'):
        return ContentType.objects.get_for_model(SubSubCategory), step2_data['subsubcategory_id']
    elif step2_data.get('subcategory_id'):
        return ContentType.objects.get_for_model(SubCategory), step2_data['subcategory_id']
    elif step2_data.get('category_id'):
        return ContentType.objects.get_for_model(Category), step2_data['category_id']
    return None, None

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
        'total_steps': 4
    })

def render_step2(request, product_data, form=None, selected_category=None, selected_subcategory=None):
    # Get all categories
    categories = Category.objects.all()
    
    # Initialize form if not provided
    if form is None:
        initial_data = {
            'category': product_data['step2'].get('category_id'),
            'subcategory': product_data['step2'].get('subcategory_id'),
            'subsubcategory': product_data['step2'].get('subsubcategory_id')
        }
        form = ProductCategoryForm(prefix='step2', initial=initial_data)
        
        # Manually set the querysets based on initial data
        if initial_data['category']:
            form.fields['subcategory'].queryset = SubCategory.objects.filter(
                category_id=initial_data['category']
            )
        if initial_data['subcategory']:
            form.fields['subsubcategory'].queryset = SubSubCategory.objects.filter(
                subcategory_id=initial_data['subcategory']
            )
    
    # Get selected values from form data if not provided
    if selected_category is None:
        selected_category = form['category'].value()
    if selected_subcategory is None:
        selected_subcategory = form['subcategory'].value()
    
    # Get subcategories and subsubcategories for template
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
        'total_steps': 4
    })
def render_step3(request, product_data, form=None, attributes=None):
    if attributes is None:
        step2_data = product_data['step2']
        content_type, object_id = get_content_type_and_id(step2_data)
        attributes = Attribute.objects.filter(
            content_type=content_type,
            object_id=object_id
        ) if content_type and object_id else []
    
    if form is None:
        form = ProductAttributeForm(prefix='step3', attributes=attributes)
    
    return render(request, 'products/step3_attributes.html', {
        'form': form,
        'attributes': attributes,
        'current_step': 3,
        'total_steps': 4
    })

def render_step4(request, product_data, form=None):
    if form is None:
        form = ProductFinalDetailsForm(prefix='step4', initial=product_data.get('step4', {}))
    
    return render(request, 'products/step4_final_details.html', {
        'form': form,
        'current_step': 4,
        'total_steps': 4
    })


def products_by_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products_list = Product.objects.filter(category=category, is_active=True)
    paginator = Paginator(products_list, 12)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    
    context = {
        'page_title': category.name,
        'current_category': category,
        'products': products,
        'subcategories': category.subcategories.all(),
        'subcategory_url_name': 'products:products_by_subcategory',
        'breadcrumbs': []
    }
    return render(request, 'products/category_view.html', context)

def products_by_subcategory(request, subcategory_id):
    subcategory = get_object_or_404(SubCategory, id=subcategory_id)
    products_list = Product.objects.filter(subcategory=subcategory, is_active=True)
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
        ]
    }
    return render(request, 'products/category_view.html', context)

def products_by_subsubcategory(request, subsubcategory_id):
    subsubcategory = get_object_or_404(SubSubCategory, id=subsubcategory_id)
    products_list = Product.objects.filter(subsubcategory=subsubcategory, is_active=True)
    paginator = Paginator(products_list, 12)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    
    context = {
        'page_title': subsubcategory.name,
        'current_category': subsubcategory,
        'products': products,
        'subcategories': None,  # No further subcategories
        'breadcrumbs': [
            {'name': subsubcategory.subcategory.category.name, 'url': reverse('products:products_by_category', args=[subsubcategory.subcategory.category.id])},
            {'name': subsubcategory.subcategory.name, 'url': reverse('products:products_by_subcategory', args=[subsubcategory.subcategory.id])}
        ]
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