import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Letter(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_letters')
    receiver_email = models.EmailField(blank=True, null=True) 
    audio_file = models.FileField(upload_to='letters/audio/')
    transcript = models.TextField(blank=True) 
    paper_color = models.CharField(max_length=20, default='white')
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    is_sent = models.BooleanField(default=False)

    def __str__(self):
        return f"Letter from {self.sender} to {self.receiver_email or 'anonymous'}"