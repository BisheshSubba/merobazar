from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .forms import ProductForm, ProductImageForm
from .models import SubCategory, Product, Category,ProductImage



def products_by_subcategory(request, subcategory_id):
    subcategory = get_object_or_404(SubCategory, id=subcategory_id)
    products = Product.objects.filter(subcategory=subcategory, is_available=True)
    
    context = {
        'subcategory': subcategory,
        'products': products,
        'categories': Category.objects.prefetch_related('subcategories').all()
    }
    return render(request, 'products/products_by_subcategory.html', context)

@login_required
def add_product(request):
    if request.method == 'POST':
        product_form = ProductForm(request.POST)
        image_form = ProductImageForm(request.POST, request.FILES)
        
        if product_form.is_valid() and image_form.is_valid():
            product = product_form.save(commit=False)
            product.user = request.user
            product.save()
            
            # Handle multiple image uploads
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
    })

def get_subcategories(request):
    category_id = request.GET.get('category_id')
    subcategories = SubCategory.objects.filter(category_id=category_id).values('id', 'name')
    return JsonResponse(list(subcategories), safe=False)