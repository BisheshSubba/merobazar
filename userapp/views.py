from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import UserRegisterForm, LoginForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.http import JsonResponse
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
    featured_products = Product.objects.filter(is_available=True).order_by('-created_at')[:8]
    recent_products = Product.objects.filter(is_available=True).order_by('-created_at')[:8]
    
    context = {
        'categories': categories,
        'featured_products': featured_products,
        'recent_products': recent_products,
    }
    return render(request, 'userapp/dashboard.html', context)


def logout_view(request):
    logout(request)
    return redirect('user_dashboard')