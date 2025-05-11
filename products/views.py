from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .forms import ProductForm, ProductImageForm
from .models import SubCategory, Product, Category,ProductImage
from collections import defaultdict



def products_by_subcategory(request, subcategory_id):
    subcategory = get_object_or_404(SubCategory, id=subcategory_id)
    products = Product.objects.filter(subcategory=subcategory, is_available=True)
    
    context = {
        'subcategory': subcategory,
        'products': products,
        'categories': Category.objects.prefetch_related('subcategories').all()
    }
    return render(request, 'products/products_by_subcategory.html', context)

def products_by_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category, is_available=True)
    
    context = {
        'category': category,
        'products': products,
        'categories': Category.objects.prefetch_related('subcategories').all()
    }
    return render(request, 'products/products_by_category.html', context)

def get_category_from_subcategory(request):
    subcategory_id = request.GET.get('subcategory_id')
    try:
        subcategory = SubCategory.objects.get(id=subcategory_id)
        return JsonResponse({'category_id': subcategory.category.id})
    except SubCategory.DoesNotExist:
        return JsonResponse({'error': 'Subcategory not found'}, status=404)

@login_required
def add_product(request):
    if request.method == 'POST':
        product_form = ProductForm(request.POST)
        image_form = ProductImageForm(request.POST, request.FILES)
        
        if product_form.is_valid() and image_form.is_valid():
            product = product_form.save(commit=False)
            product.user = request.user
            product.save()
            
            files = request.FILES.getlist('images')
            for f in files:
                ProductImage.objects.create(product=product, image=f)
            
            return redirect('user_dashboard')
    else:
        product_form = ProductForm()
        image_form = ProductImageForm()
    
    return render(request, 'products/add_product.html', {
        'product_form': product_form,
        'image_form': image_form,
        'categories': Category.objects.all(),
    })

def get_subcategories(request):
    category_id = request.GET.get('category_id')
    subcategories = SubCategory.objects.filter(category_id=category_id).order_by('name')
    data = [{'id': sub.id, 'name': sub.name} for sub in subcategories]
    return JsonResponse(data, safe=False)

def product_details(request, pk):
    product = get_object_or_404(Product, pk=pk)
    related_products = Product.objects.filter(
        category=product.category,
        is_available=True
    ).exclude(pk=product.pk).order_by('?')[:4]  # Get 4 random related products
    
    return render(request, 'products/product_detail.html', {
        'product': product,
        'related_products': related_products,
        'categories': Category.objects.all()  # Include if needed for navigation
    })