import openai
from google.cloud import texttospeech
import uuid
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone

# 1. 프롬프트 생성 함수 (수신자 타입/관계/특이사항/작성자 닉네임 반영)
def build_dynamic_prompt(letter):
    # 작성자 닉네임(없으면 아이디 등으로 대체)
    try:
        sender_nickname = letter.user.nickname  # user 모델에 nickname 필드가 있다면!
    except AttributeError:
        sender_nickname = getattr(letter.user, 'user_id', '작성자')

    # 관계/타입에 따른 역할 안내 및 가이드
    t = letter.receiver_type.lower()
    if t in ["dog", "cat", "hamster", "pet", "반려견", "반려동물"]:
        role = f"너는 {letter.receiver_type} {letter.receiver_name}야."
        guide = "주인의 편지에 대해 네(동물)의 시점에서, 1인칭(예: '나', '엄마/아빠')으로 짧고 따뜻하게 답장해줘."
    elif t in ["mother", "father", "parent", "부모님", "엄마", "아빠"]:
        role = f"너는 {letter.receiver_type}({letter.receiver_name})야. (돌아가신 경우라면 그 설정에 맞게)"
        guide = f"{sender_nickname}이(가) 쓴 편지에 대해 부모님의 시점에서, 사랑이 느껴지는 1인칭 답장을 써줘."
    elif t in ["friend", "친구"]:
        role = f"너는 {letter.receiver_name}이라는 친구야."
        guide = f"{sender_nickname}이(가) 쓴 편지에 대해 친구의 시점에서, 친근하고 진솔하게 답장해줘."
    else:
        role = f"너는 {letter.receiver_type}({letter.receiver_name})야."
        guide = f"{sender_nickname}이(가) 쓴 편지에 대해, 네 시점에서 1인칭으로 답장 써줘."

    prompt = f"""
{role}
수신자 정보:
- 이름: {letter.receiver_name}
- 성별: {letter.receiver_gender}
- 나이: {letter.receiver_age}
- 특이사항: {letter.receiver_special_note}

작성자(주인공): {sender_nickname}

너에게 편지가 도착했어.
아래 편지는 {sender_nickname}이(가) 네게 쓴 거야.

편지 내용:
\"{letter.content_text}\"

{guide}
(답장은 꼭 1인칭 시점으로, 상대방에게 직접 이야기하듯 써줘. 3줄 이내로 짧고 따뜻하게!)    
"""
    return prompt

# 2. 답장 텍스트 생성
def generate_gpt_reply(letter):
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    prompt = build_dynamic_prompt(letter)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
    )
    return response.choices[0].message.content.strip()

# 3. TTS 변환 (구글)
def synthesize_speech(text):
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="ko-KR",
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
    )
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    return response.audio_content  # mp3 bytes

# S3 직접 업로드
def upload_mp3_to_s3(mp3_data, filename):
    s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )
    key = f"skyvoice/reply/{filename}"
    s3.put_object(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=key,
        Body=mp3_data,
        ContentType='audio/mpeg',
        ACL='public-read'
    )
    url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{key}"
    return url

def make_ai_reply(letter):
    try:
        # GPT 답장 생성
        reply_text = generate_gpt_reply(letter)
        if not reply_text:
            reply_text = "[AI 답장 생성 실패]"

        # Google TTS 변환
        mp3_data = synthesize_speech(reply_text)
        if not mp3_data:
            raise ValueError("TTS 변환 실패")

        # S3 직접 업로드 후 URL 획득
        filename = f"skyvoice_reply_{uuid.uuid4().hex}.mp3"
        s3_url = upload_mp3_to_s3(mp3_data, filename)

        # 모델에 텍스트와 URL 저장
        letter.reply_text = reply_text
        letter.reply_voice_url = s3_url
        letter.replied_at = timezone.now()
        letter.save()

        return letter

    except Exception as e:
        logger.error(f"[SkyVoice AI 오류] letter.id={letter.id}: {e}")
        return None