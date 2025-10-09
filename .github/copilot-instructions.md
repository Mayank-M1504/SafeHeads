Purpose
-------
This file gives concise, actionable context for an AI coding agent working on this repository. It focuses on the architecture, developer workflows, project-specific patterns, integration points, and concrete examples so an agent can make correct code changes quickly.

High-level architecture
-----------------------
- Backend: `backend/app.py` is a Flask server that does video capture + MJPEG streaming (`/video_feed`) and exposes REST endpoints to control streaming, detection, ROI, model/device switching and to retrieve saved crop/analysis results.
- Core inference logic is encapsulated in `VideoInferenceProcessor` inside `backend/app.py` (model loading, device detection, detection modes, crop saving, Gemini integration).
- Frontend: `frontend/` is a React + Vite app (see `frontend/package.json`) that talks to the backend via REST endpoints and displays an MJPEG stream.
- Models and artifacts: YOLO model files live in the repository root and `backend/` (examples: `best.pt`, `best-helmet-2.pt`). Saved crops & outputs are in `backend/cropped_images`, `backend/helmet_saved`, and `backend/uploads`.

Why things are structured this way
---------------------------------
- Single-process Flask backend keeps inference, state (tracker, save interval, gemini results) and HTTP endpoints co-located for simplicity.
- MJPEG streaming via a generator function (`generate_frames`) avoids websockets and keeps the frontend simple (an <img src="/video_feed"> element).
- `load_yolo_model_safe` contains fragile fallback logic because ultralytics+PyTorch combinations sometimes fail; tests and helper scripts in the repo target that problem.

Key developer workflows (commands)
---------------------------------
All examples below are PowerShell-friendly.

Start backend (install deps first):
```powershell
cd backend
pip install -r requirements.txt
$env:GEMINI_API_KEY = "<your-key>"          # optional; set if using Gemini integration
python app.py
```

Start frontend (dev):
```powershell
cd frontend
npm install
npm run dev
```

There are convenience scripts in the repo root (`start.bat`, `start.sh`) — inspect them before changing startup behavior.

Important files & directories
-----------------------------
- `backend/app.py` — main server and `VideoInferenceProcessor` (model loading, inference, tracker, crop saving).
- `backend/requirements.txt` — pinned Python deps (ultralytics, torch version constraints).
- `best.pt`, `best-helmet-2.pt` — model files expected in the project root / backend.
- `backend/cropped_images`, `backend/helmet_saved`, `backend/uploads` — runtime artifacts that the server reads/writes.
- `fix_pytorch_loading.py`, `test_model_loading.py`, `setup_models.py` — helper scripts around model loading; consult them when touching `load_yolo_model_safe`.

Project-specific conventions & patterns
-------------------------------------
- Detection modes: use the string values `"vehicle"`, `"helmet"`, or `"both"` (set via `/set_detection_mode`).
- Confidence is a float in [0,1] and is exposed via `/set_confidence`.
- Vehicle classes are a list of integers (YOLO class indices). Use `/set_vehicle_classes` to change them.
- Crop file naming convention: `vehicle_{timestamp}_{i}_{WIDTHxHEIGHT}_conf{CONF:.2f}.jpg` — code may parse names for metadata.
- Minimum crop size defaults: width=135, height=332 (see `processor.min_crop_width/min_crop_height`). The server skips saving smaller crops.
- The code uses a greedy IOU tracker `SimpleTracker` to assign persistent IDs; expect tracking logic when adding/change detections.

Integration points / gotchas
---------------------------
- Model loading can fail across PyTorch/ultralytics versions. `load_yolo_model_safe()` implements 3 fallback strategies (safe globals, monkeypatch torch.load to weights_only=False, set TORCH_SERIALIZATION_WEIGHTS_ONLY env var). When updating ultralytics or torch, run `test_model_loading.py`.
- Gemini (Generative AI) integration is optional and controlled by `GEMINI_API_KEY` (read from `.env` via python-dotenv). The server queues Gemini calls via a ThreadPoolExecutor — be mindful of blocking changes.
- Streaming endpoint `/video_feed` will return 404 if `processor.is_streaming` is False; clients should start stream via `/start_stream` first.
- Device switching is supported at runtime via `/switch_device` (POST JSON: `{ "device": "cpu" }` or `"cuda:0"`) — the server attempts to move models and may fall back to CPU.

Useful examples (PowerShell)
----------------------------
Start streaming from default camera (Invoke-RestMethod returns JSON):
```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:5000/start_stream -Body (ConvertTo-Json @{ source_type='camera'; source=0 }) -ContentType 'application/json'
```

Start streaming from a video file:
```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:5000/start_stream -Body (ConvertTo-Json @{ source_type='video'; source='backend/test.mp4' }) -ContentType 'application/json'
```

Switch device to CPU:
```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:5000/switch_device -Body (ConvertTo-Json @{ device='cpu' }) -ContentType 'application/json'
```

Toggle detection on/off:
```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:5000/toggle_detection
```

Where to look when things break
-------------------------------
- Model load errors: check console logs from `load_yolo_model_safe` and run `fix_pytorch_loading.py` / `test_model_loading.py`.
- No stream or 404 at `/video_feed`: ensure you called `/start_stream` and that `processor.is_streaming` is True.
- No detections: verify `processor.confidence_threshold` and `processor.vehicle_classes` and that correct models are loaded.

When to ask the human
----------------------
- If a change requires different model file names/locations. The repo uses `best.pt` and `best-helmet-2.pt` by default.
- If you need to change the inference architecture (e.g., switch to websockets) — this touches frontend + backend.

If any section is unclear or you need a deeper walkthrough of a specific file (for example `VideoInferenceProcessor.generate_frames` or `load_yolo_model_safe`), tell me which file and I will expand with examples and call sites.
