from django.db import models
from django.conf import settings

class SkyVoiceLetter(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='skyvoice_letters')
    
    receiver_name = models.CharField(max_length=30)
    receiver_gender = models.CharField(max_length=10)
    receiver_age = models.PositiveIntegerField()
    receiver_type = models.CharField(max_length=30)
    receiver_special_note = models.CharField(max_length=100, blank=True)

    content_text = models.TextField(blank=True)
    voice_file = models.FileField(upload_to='skyvoice/', blank=True, null=True)

    reply_text = models.TextField(blank=True)
    reply_voice_file = models.FileField(upload_to='skyvoice/reply/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    replied_at = models.DateTimeField(null=True, blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    is_sent = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.user_id} → {self.receiver_name} ({self.created_at})"
