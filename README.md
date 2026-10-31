# AI Gym Coach — Real-Time Exercise Form Assistant

**Maintained by Avdhoot Ukirde**  
A computer-vision workout assistant built with Python, Streamlit, MediaPipe Pose Landmarker, OpenCV and optional Groq-powered voice coaching.

This repository is a fork that is being maintained and customized. The upstream implementation and its original contributors should continue to receive appropriate attribution. Review the upstream project's licensing terms before redistributing or relicensing any inherited code or assets.

## Project overview

AI Gym Coach uses a webcam stream and MediaPipe pose landmarks to estimate exercise movement, count repetitions, display form-related metrics, and save workout summaries in a local SQLite database. If a Groq API key and internet access are configured, an optional language-model and text-to-speech pipeline can provide spoken coaching cues.

### Supported exercises

| Exercise | Rep-count signal | Additional displayed feedback |
|---|---|---|
| Squats | Knee angle | Knee angle, back angle and squat-depth state |
| Push-ups | Elbow angle | Body alignment and hip position |
| Dumbbell biceps curls | Elbow angle | Shoulder stability and torso-swing estimate |
| Shoulder press | Elbow angle | Arm extension and back-arch estimate |
| Lunges | Front knee angle | Torso angle and balance estimate |

The displayed form indicators are heuristic estimates based on 2D pose landmarks. They are not medical assessments, a substitute for a qualified trainer, or a guarantee that an exercise is safe or correctly performed.

## Main features

- Live webcam input through Streamlit WebRTC.
- MediaPipe Pose Landmarker inference on video frames.
- Five exercise-specific repetition detectors.
- On-frame pose skeleton and exercise feedback overlays.
- Workout plans with target sets and repetitions.
- Per-user workout history stored in SQLite.
- Optional Groq LLM coaching with gTTS audio output.
- Separate responsive HTML/CSS landing page.

## Technology stack

- **Language:** Python
- **Application UI:** Streamlit
- **Real-time video:** streamlit-webrtc, OpenCV, PyAV
- **Pose estimation:** MediaPipe Tasks — Pose Landmarker
- **Numerical processing:** NumPy
- **Workout history:** SQLite
- **Optional AI coaching:** Groq API
- **Text-to-speech:** gTTS
- **Landing page:** HTML5 and CSS3

## Repository structure

```text
ai-gym-coach/
├── LandingPage/
│   ├── index.html
│   ├── style.css
│   └── fonts/
├── Main App/
│   ├── main.py
│   ├── requirements.txt
│   ├── packages.txt
│   ├── .env.example
│   ├── core/
│   ├── detectors/
│   │   ├── biceps_curl.py
│   │   ├── lunges.py
│   │   ├── pushup.py
│   │   ├── shoulder_press.py
│   │   └── squat.py
│   ├── ml_models/
│   │   └── pose_landmarker_full.task
│   ├── services/
│   │   ├── auth/
│   │   ├── coaching/
│   │   ├── config/
│   │   ├── persistence/
│   │   ├── state/
│   │   ├── tracking/
│   │   ├── ui/
│   │   └── vision/
│   ├── static/
│   └── tutorial-info/
├── .gitignore
└── README.md
```

## Requirements

- Python **3.11** is the recommended starting point for this dependency set.
- A webcam or another camera accessible to the browser.
- A modern browser with camera permissions enabled.
- Internet access for package installation and optional Groq/gTTS services.
- A Groq API key only if you want AI-generated coaching feedback.

The MediaPipe model file is included at `Main App/ml_models/pose_landmarker_full.task`. Keep this file in place; the video processor loads it when the application starts.

<a id="quick-start"></a>

## Quick start — Windows

Open PowerShell in the repository folder:

```powershell
cd "Main App"
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `Main App/.env` and optionally add your Groq API key:

```dotenv
GROQ_API_KEY=your_groq_api_key_here
```

Start the application from inside the **Main App** directory:

```powershell
streamlit run main.py
```

Open the local URL printed by Streamlit (normally `http://localhost:8501`) and allow camera access when your browser asks.

## Quick start — macOS / Linux

