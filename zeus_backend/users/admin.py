# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin
# from .models import User

# admin.site.register(User, UserAdmin)
# from django.contrib import admin
# from .models import User

# # Register your custom User model (if you have one)
# admin.site.register(User)
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': (
            'phone_number',
            'date_of_birth',
            'gender',
            'profile_picture_url'
        )}),
        ('Permissions', {'fields': (
            'is_landlord',
            'is_active',
            'is_staff',
            'is_superuser',
            'groups',
            'user_permissions'
        )}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('username', 'email', 'is_landlord', 'is_staff')

admin.site.register(User, CustomUserAdmin)