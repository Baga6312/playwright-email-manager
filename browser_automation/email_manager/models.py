from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    
    # ========== Proxy & Connection Fields ==========
    proxy_address = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Proxy address in format IP:PORT"
    )
    is_connected = models.BooleanField(
        default=False,
        help_text="Whether the user is currently connected"
    )
    
    # ========== Browser Identification Fields ==========
    browser_signature = models.TextField(
        blank=True,
        help_text="Full browser fingerprint/configuration"
    )
    user_agent = models.CharField(
        max_length=255,
        blank=True,
        help_text="Browser user agent string"
    )
    language = models.CharField(
        max_length=50,
        default='en-US',
        help_text="Browser language setting"
    )
    
    # ========== Profile Management Fields ==========
    profile_id = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        help_text="Unique identifier for browser profile"
    )
   
    is_active_profile = models.BooleanField(
        default=True,
        help_text="Whether this profile should be used"
    )
    next_rotation = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When to rotate to next profile"
    )
    
    # ========== Metadata ==========
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.username} ({self.profile_id})"

    def get_proxy_config(self):
        """Helper method to parse proxy address"""
        if self.proxy_address:
            ip, port = self.proxy_address.split(':')
            return {'ip': ip, 'port': int(port)}
        return None