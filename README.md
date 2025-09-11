# SEO Value API (FastAPI)

Deploy on Render:
- Build: `pip install -r requirements.txt`
- Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`

Environment variables required:
- GADS_DEV_TOKEN
- GADS_CLIENT_ID
- GADS_CLIENT_SECRET
- GADS_REFRESH_TOKEN
- GADS_LOGIN_CUSTOMER_ID (optional)
- GOOGLE_ADS_CUSTOMER_ID (no dashes)
- DEFAULT_LANGUAGE_ID=1000
- DEFAULT_GEO_ID=2840
- SEO_KEY (long random secret; must match WordPress SEO_BACKEND_TOKEN)

Health check: `/healthz`
Main endpoint: `POST /estimate` with JSON `{"services":"plumber, drain cleaning"}` and header `X-SEO-KEY: <secret>`.
