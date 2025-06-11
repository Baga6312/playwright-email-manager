from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'profile_id', 'is_active_profile', 
                   'is_connected', 'proxy_address', 'last_login')
    list_filter = ('is_active_profile', 'is_connected', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'profile_id', 'proxy_address')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Browser Profile', {
            'fields': ('profile_id', 'is_active_profile', 'next_rotation',
                      'browser_signature', 'user_agent', 'language')
        }),
        ('Proxy Settings', {
            'fields': ('proxy_address', 'is_connected'),
            'classes': ('collapse',)
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser',
                      'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2',
                       'profile_id', 'proxy_address'),
        }),
    )
    
    ordering = ('-date_joined',)

admin.site.register(CustomUser, CustomUserAdmin)