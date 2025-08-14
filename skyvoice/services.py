import openai
from google.cloud import texttospeech
import uuid
from django.conf import settings
from django.utils import timezone
import logging
import boto3
import re

logger = logging.getLogger(__name__)

# --- 프롬프트 생성 ---
def build_dynamic_prompt(letter):
    user = getattr(letter, 'user', None)
    sender = getattr(user, 'nickname', None) or getattr(user, 'user_id', None) or "보낸이"

    r_type_raw = (getattr(letter, 'receiver_type', '') or '').strip()
    norm = r_type_raw.replace("님", "").replace("외", "").lower()
    r_name = getattr(letter, 'receiver_name', '') or '상대'
    r_gender = getattr(letter, 'receiver_gender', '') or ''
    r_age = getattr(letter, 'receiver_age', '') or ''
    r_note = (getattr(letter, 'receiver_special_note', '') or '').strip()
    content = getattr(letter, 'content_text', '') or ''

    def kind(k): return any(x in norm for x in k)
    if kind(["grand", "할머니", "할아버지", "조부", "조모"]):
        role = f"너는 {r_name}(조부모)이고 {sender}의 마음을 보듬어 준다."
        tone = "따뜻하고 포근, 안심시키는 말투"
    elif kind(["parent", "부모", "엄마", "어머니", "아빠", "아버지"]):
        role = f"너는 {r_name}(부모)이고 {sender}를 다정히 위로한다."
        tone = "다정하고 안정감"
    elif kind(["friend", "친구"]):
        role = f"너는 친구 {r_name}이고 {sender}에게 솔직히 응원한다."
        tone = "친근하고 솔직"
    elif kind(["연인", "lover", "boyfriend", "girlfriend", "남자친구", "여자친구"]):
        role = f"너는 연인 {r_name}이고 {sender}에게 애틋하게 말한다."
        tone = "애틋하고 다정"
    elif kind(["형", "누나", "오빠", "언니", "형제", "자매", "brother", "sister"]):
        role = f"너는 {r_name}(형제/자매)이고 든든히 응원한다."
        tone = "든든하고 친밀"
    elif kind(["선생", "teacher", "교수"]):
        role = f"너는 {r_name}(선생님)이고 지혜롭게 격려한다."
        tone = "존중·따뜻"
    else:
        role = f"너는 {r_type_raw} {r_name}이고 관계에 맞게 말한다."
        tone = "진솔·따뜻, 공감→위로→응원 흐름"

    deceased_tokens = ["돌아가신", "하늘", "하늘나라", "고인", "영면", "작고", "별세", "passed", "deceased", "in heaven"]
    is_deceased = any(t in r_note.lower() for t in [x.lower() for x in deceased_tokens])
    afterlife = "이미 세상을 떠난 설정, 안심과 응원 중심." if is_deceased else ""

    prompt = f"""
규칙:
- 한국어만. 반드시 1인칭(‘나’)으로 **{r_name}의 입장**에서 {sender}에게 직접 말할 것.
- 2~3문장, 180자 이내. 이모지/해시태그/따옴표/서명 금지.
- 문두에 수신자 호명 금지.
- 메타발화 금지.

역할/톤: {role} / {tone}. {afterlife}

수신자 정보: 이름 {r_name}, 성별 {r_gender}, 나이 {r_age}, 특이사항: {r_note or "없음"}

상황: 아래는 {sender}가 보낸 편지다. 너({r_name})가 그 편지를 읽고 바로 답장한다.

편지 원문:
{content}

출력: 조건을 지킨 답장 텍스트만.
"""
    return prompt.strip()


# --- 문장 유효성 체크 ---
SENT_PAT = re.compile(r"[^\s].*?(?:[.!?…]|[。？！]|(?:다|요)(?:\.|\s|$))")

def count_sentences_ko(text: str) -> int:
    return len([m.group(0).strip() for m in SENT_PAT.finditer(text.strip())])

def is_invalid_reply(text: str, receiver_name: str, sender_name: str):
    reasons, t = [], text.strip()
    if len(t) > 180:
        reasons.append("길이 180자 초과")
    n_sent = count_sentences_ko(t)
    if not (2 <= n_sent <= 3):
        reasons.append("문장 수 2~3 미준수")
    if not re.search(r"(?:^|[^가-힣])(나|내|난|나는|내가)(?:$|[^가-힣])", t):
        reasons.append("1인칭 표현 부족")
    if receiver_name and re.match(rf"^\s*{re.escape(receiver_name)}\s*[,·:]", t):
        reasons.append("문두 수신자 호명")
    if '"' in t or '“' in t or '”' in t:
        reasons.append("따옴표 포함")
    return len(reasons) > 0, reasons


def postprocess_reply(text: str) -> str:
    t = text.strip().replace("“", "").replace("”", "").replace("‘", "").replace("’", "").replace("`", "")
    return t.strip('"').replace("\n\n", "\n").strip()


# --- GPT 호출 ---
def generate_gpt_reply(letter):
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    user_prompt = build_dynamic_prompt(letter)
    system_prompt = "너는 규칙을 철저히 지키는 한국어 답장 생성기다."

    def llm_call(prompt):
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            max_tokens=200,
            temperature=0.2,
        )
        return resp.choices[0].message.content

    logger.debug(f"[GPT] Prompt:\n{user_prompt}")
    raw_reply = llm_call(user_prompt)
    logger.debug(f"[GPT] Raw reply: {raw_reply}")

    reply = postprocess_reply(raw_reply)
    invalid, reasons = is_invalid_reply(reply, letter.receiver_name, getattr(letter.user, 'nickname', ''))

    if invalid:
        logger.warning(f"[GPT] Reply invalid: {reasons}")
        retry_prompt = f"{user_prompt}\n\n규칙을 다시 지켜서 작성."
        raw_retry = llm_call(retry_prompt)
        logger.debug(f"[GPT] Retry raw reply: {raw_retry}")
        reply = postprocess_reply(raw_retry)

    logger.info(f"[GPT] Final reply: {reply}")
    return reply


# --- TTS 변환 ---
def synthesize_speech(text):
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="ko-KR",
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
    )
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
    logger.debug(f"[TTS] Generated audio size: {len(response.audio_content)} bytes")
    return response.audio_content


# --- S3 업로드 ---
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
    )
    url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{key}"
    logger.debug(f"[S3] Uploaded to: {url}")
    return url


# --- 메인 함수 ---
def make_ai_reply(letter):
    try:
        reply_text = generate_gpt_reply(letter)
        if not reply_text:
            logger.error("[AI] Empty reply text")
            reply_text = "[AI 답장 생성 실패]"

        mp3_data = synthesize_speech(reply_text)
        if not mp3_data:
            raise ValueError("TTS 변환 실패")

        filename = f"skyvoice_reply_{uuid.uuid4().hex}.mp3"
        s3_url = upload_mp3_to_s3(mp3_data, filename)

        letter.reply_text = reply_text
        letter.reply_voice_url = s3_url
        letter.replied_at = timezone.now()
        letter.save()

        logger.info(f"[AI] Reply saved: {reply_text[:30]}..., Voice URL: {s3_url}")
        return letter

    except Exception as e:
        logger.exception(f"[SkyVoice AI 오류] letter.id={letter.id}: {e}")
        return None