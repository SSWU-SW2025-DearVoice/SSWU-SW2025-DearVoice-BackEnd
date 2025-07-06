import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Letter(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # 공유 링크용 고유값
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_letters')
    receiver_email = models.EmailField(blank=True, null=True)  # 회원/비회원 모두 고려
    audio_file = models.FileField(upload_to='letters/audio/')
    transcript = models.TextField(blank=True)  # 나중에 STT 변환 결과 저장
    paper_color = models.CharField(max_length=20, default='white')  # 선택형
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Letter from {self.sender} to {self.receiver_email or 'anonymous'}"
