from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model, authenticate, login, logout
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q
from products.models import Category, SubCategory, SubSubCategory, Product,Sale, Order, OrderItem, Wishlist, Cart
from .forms import (
    CategoryForm, SubCategoryForm, SubSubCategoryForm
)
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

@admin_required
def manage_products(request):
    products = Product.objects.select_related(
        'category', 'subcategory', 'subsubcategory'
    ).prefetch_related(
        'images'  # removed 'attributes'
    ).all().order_by('-created_at')

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
            'images'  # removed 'attributes'
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
@admin_required
def admin_reports_view(request):
    # Time periods
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Product statistics
    total_products = Product.objects.count()
    active_products = Product.objects.filter(is_active=True).count()
    inactive_products = total_products - active_products
    
    # Sales statistics
    total_sales = Sale.objects.count()
    total_revenue = Sale.objects.aggregate(total=Sum('sold_price'))['total'] or 0
    
    # Recent sales (last 7 days)
    recent_sales = Sale.objects.filter(sold_at__date__gte=week_ago).count()
    recent_revenue = Sale.objects.filter(
        sold_at__date__gte=week_ago
    ).aggregate(total=Sum('sold_price'))['total'] or 0
    
    # Order statistics
    total_orders = Order.objects.count()
    paid_orders = Order.objects.filter(status='paid').count()
    unpaid_orders = Order.objects.filter(status='unpaid').count()
    
    # User engagement
    total_wishlist_items = Wishlist.objects.count()
    total_cart_items = Cart.objects.count()
    
    # Top selling products
    top_products = Sale.objects.values(
        'product__name'
    ).annotate(
        total_sold=Count('id'),
        total_revenue=Sum('sold_price')
    ).order_by('-total_sold')[:10]
    
    # Sales trend (last 30 days)
    sales_trend = []
    for i in range(30):
        date = today - timedelta(days=29 - i)
        daily_sales = Sale.objects.filter(sold_at__date=date).count()
        daily_revenue = Sale.objects.filter(
            sold_at__date=date
        ).aggregate(total=Sum('sold_price'))['total'] or 0
        sales_trend.append({
            'date': date,
            'sales_count': daily_sales,
            'revenue': daily_revenue
        })
    
    context = {
        'total_products': total_products,
        'active_products': active_products,
        'inactive_products': inactive_products,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'recent_sales': recent_sales,
        'recent_revenue': recent_revenue,
        'total_orders': total_orders,
        'paid_orders': paid_orders,
        'unpaid_orders': unpaid_orders,
        'total_wishlist_items': total_wishlist_items,
        'total_cart_items': total_cart_items,
        'top_products': top_products,
        'sales_trend': sales_trend,
        'today': today,
        'week_ago': week_ago,
        'month_ago': month_ago,
    }
    
    return render(request, 'adminapp/reports.html', context)

@admin_required
def sales_report_view(request):
    # Get date range from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    sales = Sale.objects.all().order_by('-sold_at')
    
    if start_date and end_date:
        sales = sales.filter(
            sold_at__date__range=[start_date, end_date]
        )
    
    total_sales = sales.count()
    total_revenue = sales.aggregate(total=Sum('sold_price'))['total'] or 0
    avg_sale_price = sales.aggregate(avg=Avg('sold_price'))['avg'] or 0
    
    context = {
        'sales': sales,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'avg_sale_price': avg_sale_price,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'adminapp/sales_report.html', context)