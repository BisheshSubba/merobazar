from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from products.models import Category, SubCategory 
from .forms import CategoryForm, SubCategoryForm
from django.contrib.auth import authenticate, login
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

@admin_required
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

@admin_required
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
    categories = Category.objects.all().order_by('-created_at')
    return render(request, 'adminapp/manage_categories.html', {
        'categories': categories
    })
@admin_required
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category added successfully!', extra_tags='admin')
            return redirect('manage_categories')
    else:
        form = CategoryForm()
    
    return render(request, 'adminapp/category_form.html', {
        'form': form,
        'title': 'Add Category'
    })
@admin_required
def edit_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully!', extra_tags='admin')
            return redirect('manage_categories')
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'adminapp/category_form.html', {
        'form': form,
        'title': 'Edit Category'
    })
@admin_required
def delete_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        # Check if category has subcategories before deleting
        if category.subcategories.exists():
            messages.error(request, 'Cannot delete category with existing subcategories!', extra_tags='admin')
        else:
            category.delete()
            messages.success(request, 'Category deleted successfully!', extra_tags='admin')
        return redirect('manage_categories')
    
    return render(request, 'adminapp/confirm_delete.html', {
        'object': category,
        'title': 'Confirm Delete Category'
    })

@admin_required
def manage_subcategories(request):
    subcategories = SubCategory.objects.select_related('category').all().order_by('-created_at')
    return render(request, 'adminapp/manage_subcategories.html', {
        'subcategories': subcategories
    })

@admin_required
def add_subcategory(request):
    if request.method == 'POST':
        form = SubCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subcategory added successfully!', extra_tags='admin')
            return redirect('manage_subcategories')
    else:
        form = SubCategoryForm()
    
    return render(request, 'adminapp/subcategory_form.html', {
        'form': form,
        'title': 'Add Subcategory'
    })

@admin_required
def edit_subcategory(request, pk):
    subcategory = get_object_or_404(SubCategory, pk=pk)
    
    if request.method == 'POST':
        form = SubCategoryForm(request.POST, instance=subcategory)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subcategory updated successfully!', extra_tags='admin')
            return redirect('manage_subcategories')
    else:
        form = SubCategoryForm(instance=subcategory)
    
    return render(request, 'adminapp/subcategory_form.html', {
        'form': form,
        'title': 'Edit Subcategory'
    })

@admin_required
def delete_subcategory(request, pk):

    subcategory = get_object_or_404(SubCategory, pk=pk)
    
    if request.method == 'POST':
        # Check if subcategory has products before deleting
        if subcategory.product_set.exists():
            messages.error(request, 'Cannot delete subcategory with existing products!', extra_tags='admin')
        else:
            subcategory.delete()
            messages.success(request, 'Subcategory deleted successfully!', extra_tags='admin')
        return redirect('manage_subcategories')
    
    return render(request, 'adminapp/confirm_delete.html', {
        'object': subcategory,
        'title': 'Confirm Delete Subcategory'
    })