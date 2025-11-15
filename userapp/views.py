from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import UserRegisterForm, LoginForm, ProfileUpdateForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import CustomUser
from django.db.models import Q
from recommendations.utils import HybridRecommender
from products.models import Product, Category, SubCategory, Order, OrderItem

User = get_user_model()
def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'user'

            # user.is_active = False   # deactivate until verified (DISABLED)
            user.is_active = True      # activate immediately (NO email verification)
            user.save()

            # --- EMAIL VERIFICATION DISABLED ---
            # current_site = get_current_site(request)
            # subject = "Confirm your Gmail account"
            # message = render_to_string('userapp/email_verification.html', {
            #     'user': user,
            #     'domain': current_site.domain,
            #     'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            #     'token': default_token_generator.make_token(user),
            # })
            # email = EmailMessage(subject, message, to=[user.email])
            # email.send()
            # ------------------------------------

            # return render(request, 'userapp/check_email.html', {'email': user.email})
            # Instead of verification page, go straight to login
            messages.success(request, "Account created successfully! You can now log in.")
            return redirect('user_login')

    else:
        form = UserRegisterForm()
    return render(request, 'userapp/register.html', {'form': form})


def activate_view(request, uidb64, token):
    # --- EMAIL ACTIVATION DISABLED ---
    # try:
    #     uid = force_str(urlsafe_base64_decode(uidb64))
    #     user = CustomUser.objects.get(pk=uid)
    # except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
    #     user = None

    # if user is not None and default_token_generator.check_token(user, token):
    #     user.is_active = True
    #     user.save()
    #     messages.success(request, "Your email has been verified! You can now log in.")
    #     return redirect('user_login')
    # else:
    #     return render(request, 'userapp/activation_failed.html')
    # ---------------------------------

    # New simple redirect
    return redirect('user_login')


def login_view(request):
    if request.user.is_authenticated:
        if request.user.role == 'admin':
            return redirect('admin_login')
        return redirect('user_dashboard')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()

            # --- REMOVE INACTIVE USER BLOCKING ---
            # if not user.is_active:
            #     messages.error(request, "Your account is inactive. Please check your email to verify your account.", extra_tags='login')
            #
            #     # Optional: resend verification email link (DISABLED)
            #     resend = request.POST.get("resend_verification")
            #     if resend == "true":
            #         current_site = get_current_site(request)
            #         subject = "Confirm your Gmail account"
            #         message = render_to_string('userapp/email_verification.html', {
            #             'user': user,
            #             'domain': current_site.domain,
            #             'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            #             'token': default_token_generator.make_token(user),
            #         })
            #         email = EmailMessage(subject, message, to=[user.email])
            #         email.send()
            #         messages.success(request, "Verification email resent. Please check your inbox.", extra_tags='login')
            #
            #     return redirect('user_login')
            # --------------------------------------

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

    recommender = HybridRecommender()
    recommended_products = []
    popular_products = []

    if request.user.is_authenticated:
        # Personalized recommendations
        try:
            recommended_products = recommender.get_hybrid_recommendations(
                user_id=request.user.id,
                top_n=8
            )
        except Exception:
            pass
    else:
        # Show popular products for guests
        try:
            popular_products = recommender.get_popular_products(top_n=8)
        except Exception:
            pass
    context = {
        'categories': categories,
        'featured_products': featured_products,
        'recent_products': recent_products,
        'recommended_products': recommended_products,
        'popular_products': popular_products,
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
def my_orders_view(request):
    # Orders made by the user (as buyer)
    user_orders_list = Order.objects.filter(user=request.user).order_by('-created_at').prefetch_related('items__product')
    paginator = Paginator(user_orders_list, 5)  # 5 orders per page
    page_number = request.GET.get('page')
    user_orders = paginator.get_page(page_number)

    context = {
        'user_orders': user_orders,
    }
    return render(request, 'userapp/my_orders.html', context)

@login_required
def orders_received_view(request):
    # Orders received by the user (as seller)
    received_items = OrderItem.objects.filter(seller=request.user).select_related('order', 'product')
    
    # Group received items by order
    received_orders_dict = {}
    for item in received_items:
        if item.order.id not in received_orders_dict:
            received_orders_dict[item.order.id] = {
                'order': item.order,
                'items': []
            }
        received_orders_dict[item.order.id]['items'].append(item)
    
    received_orders_list = list(received_orders_dict.values())
    received_paginator = Paginator(received_orders_list, 5)  # 5 orders per page
    page_number = request.GET.get('page')
    received_orders = received_paginator.get_page(page_number)

    context = {
        'received_orders': received_orders,
    }
    return render(request, 'userapp/orders_received.html', context)


@login_required
def order_detail_view(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related('items__product'), id=order_id, user=request.user)
    return render(request, 'userapp/order_detail.html', {'order': order})

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
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort_by', 'newest')  # Default to newest first
    page_number = request.GET.get('page', 1)
    
    if query:
        # Search in product name, description, and brand
        products_list = Product.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(brand__icontains=query),
            is_active=True
        ).distinct()
    else:
        products_list = Product.objects.none()
    
    # Apply price filters if provided
    if min_price:
        products_list = products_list.filter(price__gte=min_price)
    if max_price:
        products_list = products_list.filter(price__lte=max_price)
    
    # Sorting mapping
    sort_mapping = {
        'price_asc': 'price',
        'price_desc': '-price',
        'newest': '-created_at',
        'oldest': 'created_at',
    }
    order_by = sort_mapping.get(sort_by, '-created_at')
    products_list = products_list.order_by(order_by)
    
    # Pagination with 12 items per page
    paginator = Paginator(products_list, 12)
    products = paginator.get_page(page_number)
    
    context = {
        'products': products,
        'query': query,
        'current_sort': order_by,
        'applied_filters': {
            'min_price': min_price,
            'max_price': max_price,
        },
        'categories': Category.objects.prefetch_related('subcategories').all(),
    }
    return render(request, 'userapp/search_results.html', context)

def landing_page(request):
     return render(request, 'userapp/landing.html') 