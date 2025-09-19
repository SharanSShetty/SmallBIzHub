from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages
from .models import CustomUser
from .forms import RegisterForm, LoginForm
from django.http import JsonResponse
from Business.models import Business,Visitor,Review
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            if CustomUser.objects.filter(username=username).exists():
                messages.error(request, "Username already taken")
            elif CustomUser.objects.filter(email=email).exists():
                messages.error(request, "Email already registered")
            else:
                CustomUser.objects.create(username=username, email=email, password=password)
                messages.success(request, "Registration successful! Please login.")
                return redirect('login')

    else:
        form = RegisterForm()
    return render(request, 'user/register.html', {'form': form})

def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = CustomUser.objects.filter(username=username, password=password).first()
            if user:
                request.session['username'] = user.username
                messages.success(request, f"Welcome, {user.username}!")
                return redirect('dashboard')
            else:
                messages.error(request, "Invalid username or password")

    else:
        form = LoginForm()
    return render(request, 'user/login.html', {'form': form})


def dashboard(request):
    if 'username' not in request.session:
        return redirect('login')  # Ensure user is logged in
        
    user = CustomUser.objects.get(username=request.session['username'])  # Get logged-in user
    query = request.GET.get('search', '')
    businesses = Business.objects.filter(approval_status=True)
        
    if query:
        businesses = businesses.filter(
            name__icontains=query
        ) | businesses.filter(
            shop__icontains=query
        ) | businesses.filter(
            business_address__icontains=query
        )
        
    # Add `is_liked` attribute to each business
    for business in businesses:
        business.is_liked = business.likes.filter(id=user.id).exists()
        
    return render(request, 'user/dashboard.html', {
        'businesses': businesses,
        'username': request.session['username'],
        'user': user  # Add the user object to the context
    })

def like_business(request, business_id):
    if request.method == "POST":
        if 'username' not in request.session:
            return JsonResponse({"error": "User not authenticated"}, status=401)

        user = CustomUser.objects.get(username=request.session['username'])
        business = get_object_or_404(Business, id=business_id)

        if business.likes.filter(id=user.id).exists():
            business.likes.remove(user)
            liked = False
        else:
            business.likes.add(user)
            liked = True

        return JsonResponse({"liked": liked, "total_likes": business.total_likes()})

    return JsonResponse({"error": "Invalid request"}, status=400)

def business_detail(request, business_id):
    if 'username' not in request.session:
        return redirect('login')  # Ensure user is logged in
    
    business = get_object_or_404(Business, id=business_id)
    user = CustomUser.objects.get(username=request.session['username'])  # Get logged-in user
    
    # Track visitor if they haven't visited before
    Visitor.objects.get_or_create(business=business, user=user)
    
    # Get reviews for this business
    reviews = Review.objects.filter(business=business).order_by('-created_at')
    
    # Return with both business and reviews in the context
    return render(request, 'user/business_detail.html', {
        'business': business,
        'reviews': reviews
    })

def logout_view(request):
    request.session.flush()
    messages.success(request, "You have been logged out.")
    return redirect('login')

def save_google_user(backend, user, response, request, *args, **kwargs):
    if backend.name == 'google-oauth2':
        email = response.get('email')
        username = email.split('@')[0]  # Extract username before '@'

        # Check if user exists
        existing_user = CustomUser.objects.filter(email=email).first()
        if not existing_user:
            # Create a new user
            new_user = CustomUser.objects.create(username=username, email=email, password="")
            new_user.save()
            request.session['username'] = new_user.username  # Store new user's username
        else:
            request.session['username'] = existing_user.username  # Store existing user's username

    return redirect('/users/dashboard/')  # Redirect after login

def update_profile(request):
    if request.method == 'POST':
        if 'username' not in request.session:
            return redirect('login')
            
        try:
            # Get the user from the session username
            user = CustomUser.objects.get(username=request.session['username'])
            
            # Update user details (excluding email)
            user.username = request.POST.get('username')
            # Email remains unchanged
            user.phone_number = request.POST.get('phone_number')
            
            # Update profile image if provided
            if 'profile' in request.FILES:
                user.profile = request.FILES['profile']
            
            user.save()
            
            # Update the session username if it changed
            if user.username != request.session['username']:
                request.session['username'] = user.username
                
            messages.success(request, 'Profile updated successfully!')
        except CustomUser.DoesNotExist:
            messages.error(request, 'User not found!')
        
        return redirect('dashboard')
    
    return redirect('dashboard')

def save_business(request, business_id):
    # Ensure the user is authenticated via session
    if 'username' not in request.session:
        return JsonResponse({'message': 'Unauthorized'}, status=401)

    try:
        # Get the user from the session
        user = CustomUser.objects.get(username=request.session['username'])
        business = get_object_or_404(Business, id=business_id)

        # Toggle save/unsave
        if business in user.saved_businesses.all():
            user.saved_businesses.remove(business)
            return JsonResponse({'message': 'Unsaved'})
        else:
            user.saved_businesses.add(business)
            return JsonResponse({'message': 'Saved'})
    
    except CustomUser.DoesNotExist:
        return JsonResponse({'message': 'User not found'}, status=404)

    return JsonResponse({'message': 'Error'}, status=400)


def saved_businesses(request):
    # Ensure the user is authenticated via session
    if 'username' not in request.session:
        return redirect('login')

    try:
        # Get the logged-in user
        user = CustomUser.objects.get(username=request.session['username'])

        # Fetch all saved businesses
        saved_businesses = user.saved_businesses.all()

        return render(request, 'user/saved_businesses.html', {'saved_businesses': saved_businesses})

    except CustomUser.DoesNotExist:
        return redirect('login')
    
@csrf_exempt
def post_review(request, business_id):
    # Ensure user authentication via session
    if 'username' not in request.session:
        messages.error(request, "You must be logged in to post a review.")
        return redirect('login')

    # Get user from session
    try:
        user = CustomUser.objects.get(username=request.session['username'])
    except CustomUser.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('login')

    business = get_object_or_404(Business, id=business_id)

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()

        if content:
            Review.objects.create(user=user, business=business, content=content)
            messages.success(request, "Your review has been posted successfully!")
        else:
            messages.error(request, "Review content cannot be empty.")

    # Fetch all reviews for the business
    reviews = Review.objects.filter(business=business).order_by('-created_at')

    return render(request, 'user/business_detail.html', {
        'business': business,
        'reviews': reviews
    })

def contact_view(request):
    if 'username' not in request.session:
        messages.error(request, "You must be logged in to post a complaint.")
        return redirect('login')  # redirect to your login page

    # Get the user instance
    try:
        user = CustomUser.objects.get(username=request.session['username'])
    except CustomUser.DoesNotExist:
        messages.error(request, "Invalid user session. Please log in again.")
        return redirect('login')

    if request.method == 'POST':
        complaint = request.POST.get('complaint', '').strip()

        if not complaint:
            return render(request, 'user/contact.html', {
                'username': user.username,
                'email': user.email,
                'error': 'Complaint cannot be empty.'
            })

        # Send email
        subject = f"Complaint from {user.username}"
        message = f"""
        Username: {user.username}
        Email: {user.email}

        Complaint:
        {complaint}
        """
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.ADMIN_EMAIL],
            fail_silently=False
        )

        return redirect('contact_success')

    return render(request, 'user/contact.html', {
        'username': user.username,
        'email': user.email
    })

def contact_success_view(request):
    if 'username' not in request.session:
        messages.error(request, "You must be logged in.")
        return redirect('login')
    return render(request, 'user/sucess.html')
