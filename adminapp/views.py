from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from products.models import Category, SubCategory, SubSubCategory, Attribute, Product, ProductAttribute, ProductImage
from .forms import (
    CategoryForm, SubCategoryForm, SubSubCategoryForm, 
    AttributeForm, AttributeEditForm
)
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
User = get_user_model()

def admin_login(request):
    if request.user.is_authenticated and request.user.role == 'admin':
        return redirect('admin_dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.role == 'admin':
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Invalid credentials or not an admin account.", extra_tags='admin')
    
    return render(request, 'adminapp/admin_login.html')
def admin_logout(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, "Logged out successfully.", extra_tags='admin')
    return redirect('admin_login')

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('admin_login')
        if request.user.role != 'admin':
            return render(request, '403.html')
        return view_func(request, *args, **kwargs)
    return wrapper

@admin_required
def admin_dashboard(request):
    # Get counts from database
    category_count = Category.objects.count()
    subcategory_count = SubCategory.objects.count()
    
    context = {
        'category_count': category_count,
        'subcategory_count': subcategory_count,
    }
    return render(request, 'adminapp/dashboard.html', context)
@admin_required
def manage_users(request):
    users = User.objects.filter(role='user').order_by('-date_joined')
    return render(request, 'adminapp/manage_users.html', {
        'users': users
    })


def toggle_user_status(request, pk):
    user = get_object_or_404(User, pk=pk)
    
    if user.role == 'admin':
        messages.error(request, "Cannot modify status of admin accounts.", extra_tags='admin')
    elif user == request.user:
        messages.error(request, "You cannot suspend your own account!", extra_tags='admin')
    else:
        user.is_active = not user.is_active
        user.save()
        status = "activated" if user.is_active else "suspended"
        messages.success(request, f'User {user.username} has been {status}.', extra_tags='admin')
    
    return redirect('manage_users')


def delete_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        if user.role == 'admin':
            messages.error(request, "Cannot delete admin accounts.", extra_tags='admin')
        elif user == request.user:
            messages.error(request, "You cannot delete your own account!", extra_tags='admin')
        else:
            username = user.username
            user.delete()
            messages.success(request, f'User {username} has been deleted.', extra_tags='admin')
        return redirect('manage_users')
    
    return render(request, 'adminapp/confirm_delete.html', {
        'object': user,
        'title': 'Confirm Delete User'
    })
@admin_required
def manage_categories(request):
    categories = Category.objects.prefetch_related(
        'subcategories__subsubcategories'
    ).all()
    return render(request, 'adminapp/manage_categories.html', {
        'categories': categories
    })

def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category added successfully!')
            return redirect('manage_categories')
    else:
        form = CategoryForm()
    return render(request, 'adminapp/category_form.html', {
        'form': form,
        'title': 'Add Category'
    })

def edit_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('manage_categories')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'adminapp/category_form.html', {
        'form': form,
        'title': 'Edit Category'
    })

def add_subcategory(request):
    if request.method == 'POST':
        form = SubCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subcategory added successfully!')
            return redirect('manage_categories')
    else:
        form = SubCategoryForm()
    return render(request, 'adminapp/category_form.html', {
        'form': form,
        'title': 'Add Subcategory'
    })

def edit_subcategory(request, pk):
    subcategory = get_object_or_404(SubCategory, pk=pk)
    if request.method == 'POST':
        form = SubCategoryForm(request.POST, instance=subcategory)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subcategory updated successfully!')
            return redirect('manage_categories')
    else:
        form = SubCategoryForm(instance=subcategory)
    return render(request, 'adminapp/category_form.html', {
        'form': form,
        'title': 'Edit Subcategory'
    })

def add_subsubcategory(request):
    if request.method == 'POST':
        form = SubSubCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sub-subcategory added successfully!')
            return redirect('manage_categories')
    else:
        form = SubSubCategoryForm()
    return render(request, 'adminapp/category_form.html', {
        'form': form,
        'title': 'Add Sub-subcategory'
    })

def edit_subsubcategory(request, pk):
    subsubcategory = get_object_or_404(SubSubCategory, pk=pk)
    if request.method == 'POST':
        form = SubSubCategoryForm(request.POST, instance=subsubcategory)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sub-subcategory updated successfully!')
            return redirect('manage_categories')
    else:
        form = SubSubCategoryForm(instance=subsubcategory)
    return render(request, 'adminapp/category_form.html', {
        'form': form,
        'title': 'Edit Sub-subcategory'
    })

def add_attribute(request):
    if request.method == 'POST':
        form = AttributeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Attribute added successfully!')
            return redirect('manage_categories')
    else:
        form = AttributeForm()
    return render(request, 'adminapp/attribute_form.html', {
        'form': form,
        'title': 'Add Attribute'
    })

def edit_attribute(request, pk):
    attribute = get_object_or_404(Attribute, pk=pk)
    if request.method == 'POST':
        form = AttributeEditForm(request.POST, instance=attribute)
        if form.is_valid():
            form.save()
            messages.success(request, 'Attribute updated successfully!')
            return redirect('manage_categories')
    else:
        form = AttributeEditForm(instance=attribute)
    return render(request, 'adminapp/attribute_form.html', {
        'form': form,
        'title': 'Edit Attribute'
    })
@admin_required
def manage_products(request):
    products = Product.objects.select_related(
        'category', 'subcategory', 'subsubcategory'
    ).prefetch_related(
        'attributes', 'images'
    ).all().order_by('-created_at')

    # Optional filtering/search functionality
    category_id = request.GET.get('category')
    search_query = request.GET.get('q')
    
    if category_id:
        products = products.filter(category_id=category_id)
    if search_query:
        products = products.filter(name__icontains=search_query)

    categories = Category.objects.all()
    
    return render(request, 'adminapp/manage_products.html', {
        'products': products,
        'categories': categories,
        'selected_category': int(category_id) if category_id else None,
        'search_query': search_query or ''
    })

@admin_required
def product_detail_admin(request, pk):
    product = get_object_or_404(
        Product.objects.select_related(
            'category', 'subcategory', 'subsubcategory'
        ).prefetch_related(
            'attributes', 'images'
        ),
        pk=pk
    )
    
    return render(request, 'adminapp/product_detail_admin.html', {
        'product': product,
    })

@admin_required
def toggle_product_status(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.is_active = not product.is_active
    product.save()
    status = "activated" if product.is_active else "deactivated"
    messages.success(request, f'Product {product.name} has been {status}.', extra_tags='admin')
    return redirect('manage_products')

@admin_required
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Product {product_name} has been deleted.', extra_tags='admin')
        return redirect('manage_products')
    
    return render(request, 'adminapp/confirm_delete.html', {
        'object': product,
        'title': 'Confirm Delete Product'
    })