import openai
from google.cloud import texttospeech
import uuid
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
import logging
import boto3

logger = logging.getLogger(__name__)

# 1. 프롬프트 생성 함수
def build_dynamic_prompt(letter):
    #필드 추출
    user = getattr(letter, 'user', None)
    sender_nickname = getattr(user, 'nickname', None) or getattr(user, 'user_id', None) or "작성자"

    r_type = (getattr(letter, 'receiver_type', '') or '').strip().lower()
    r_name = getattr(letter, 'receiver_name', '') or '상대'
    r_gender = getattr(letter, 'receiver_gender', '') or ''
    r_age = getattr(letter, 'receiver_age', '') or ''
    r_note = (getattr(letter, 'receiver_special_note', '') or '').strip()
    content = getattr(letter, 'content_text', '') or ''

    PET_KEYWORDS = {"dog","cat","hamster","pet","반려견","반려동물","고양이","강아지"}
    PARENT_KEYWORDS = {"mother","father","parent","부모님","엄마","아빠"}
    FRIEND_KEYWORDS = {"friend","친구"}

    # 관계별 역할 및 톤
    if r_type in PET_KEYWORDS:
        role_line = f"역할: 너는 반려동물 {r_name}야."
        style_line = "어조: 사랑스럽고 천진난만하게."
        pov_line = "시점: 1인칭(‘나’)으로, 주인을 ‘엄마/아빠’ 또는 이름으로 부르기."
    elif r_type in PARENT_KEYWORDS:
        parent_honorific = "엄마" if r_type in {"mother","엄마"} else ("아빠" if r_type in {"father","아빠"} else "부모")
        role_line = f"역할: 너는 {parent_honorific} {r_name}야."
        style_line = "어조: 다정하고 위로가 되는 말투."
        pov_line = "시점: 1인칭(‘나’)으로, 자녀를 이름이나 애칭으로 부르기."
    elif r_type in FRIEND_KEYWORDS:
        role_line = f"역할: 너는 친구 {r_name}야."
        style_line = "어조: 친근하고 솔직하게."
        pov_line = "시점: 1인칭(‘나’)으로, 이름으로 부르기."
    else:
        role_line = f"역할: 너는 {r_type} {r_name}야."
        style_line = "어조: 관계에 맞게 진솔하고 따뜻하게."
        pov_line = "시점: 1인칭(‘나’)으로 쓰기."

    # 특이사항에서 사망 여부
    note_lower = r_note.lower()
    is_deceased = any(k in note_lower for k in ["돌아가신","하늘나라","고인","passed","deceased"])
    deceased_line = "설정: 너는 이미 세상을 떠났고, 편지는 추모의 마음으로 읽었다고 가정." if is_deceased else ""

    # Few-shot 예시
    examples = """
예시:
[반려동물]
편지: "요즘 너무 바빠서 못 놀아줘서 미안해."
답장: "나는 너랑 놀 수만 있다면 언제든 좋아. 오늘 밤엔 꼭 같이 놀자!"

[부모]
편지: "요즘 학교가 힘들어서 지쳐."
답장: "네 마음이 힘들다니 안타깝구나. 항상 네 편이니 믿고 나아가렴."

[친구]
편지: "이번 주말에 영화 보러 갈래?"
답장: "좋지! 너랑 같이 영화 보면 재밌을 것 같아."
"""

    # 프롬프트
    prompt = f"""
시스템 지시:
- 출력 형식: 2~3문장, 180자 이내
- 반드시 1인칭 시점(‘나’)으로 작성
- 수신자({r_name})의 입장에서 {sender_nickname}에게 직접 말하기
- 편지의 감정에 공감 + 짧은 위로/격려 + 약속/응원 포함
- 이모지, 해시태그, 서명 금지
- 메타 발화, 지시 재언급 금지

{role_line}
{style_line}
{pov_line}
{deceased_line}

수신자 정보:
- 이름: {r_name}
- 성별: {r_gender}
- 나이: {r_age}
- 특이사항: {r_note if r_note else "없음"}

작성자(보낸이): {sender_nickname}

상황:
아래 편지는 {sender_nickname}이(가) {r_name}에게 보낸 편지야.
편지를 읽은 너({r_name})가 답장을 쓴다.

편지:
\"\"\"{content}\"\"\"

{examples}

출력:
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
        #ACL='public-read'
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