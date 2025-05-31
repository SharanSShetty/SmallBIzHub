from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import AdminRegisterForm, AdminLoginForm
from django.contrib.auth import logout
from django.http import JsonResponse
from Business.models import Business,BusinessImage,User
from datetime import datetime
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags

def admin_register(request):
    if request.method == 'POST':
        form = AdminRegisterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')

            # Create admin user using email as the username
            User.objects.create_user(username=email, email=email, password=password, is_staff=True)

            messages.success(request, "Admin registered successfully!")
            return redirect('admin_login')
    else:
        form = AdminRegisterForm()
    return render(request, 'control/aregister.html', {'form': form})


def admin_login(request):
    if request.method == 'POST':
        form = AdminLoginForm(data=request.POST)
        if form.is_valid():
            email = form.cleaned_data['username']  # Use email for authentication
            password = form.cleaned_data['password']

            user = authenticate(request, username=email, password=password)
            if user and user.is_staff:
                login(request, user)
                return redirect(request.GET.get('next', 'admin_home'))
            else:
                messages.error(request, "Invalid credentials or not an admin!")
    else:
        form = AdminLoginForm()
    return render(request, 'control/alogin.html', {'form': form})


@login_required(login_url='admin_login')
def admin_home(request):
    total_users = User.objects.count()
    current_month = datetime.now().month
    current_year = datetime.now().year

    # Use `created_at` to filter for users registered this month
    users_this_month = User.objects.filter(
        created_at__year=current_year,
        created_at__month=current_month
    ).count()

    return render(request, 'control/ahome.html', {
        'email': request.user.email,
        'total_users': total_users,
        'users_this_month': users_this_month
    })

def admin_logout(request):
    logout(request)
    messages.success(request, "You have been logged out successfully!")
    return redirect('admin_login')

@login_required(login_url='admin_login')
def approve(request):
    if request.method == "POST":
        business_id = request.POST.get("business_id")
        action = request.POST.get("action")
        business = get_object_or_404(Business, id=business_id)
        owner_email = business.owner.email  # Assuming `owner` is a ForeignKey to User with an email field

        if action == "approve":
            business.approval_status = True
            business.save()
            subject = "Hurray! Your Business Has Been Approved 🎉"
            html_message = render_to_string('control/business_approved.html', {'business': business})
        elif action == "reject":
            subject = "Oops! Your Business Was Rejected 😢"
            html_message = render_to_string('control/business_rejected.html', {'business': business})
            business.delete()
        else:
            return JsonResponse({"success": False, "message": "Invalid action"})

        # Strip HTML to get plain text version
        plain_message = strip_tags(html_message)

        # Send email with both plain text and HTML versions
        email = EmailMultiAlternatives(subject, plain_message, settings.DEFAULT_FROM_EMAIL, [owner_email])
        email.attach_alternative(html_message, "text/html")
        email.send()

        return JsonResponse({"success": True, "message": f"{business.name} {'approved' if action == 'approve' else 'rejected'}"})

    businesses = Business.objects.filter(approval_status=False)
    return render(request, 'control/approve_businesses.html', {'businesses': businesses})

@login_required(login_url='admin_login')
def manage_business(request):
    businesses = Business.objects.filter(approval_status=True).prefetch_related('images')

    if request.method == 'POST':
        if 'delete_business' in request.POST:
            # Delete selected business
            business_id = request.POST.get('delete_business')
            business = get_object_or_404(Business, id=business_id)
            business.delete()
            return redirect('manage_business')

        elif 'delete_image' in request.POST:
            # Delete selected image
            image_id = request.POST.get('delete_image')
            image = get_object_or_404(BusinessImage, id=image_id)
            image.delete()
            return redirect('manage_business')

        elif 'update_business' in request.POST:
            # Update business details
            business_id = request.POST.get('update_business')
            business = get_object_or_404(Business, id=business_id)
            
            # Update fields
            business.name = request.POST.get('name', business.name)
            business.shop = request.POST.get('shop', business.shop)
            business.mobile_number = request.POST.get('mobile_number', business.mobile_number)
            business.business_type = request.POST.get('business_type', business.business_type)
            business.business_address = request.POST.get('business_address', business.business_address)
            business.google_map_location = request.POST.get('google_map_location', business.google_map_location)
            business.description = request.POST.get('description', business.description)  # New field
            business.hours_of_operation = request.POST.get('hours_of_operation', business.hours_of_operation)  # New field
            business.save()

            # Add extra images
            if 'images' in request.FILES:
                for image in request.FILES.getlist('images'):
                    BusinessImage.objects.create(business=business, image=image)

            return redirect('manage_business')

    return render(request, 'control/manage_business.html', {'businesses': businesses})

@login_required(login_url='admin_login')  
def manage_users(request):
    """Manage users page - list and perform basic actions."""
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Staff required.')
        return redirect('home')

    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        user = get_object_or_404(User, id=user_id)

        if action == 'delete':
            user.delete()
            messages.success(request, f'User {user.email} deleted successfully.')
        elif action == 'toggle_active':
            user.is_active = not user.is_active
            user.save()
            status = 'activated' if user.is_active else 'deactivated'
            messages.success(request, f'User {user.email} {status}.')

    users = User.objects.all()
    return render(request, 'control/manage_users.html', {'users': users})