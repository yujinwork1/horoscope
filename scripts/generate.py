import os, json, re, time, html as htmllib, requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
         "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]


def get_week_label():
    mdt = datetime.now(ZoneInfo("America/Edmonton"))
    days_back = (mdt.weekday() - 3) % 7
    thursday = mdt - timedelta(days=days_back)
    wednesday = thursday + timedelta(days=6)
    fmt = lambda d: d.strftime("%b %-d")
    return f"{fmt(thursday)} \u2013 {fmt(wednesday)}"


def extract_json(text):
    """모델이 앞뒤에 설명이나 코드블록을 붙여도 JSON 부분만 뽑아낸다."""
    text = text.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON object found in response: {text[:300]}")
    return json.loads(text[start:end + 1])


def generate_horoscopes(week_label):
    api_key = os.environ["GROQ_API_KEY"]
    prompt = f"""You are a mystical, poetic astrologer writing weekly horoscopes for a community newspaper.
Generate horoscopes for all 12 zodiac signs for the week of {week_label}.

Rules:
- Each reading must be exactly 2 sentences (30-50 words total)
- Tone: mystical, warm, encouraging, slightly poetic
- Reference celestial bodies (planets, moon phases) naturally
- Each sign must feel distinct - vary the imagery, do not reuse the same opening or the same celestial body across signs
- Keep it general enough to resonate widely
- No doom or negativity - uplifting and empowering
- Plain text only: no HTML, no angle brackets, no backslashes

Return ONLY a valid JSON object, no markdown, no code blocks, no commentary:
{{"Aries":"...","Taurus":"...","Gemini":"...","Cancer":"...","Leo":"...","Virgo":"...","Libra":"...","Scorpio":"...","Sagittarius":"...","Capricorn":"...","Aquarius":"...","Pisces":"..."}}"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "max_tokens": 8000,
        "reasoning_effort": "low"
    }

    last_error = None
    for attempt in range(4):
        print(f"Attempt {attempt+1}/4 (model: {MODEL})...")
        try:
            res = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers, json=payload, timeout=90
            )
        except Exception as e:
            last_error = e
            print(f"Request failed: {e}")
            time.sleep(10)
            continue

        if res.status_code == 429 or res.status_code >= 500:
            wait = 15 + (attempt * 10)
            print(f"HTTP {res.status_code}, retrying in {wait}s...")
            last_error = f"HTTP {res.status_code}: {res.text[:300]}"
            time.sleep(wait)
            continue

        if res.status_code >= 400:
            # 401(키 문제), 404(모델 없음) 등은 재시도해도 소용없으니 바로 종료
            print(f"HTTP {res.status_code} - response body:")
            print(res.text[:1500])
            res.raise_for_status()

        data = res.json()
        choice = data["choices"][0]
        text = (choice["message"].get("content") or "").strip()

        if not text:
            last_error = f"Empty content (finish_reason: {choice.get('finish_reason')})"
            print(last_error)
            time.sleep(5)
            continue

        try:
            readings = extract_json(text)
        except Exception as e:
            last_error = e
            print(f"JSON parse failed, retrying: {e}")
            time.sleep(5)
            continue

        missing = [s for s in SIGNS if not str(readings.get(s, "")).strip()]
        if missing:
            last_error = f"Missing readings for: {missing}"
            print(last_error + ", retrying...")
            time.sleep(5)
            continue

        return readings

    raise Exception(f"Failed after 4 attempts. Last error: {last_error}")


def inject(readings, week_label):
    with open("index.html", "r", encoding="utf-8") as f:
        page = f.read()

    page, n = re.subn(
        r'(id="weekBadge"[^>]*>)([^<]*)',
        lambda m: m.group(1) + f"\u2726 {week_label} \u2726",
        page
    )
    if n == 0:
        print("Warning: weekBadge not found in index.html")

    not_found = []
    for sign in SIGNS:
        # html.escape: & < > " 를 안전하게 바꿔서 다음 주 정규식이 깨지지 않게 함
        safe = htmllib.escape(str(readings[sign]).strip(), quote=True)
        page, n = re.subn(
            rf'(<div class="hs-reading" data-sign="{sign}">)[^<]*(</div>)',
            lambda m, s=safe: m.group(1) + s + m.group(2),  # lambda라서 \ 문자도 안전
            page
        )
        if n == 0:
            not_found.append(sign)

    if not_found:
        raise Exception(f"Could not find reading slots in index.html for: {not_found}")

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(page)
    print(f"\u2726 Updated horoscope for {week_label}")


if __name__ == "__main__":
    week_label = get_week_label()
    print(f"Generating horoscopes for: {week_label}")
    readings = generate_horoscopes(week_label)
    print("Groq response OK:", list(readings.keys()))
    inject(readings, week_label)
