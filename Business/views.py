from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages
from .models import User,Review
from .forms import RegisterForm, LoginForm
from .forms import BusinessForm
from .models import BusinessImage,Visitor
from django.http import JsonResponse, HttpResponseForbidden
from .models import Business, BusinessImage
from .forms import BusinessImageForm
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
import uuid

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            email = form.cleaned_data['email']
            user.password = form.cleaned_data['password']  # No hashing
            user.save()

            # Sending Welcome Email (Now passing email as context)
            subject = "Welcome to Our Platform!"
            context = {'email': email}  # Pass email to template
            html_message = render_to_string('owner/wemail.html', context)
            plain_message = strip_tags(html_message)
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [email]

            email_message = EmailMultiAlternatives(subject, plain_message, from_email, recipient_list)
            email_message.attach_alternative(html_message, "text/html")
            email_message.send()

            messages.success(request, "Registration successful. Please log in.")
            return redirect('ologin')
    else:
        form = RegisterForm()

    return render(request, 'owner/register.html', {'form': form})


def login(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = User.objects.filter(email=email, password=password).first()
            if user:
                request.session['user_email'] = user.email
                return redirect('home')
            else:
                messages.error(request, "Invalid email or password.")
    else:
        form = LoginForm()
    return render(request, 'owner/login.html', {'form': form})


def ologout(request):
    request.session.flush()
    return redirect('ologin')


def home(request):
    # Check if the user is logged in
    if 'user_email' not in request.session:
        return redirect('ologin')  # Redirect if not logged in
    
    user_email = request.session['user_email']
    
    # Fetch all businesses owned by the logged-in user
    owner_businesses = Business.objects.filter(owner__email=user_email)
    
    # Check if the user already has an approved business
    has_approved_business = Business.objects.filter(
        owner__email=user_email,
        approval_status=True
    ).exists()
    
    # If user has approved businesses, prepare data only for those
    labels = []
    data = []
    
    if has_approved_business:
        # Only get approved businesses for graph data
        approved_businesses = Business.objects.filter(
            owner__email=user_email,
            approval_status=True
        )
        
        # Prepare data for Chart.js with only approved businesses
        labels = [business.name for business in approved_businesses]
        data = [business.total_likes() for business in approved_businesses]
    
    return render(request, 'owner/home.html', {
        'user_email': user_email,
        'businesses': owner_businesses,  # Pass all businesses to template
        'labels': labels,
        'data': data,
        'has_approved_business': has_approved_business
    })

def add(request):
    # Check if 'user_email' is in the session
    if 'user_email' not in request.session:
        messages.error(request, "You must be logged in to add a business.")
        return redirect('ologin')  # Redirect to login page or any other page

    # Get the logged-in user from the session
    user_email = request.session['user_email']
    owner = User.objects.get(email=user_email)

    if request.method == 'POST':
        form = BusinessForm(request.POST)
        files = request.FILES.getlist('business_images')  # Fetch multiple images
        
        if form.is_valid():
            # Create a new business and assign the logged-in user as the owner
            business = form.save(commit=False)
            business.owner = owner  # Automatically set the owner
            business.save()  # Save the business
            
            # Handle the business images
            for file in files:
                BusinessImage.objects.create(business=business, image=file)
            
            # Send email to admin using the owner's email
            send_mail(
    subject="New Business Approval Request",
    message=f"You have a new business request from {owner.email}. Please review and approve it.",
    from_email=owner.email,  # Owner's email dynamically set as the sender
    recipient_list=[settings.ADMIN_EMAIL],  # Admin's email address
    fail_silently=False,
)

            
            messages.success(request, "Your request was sent successfully. Please wait for admin approval.")
            return redirect('addbusiness')  # Or redirect to another page after successful submission
    else:
        form = BusinessForm()

    return render(request, 'owner/add_business.html', {'form': form})

def manage_business(request):
    if 'user_email' not in request.session:
        messages.error(request, "You must be logged in to manage the business.")
        return redirect('ologin')

    try:
        user_email = request.session['user_email']
        owner = User.objects.get(email=user_email)
        businesses = Business.objects.filter(owner=owner, approval_status=True)
        context = {'businesses': businesses}
        return render(request, 'owner/manage_business.html', context)
    except User.DoesNotExist:
        messages.error(request, "User account not found.")
        return redirect('ologin')

from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from .models import Business, BusinessImage

def update_business(request, business_id):
    if 'user_email' not in request.session:
        return JsonResponse({'success': False, 'message': 'Authentication required'}, status=401)

    try:
        business = get_object_or_404(Business, id=business_id, owner__email=request.session['user_email'])

        if request.method == 'POST':
            # Updating business details
            business.name = request.POST.get('name', business.name)
            business.shop = request.POST.get('shop', business.shop)
            business.mobile_number = request.POST.get('mobile_number', business.mobile_number)
            business.business_type = request.POST.get('business_type', business.business_type)
            business.google_map_location = request.POST.get('google_map_location', business.google_map_location)
            business.business_address = request.POST.get('business_address', business.business_address)
            business.description = request.POST.get('description', business.description)
            business.hours_of_operation = request.POST.get('hours_of_operation', business.hours_of_operation)

            # Handling image upload
            image_file = request.FILES.get('image')
            if image_file:
                new_image = BusinessImage(business=business, image=image_file)
                new_image.save()

            business.save()
            return JsonResponse({'success': True, 'message': 'Business updated successfully.'})

    except Business.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Business not found'}, status=404)
    
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return HttpResponseForbidden()


# def upload_image(request, business_id):
#     if 'user_email' not in request.session:
#         messages.error(request, "You must be logged in to upload images.")
#         return JsonResponse({'success': False, 'message': 'Authentication required'}, status=401)

#     try:
#         business = get_object_or_404(Business, id=business_id, owner__email=request.session['user_email'])

#         if request.method == 'POST' and request.FILES.get('image'):
#             form = BusinessImageForm(request.POST, request.FILES)
#             if form.is_valid():
#                 image = form.save(commit=False)
#                 image.business = business
#                 image.save()
#                 messages.success(request, "Image uploaded successfully.")
#                 return JsonResponse({
#                     'success': True,
#                     'image_url': image.image.url,
#                     'image_id': image.id
#                 })
#             return JsonResponse({'success': False, 'message': 'Invalid image format.'}, status=400)

#     except Exception as e:
#         return JsonResponse({'success': False, 'message': str(e)}, status=500)

#     return JsonResponse({'success': False, 'message': 'Invalid request.'})

def delete_image(request, image_id):
    if 'user_email' not in request.session:
        messages.error(request, "You must be logged in to delete images.")
        return JsonResponse({'success': False, 'message': 'Authentication required'}, status=401)

    try:
        image = get_object_or_404(BusinessImage, id=image_id, business__owner__email=request.session['user_email'])

        if request.method == 'POST':
            image.delete()
            messages.success(request, "Image deleted successfully.")
            return JsonResponse({'success': True, 'message': 'Image deleted successfully.'})

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return JsonResponse({'success': False, 'message': 'Invalid request.'})

@csrf_exempt
def delete_business(request, business_id):
    if request.method == 'POST':
        try:
            # Get the business object
            business = Business.objects.get(id=business_id)
            # Delete the business
            business.delete()
            return JsonResponse({'success': True})
        except Business.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Business not found'})
    return JsonResponse({'success': False, 'message': 'Invalid request'})

def visited_users(request, business_id):
    if 'user_email' not in request.session:
        return redirect('ologin')

    business = get_object_or_404(Business, id=business_id)

    # Only allow the owner to see visitors
    if business.owner.email != request.session['user_email']:
        return redirect('home')

    # Fetch all visitors for this business
    visitors = Visitor.objects.filter(business=business).select_related('user')

    return render(request, 'owner/visitedusers.html', {
        'business': business,
        'visitors': visitors
    })

def contact_us(request):
    if 'user_email' not in request.session:
        return redirect('ologin')

    user_email = request.session['user_email']

    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")

        if name and description:
            send_mail(
                subject=f"New Contact Us Message from {name}",
                message=f"Name: {name}\nEmail: {user_email}\n\nDescription:\n{description}",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[settings.ADMIN_EMAIL],
                fail_silently=False,
            )

            return redirect("success_page")  # Make sure 'success_page' exists in urls.py

    return render(request, "owner/contact.html", {"user_email": user_email})

def success_page(request):
    return render(request, "owner/success.html")

reset_tokens = {}

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()

        if user:
            # Generate a unique token using UUID
            token = str(uuid.uuid4())  
            reset_tokens[token] = user.id  # Store token with user ID

            # Create password reset link
            reset_url = request.build_absolute_uri(reverse('reset_password', kwargs={'token': token}))

            # Send email
            subject = "Password Reset Request"
            message = f"Click the link below to reset your password:\n{reset_url}"
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])

            return render(request, 'owner/forgot_password.html', {'message': "A reset link has been sent to your email."})
        else:
            return render(request, 'owner/forgot_password.html', {'message': "Email does not exist."})

    return render(request, 'owner/forgot_password.html')


