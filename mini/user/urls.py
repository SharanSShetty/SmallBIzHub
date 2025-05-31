from django.urls import path,include
from .views import register, login_view, dashboard, logout_view,like_business,business_detail,update_profile,save_business,saved_businesses,post_review,contact_success_view,contact_view

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('dashboard/', dashboard, name='dashboard'),
    path('logout/', logout_view, name='logout'),
    path('oauth/', include('social_django.urls', namespace='social')),  # Add Google login
    path('like/<int:business_id>/', like_business, name='like_business'),
    path('business/<int:business_id>/',business_detail, name='business_detail'),
    path('update-profile/', update_profile, name='update_profile'),
    path('save_business/<int:business_id>/', save_business, name='save_business'),
    path('saved/', saved_businesses, name='saved_businesses'),
    path('post-review/<int:business_id>/', post_review, name='post_review'),
    path('contact/', contact_view, name='contact'),
    path('contact/success/', contact_success_view, name='contact_success'),
]
