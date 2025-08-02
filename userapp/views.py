from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import UserRegisterForm, LoginForm, ProfileUpdateForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from products.models import Product, Category, SubCategory

User = get_user_model()

def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'user'
            user.save()
            return redirect('user_login')
    else:
        form = UserRegisterForm()
    return render(request, 'userapp/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        if request.user.role == 'admin':
            return redirect('admin_login')
        return redirect('user_dashboard')
        
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            
            if not user.is_active:
                messages.error(request, "Your account has been suspended.", extra_tags='login')
                return redirect('user_login')
            
            if user.role == 'admin':
                messages.error(request, "You don't have permission to access this login page. Please use the admin login.", extra_tags='login')
                return redirect('admin_login')
            
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!", extra_tags='login')
            return redirect('user_dashboard')
    else:
        form = LoginForm()
    return render(request, 'userapp/login.html', {'form': form})

def user_dashboard(request):

    categories = Category.objects.prefetch_related('subcategories').all()
    featured_products = Product.objects.filter(is_active=True).order_by('-created_at')[:8]
    recent_products = Product.objects.filter(is_active=True).order_by('-created_at')[:8]
    
    context = {
        'categories': categories,
        'featured_products': featured_products,
        'recent_products': recent_products,
    }
    return render(request, 'userapp/dashboard.html', context)


def logout_view(request):
    logout(request)
    return redirect('user_dashboard')


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    # Get user's products - changed from seller=request.user to user=request.user
    user_products = Product.objects.filter(user=request.user)
    
    context = {
        'form': form,
        'user_products': user_products
    }
    return render(request, 'userapp/profile.html', context)

@login_required
def user_products_view(request):
    # Changed from seller=request.user to user=request.user
    user_products = Product.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'user_products': user_products
    }
    return render(request, 'userapp/user_products.html', context)


def search_products(request):
    query = request.GET.get('q', '')
    page_number = request.GET.get('page', 1)
    
    if query:
        # Search in product name, description, and brand
        products_list = Product.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(brand__icontains=query),
            is_active=True
        ).distinct().order_by('-created_at')
    else:
        products_list = Product.objects.none()
    
    # Pagination with 12 items per page
    paginator = Paginator(products_list, 12)
    products = paginator.get_page(page_number)
    
    context = {
        'products': products,
        'query': query,
        'categories': Category.objects.prefetch_related('subcategories').all(),
    }
    return render(request, 'userapp/search_results.html', context)