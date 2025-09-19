from django import forms
from .models import User
from .models import Business, BusinessImage
import re

class RegisterForm(forms.ModelForm):
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")
    
    class Meta:
        model = User
        fields = ['email', 'password']
        widgets = {
            'password': forms.PasswordInput,
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        
        # Check password length
        if len(password) < 6:
            raise forms.ValidationError("Password must be at least 6 characters long.")
        
        # Check for at least one capital letter
        if not re.search(r'[A-Z]', password):
            raise forms.ValidationError("Password must contain at least one capital letter.")
        
        # Check for at least one number
        if not re.search(r'\d', password):
            raise forms.ValidationError("Password must contain at least one number.")
        
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        
        return cleaned_data

class LoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(widget=forms.PasswordInput, label="Password")

class BusinessForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = [
            'name', 'shop', 'mobile_number', 'business_type', 
            'google_map_location', 'business_address', 'description', 'hours_of_operation'
        ]
        widgets = {
            'google_map_location': forms.Textarea(attrs={'rows': 3}),
            'business_address': forms.Textarea(attrs={'rows': 3}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'hours_of_operation': forms.TextInput(attrs={'placeholder': 'e.g., Mon-Fri: 9 AM - 6 PM'})
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if any(char.isdigit() for char in name):
            raise forms.ValidationError("Name should not contain any numbers")
        return name
    
    def clean_mobile_number(self):
        mobile_number = self.cleaned_data.get('mobile_number')
        if len(mobile_number) > 10:
            raise forms.ValidationError("Mobile number should not exceed 10 digits")
        return mobile_number

class BusinessImageForm(forms.ModelForm):
    class Meta:
        model = BusinessImage
        fields = ['image']