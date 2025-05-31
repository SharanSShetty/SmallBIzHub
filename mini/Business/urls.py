from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('', views.login, name='ologin'),
    path('logout/', views.ologout, name='ologout'),
    path('home/', views.home, name='home'),
    path('addbusiness',views.add,name='addbusiness'),
    path('manage_business/', views.manage_business, name='manage_business'),
    path('update_business/<int:business_id>/', views.update_business, name='update_business'),
    # path('upload_image/<int:business_id>/', views.upload_image, name='upload_image'),
    path('delete_image/<int:image_id>/', views.delete_image, name='delete_image'),
    path('delete_business/<int:business_id>/', views.delete_business, name='delete_business'),
     path('business/<int:business_id>/visitors/', views.visited_users, name='visited_users'), 
     path("contact/", views.contact_us, name="contact_us"),
     path("success/", views.success_page, name="success_page"), 
     path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
    path('reviews/', views.owner_reviews, name='owner_reviews'),
    path('delete/<int:review_id>/', views.delete_review, name='delete_review'),
]
