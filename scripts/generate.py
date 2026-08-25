import os, json, re, time, requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

MODEL = "openai/gpt-oss-120b"


def get_week_label():
    mdt = datetime.now(ZoneInfo("America/Edmonton"))
    days_back = (mdt.weekday() - 3) % 7
    thursday = mdt - timedelta(days=days_back)
    sunday = thursday + timedelta(days=6)
    fmt = lambda d: d.strftime("%b %-d")
    return f"{fmt(thursday)} – {fmt(sunday)}"


def generate_horoscopes(week_label):
    api_key = os.environ["GROQ_API_KEY"]
    prompt = f"""You are a mystical, poetic astrologer writing weekly horoscopes for a community newspaper.
Generate horoscopes for all 12 zodiac signs for the week of {week_label}.

Rules:
- Each reading must be exactly 2 sentences (30-50 words total)
- Tone: mystical, warm, encouraging, slightly poetic
- Reference celestial bodies (planets, moon phases) naturally
- Each sign must feel distinct — vary the imagery, do not reuse the same opening or the same celestial body across signs
- Keep it general enough to resonate widely
- No doom or negativity — uplifting and empowering

Return ONLY valid JSON, no markdown, no code blocks:
{{"Aries":"...","Taurus":"...","Gemini":"...","Cancer":"...","Leo":"...","Virgo":"...","Libra":"...","Scorpio":"...","Sagittarius":"...","Capricorn":"...","Aquarius":"...","Pisces":"..."}}"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "max_tokens": 4000,
        "reasoning_effort": "low",
        "reasoning_format": "hidden",
        "response_format": {"type": "json_object"}
    }

    for attempt in range(4):
        print(f"Attempt {attempt+1}/4 (model: {MODEL})...")
        try:
            res = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers, json=payload, timeout=60
            )
        except Exception as e:
            print(f"Request failed: {e}")
            time.sleep(10)
            continue

        if res.status_code == 429:
            wait = 15 + (attempt * 10)
            print(f"Rate limited, waiting {wait}s...")
            time.sleep(wait)
            continue

        if res.status_code >= 400:
            # 모델 종료/키 만료 등은 재시도해도 소용없으니 에러 본문을 그대로 출력
            print(f"HTTP {res.status_code} — response body:")
            print(res.text[:1000])
            res.raise_for_status()

        text = res.json()["choices"][0]["message"]["content"].strip()
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'^```\s*', '', text)
        text = re.sub(r'\s*```$', '', text).strip()
        return json.loads(text)

    raise Exception("Failed after 4 attempts")


SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
         "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]


def inject(readings, week_label):
    missing = [s for s in SIGNS if not readings.get(s)]
    if missing:
        raise Exception(f"Missing readings for: {missing}")

    with open("index.html", "r") as f:
        html = f.read()
    html = re.sub(r'(id="weekBadge"[^>]*>)([^<]*)', f'\\1✦ {week_label} ✦', html)
    for sign in SIGNS:
        reading = readings[sign]
        reading_escaped = reading.replace('"', '&quot;')
        html = re.sub(
            rf'(<div class="hs-reading" data-sign="{sign}">)[^<]*(</div>)',
            rf'\g<1>{reading_escaped}\2',
            html
        )
    with open("index.html", "w") as f:
        f.write(html)
    print(f"✦ Updated horoscope for {week_label}")


if __name__ == "__main__":
    week_label = get_week_label()
    print(f"Generating horoscopes for: {week_label}")
    readings = generate_horoscopes(week_label)
    print("Groq response OK:", list(readings.keys()))
    inject(readings, week_label)
