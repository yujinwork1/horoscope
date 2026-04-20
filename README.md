# Meridian Source — Weekly Horoscope

매주 목요일 6AM MDT에 Gemini AI가 자동으로 운세를 업데이트합니다.

## 세팅 방법 (딱 한 번만!)

### 1. GitHub 레포 만들기
1. [github.com](https://github.com) 로그인
2. **New repository** 클릭
3. Repository name: `horoscope` (또는 원하는 이름)
4. **Public** 선택 (GitHub Pages 무료 사용)
5. **Create repository**

### 2. 파일 업로드
이 폴더 안의 파일들을 모두 GitHub에 업로드:
- `index.html`
- `scripts/generate.py`
- `.github/workflows/update-horoscope.yml`

> 팁: GitHub 레포 페이지에서 **Add file → Upload files** 로 드래그앤드롭 가능

### 3. Gemini API 키 등록
1. GitHub 레포 → **Settings** 탭
2. 왼쪽 메뉴 → **Secrets and variables → Actions**
3. **New repository secret** 클릭
4. Name: `GEMINI_API_KEY`
5. Secret: 발급받은 Gemini API 키 붙여넣기
6. **Add secret**

### 4. GitHub Pages 켜기
1. GitHub 레포 → **Settings** 탭
2. 왼쪽 메뉴 → **Pages**
3. Source: **Deploy from a branch**
4. Branch: `main` / `/ (root)`
5. **Save**

잠시 후 `https://[username].github.io/horoscope/` 주소로 접근 가능!

### 5. WordPress 임베드
```html
<iframe 
  src="https://[username].github.io/horoscope/" 
  width="100%" 
  height="2000px" 
  frameborder="0"
  scrolling="no">
</iframe>
```

## 수동 업데이트
GitHub 레포 → **Actions** 탭 → **Update Weekly Horoscope** → **Run workflow**