```bash
cd "Main App"
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

Optionally add `GROQ_API_KEY=your_groq_api_key_here` to `Main App/.env`, then run:

```bash
streamlit run main.py
```

### Why run from Main App?

The application currently loads its model and static assets relative to the working directory. Running Streamlit from `Main App` ensures it can find `ml_models/pose_landmarker_full.task` and `static/` without changing paths.

## Configure optional AI coaching

The exercise tracking interface can run without a Groq key. Without one, pose detection, repetition counting and workout history remain available, but LLM-generated coaching and speech are disabled.

For local development, put the key in `Main App/.env`:

```dotenv
GROQ_API_KEY=your_groq_api_key_here
```

Never commit a real `.env` file, API key, or Streamlit secrets file. The repository ignores local secrets. For Streamlit Community Cloud, add `GROQ_API_KEY` in the app's Secrets settings instead of placing it in source code.

The voice feature also needs network access: Groq generates the coaching text and gTTS generates the audio. If either service is unavailable, the main workout interface should remain usable.

## How to use the app

1. Launch the Streamlit application.
2. Enter a username to create or reopen a local workout profile.
3. Choose an exercise, target sets and repetitions in the sidebar.
4. Select **Start Workout**.
5. Allow browser camera access and position your full body so the required joints are visible.
6. Follow the on-screen repetition count and exercise-specific feedback.
7. Select **End Workout** when finished.
8. Review saved workout summaries in the Workout History section.

The username screen is a lightweight profile selector, not secure account authentication. The SQLite database is stored locally at `Main App/data.db` and is excluded from Git.

## Deploy on Streamlit Community Cloud

1. Push this repository to GitHub.
2. In Streamlit Community Cloud, create an app using this repository and the `main` branch.
3. Set the app's **Main file path** to `Main App/main.py`.
4. Choose Python 3.11 in the advanced settings if available.
5. Add `GROQ_API_KEY` under the app's Secrets settings if you want AI coaching.
6. Deploy and review the app logs if dependency installation or startup fails.

The Python dependency file and system package file are stored beside the Streamlit entry point in `Main App/`. Camera access on a deployed site requires a secure browser context (HTTPS) and the user's permission. Check your hosting provider's support for WebRTC connections before relying on remote webcam access.

**Persistence note:** The included SQLite database is local to the running app. Some hosted environments have ephemeral storage, so workout history may not survive restarts or redeployments. Use a managed database if durable multi-user storage is required.

## Troubleshooting

| Symptom | Checks |
|---|---|
| Model file not found | Run Streamlit from `Main App` and confirm `ml_models/pose_landmarker_full.task` exists. |
| Camera does not start | Use localhost or HTTPS, grant camera permission, and check browser/host WebRTC support. |
| No pose detected | Improve lighting, move farther from the camera, and keep the relevant body joints visible. |
| AI coach is unavailable | Confirm `GROQ_API_KEY` is set correctly and that the host can reach Groq. |
| Spoken feedback is unavailable | Check internet connectivity; gTTS requires an external service. |
| Package installation fails | Use Python 3.11, recreate the virtual environment, and reinstall `Main App/requirements.txt`. |

## Landing page

Open `LandingPage/index.html` in a browser to view the project landing page. The landing page is a static introduction; the workout application itself runs separately through Streamlit.

## Safety and privacy

- Exercise feedback is an approximate computer-vision aid and can be wrong when landmarks are occluded, lighting is poor, or camera placement is unsuitable.
- Stop exercising if you experience pain, dizziness, or unusual discomfort. Seek guidance from a qualified professional when needed.
- The application processes live camera frames for pose estimation. Do not assume the video stream is end-to-end private; review the hosting and WebRTC configuration before using it with sensitive footage.
- Do not store API keys or private credentials in Git.

## Credits and attribution

This repository is a fork of an existing AI Gym Coach project. The inherited source structure, detector logic, model asset and other upstream materials are not represented as entirely original work by the maintainer of this fork. Please consult the upstream repository and its license before redistributing or relicensing inherited material.

## Maintainer

**Avdhoot Ukirde**  
GitHub: [@Avdhoot-Ukirde](https://github.com/Avdhoot-Ukirde)  
Email: [avdhootukirde106@gmail.com](mailto:avdhootukirde106@gmail.com)

---

If you improve the project, document the changes, test the relevant exercise detectors, and keep API keys and local workout databases out of version control.
