from django.db import models
from django.conf import settings

class SkyVoiceLetter(models.Model):
    # 작성자
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='skyvoice_letters')
    
    # 수신자 정보
    receiver_name = models.CharField(max_length=30)
    receiver_gender = models.CharField(max_length=10)
    receiver_age = models.PositiveIntegerField()
    receiver_type = models.CharField(max_length=30)
    receiver_special_note = models.CharField(max_length=100, blank=True)

    # 작성자가 작성한 편지
    content_text = models.TextField(blank=True)
    # 음성 파일(S3)
    voice_file = models.FileField(upload_to='skyvoice/', blank=True, null=True)

    # AI 답신
    reply_text = models.TextField(blank=True)
    reply_voice_file = models.FileField(upload_to='skyvoice/reply/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    replied_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.user_id} → {self.receiver_name} ({self.created_at})"