def reset_password(request, token):
    user_id = reset_tokens.get(token)

    if not user_id:
        return render(request, 'owner/reset_password.html', {'message': "Invalid or expired token!"})

    user = User.objects.filter(id=user_id).first()

    if user:
        if request.method == 'POST':
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')

            if password == confirm_password:
                user.password = password  # Save password as plain text (not recommended)
                user.save()
                del reset_tokens[token]  # Remove used token
                return redirect('ologin')

            return render(request, 'owner/reset_password.html', {'message': "Passwords do not match!"})

        return render(request, 'owner/reset_password.html')
    else:
        return render(request, 'owner/reset_password.html', {'message': "User not found!"})
    
def owner_reviews(request):
    if 'user_email' not in request.session:
        return redirect('ologin')

    user_email = request.session['user_email']
    user = get_object_or_404(User, email=user_email)  # Retrieve user based on session email

    owner_businesses = Business.objects.filter(owner=user)
    reviews = Review.objects.filter(business__in=owner_businesses)
    
    return render(request, 'owner/owner_reviews.html', {'reviews': reviews})

def delete_review(request, review_id):
    if 'user_email' not in request.session:
        return redirect('ologin')

    user_email = request.session['user_email']
    user = get_object_or_404(User, email=user_email)

    review = get_object_or_404(Review, id=review_id, business__owner=user)
    
    if request.method == 'POST':
        review.delete()
        return redirect('owner_reviews')

    return render(request, 'owner/confirm_delete.html', {'review': review})

