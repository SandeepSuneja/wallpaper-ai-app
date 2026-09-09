# Wallcraft

AI wallpapers powered by **FLUX.2-klein-base-4B**.

- **Web (Angular):** landscape desktop wallpapers — `frontend/`
- **Mobile (Flutter):** portrait phone wallpapers — `mobile/`
- **Backend (FastAPI):** shared generation API — `backend/`

Steps / guidance / seed are chosen automatically from the selected resolution (not shown in the UI).

## Quick start

### 1. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install git+https://github.com/huggingface/diffusers.git
copy .env.example .env
set PYTHONPATH=.
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

API docs: http://127.0.0.1:8001/docs

### 2. Web app

```bash
cd frontend
npm install
npm start
```

App: http://localhost:4200

### 3. Mobile app

```bash
cd mobile
flutter pub get
# Android emulator (default API host is 10.0.2.2:8001):
flutter run
# Physical device — use your PC LAN IP:
flutter run --dart-define=API_BASE=http://192.168.x.x:8001
```

## Resolutions & quality mapping

### Web (landscape)

| Preset | Size | Steps | Guidance |
|--------|------|-------|----------|
| Full HD | 1920×1080 | 32 | 4.0 |
| QHD | 2560×1440 | 36 | 4.0 |
| 4K UHD | 3840×2160 | 40 | 4.0 |
| Ultrawide | 2560×1080 | 36 | 4.0 |

### Mobile (portrait)

| Preset | Size | Steps | Guidance |
|--------|------|-------|----------|
| Phone FHD | 1080×1920 | 32 | 4.0 |
| Phone QHD | 1440×2560 | 36 | 4.0 |
| Tablet | 1600×2560 | 36 | 4.0 |

Seed is random each run unless provided by an API client.

## Set as wallpaper

- **Web:** “Set as background” / “Set as lock screen” downloads the PNG and shows OS instructions (browsers cannot set desktop wallpaper directly).
- **Android:** applies home / lock screen via system wallpaper APIs.
- **iOS:** saves to Photos; user sets wallpaper from the Photos share sheet (Apple restriction).

## API

- `GET /api/health`
- `GET /api/presets?orientation=landscape|portrait`
- `GET /api/gallery?orientation=landscape|portrait`
- `POST /api/generate`
- `POST /api/images/{id}/publish`
- `GET /api/images/{id}`
