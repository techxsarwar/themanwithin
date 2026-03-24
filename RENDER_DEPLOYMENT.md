# Deploying to Render

This codebase is now fully configured to run a Python FastAPI backend that serves your website and handles contact form submissions.

To get this live on Render, follow these steps:

1. **Push your code to GitHub**
   Ensure all the files in this directory (`main.py`, `requirements.txt`, `render.yaml`, `index.html`, etc.) are pushed to a GitHub repository.

2. **Connect to Render using Blueprint**
   - Log in to your [Render dashboard](https://dashboard.render.com).
   - Click the "New" button and select **Blueprint**.
   - Connect your GitHub repository.
   - Render will automatically read the `render.yaml` file and set up a Web Service with the correct `Start Command` (`uvicorn backend.main:app --host 0.0.0.0 --port 10000`) and Environment (`Python`).

3. **Manual Setup (If not using Blueprint)**
   - Click "New" -> **Web Service**.
   - Select your GitHub repository.
   - Set **Environment** to `Python 3`.
   - Set **Build Command** to `pip install -r backend/requirements.txt`
   - Set **Start Command** to `uvicorn backend.main:app --host 0.0.0.0 --port 10000`
   - Click "Create Web Service".

Your website will then be built and deployed! The "Contact" form will now interact with your deployed FastAPI backend, and you can see contact submissions in your Render dashboard logs.
