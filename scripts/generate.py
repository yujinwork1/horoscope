import os, json, requests, re, time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

def get_week_label():
    mdt = datetime.now(ZoneInfo("America/Edmonton"))
    days_back = (mdt.weekday() - 3) % 7
    thursday = mdt - timedelta(days=days_back)
    sunday = thursday + timedelta(days=6)
    fmt = lambda d: d.strftime("%b %-d")
    return f"{fmt(thursday)} – {fmt(sunday)}"

def generate_horoscopes(week_label):
    api_key = os.environ["GEMINI_API_KEY"]
    prompt = f"""You are a mystical, poetic astrologer writing weekly horoscopes for a community newspaper.
Generate horoscopes for all 12 zodiac signs for the week of {week_label}.

Rules:
- Each reading must be exactly 2 sentences (30-50 words total)
- Tone: mystical, warm, encouraging, slightly poetic
- Reference celestial bodies (planets, moon phases) naturally
- Keep it general enough to resonate widely
- No doom or negativity — uplifting and empowering

Return ONLY valid JSON, no markdown, no code blocks:
{{"Aries":"...","Taurus":"...","Gemini":"...","Cancer":"...","Leo":"...","Virgo":"...","Libra":"...","Scorpio":"...","Sagittarius":"...","Capricorn":"...","Aquarius":"...","Pisces":"..."}}"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.9, "maxOutputTokens": 1500}
    }

    for attempt in range(6):
        print(f"Attempt {attempt+1}/6...")
        try:
            res = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=60)
        except Exception as e:
            print(f"Request failed: {e}")
            time.sleep(20)
            continue

        if res.status_code == 429:
            wait = 20 + (attempt * 15)
            print(f"Rate limited (429), waiting {wait}s...")
            time.sleep(wait)
            continue

        res.raise_for_status()
        text = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'^```\s*', '', text)
        text = re.sub(r'\s*```$', '', text).strip()
        return json.loads(text)

    raise Exception("Gemini API rate limit exceeded after 6 attempts")

SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
         "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]

def inject(readings, week_label):
    with open("index.html", "r") as f:
        html = f.read()
    html = re.sub(r'(id="weekBadge"[^>]*>)([^<]*)', f'\\1✦ {week_label} ✦', html)
    for sign in SIGNS:
        reading = readings.get(sign, "")
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
    print("Gemini response OK:", list(readings.keys()))
    inject(readings, week_label)
