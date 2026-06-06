# deploy-your-startup-website

A lightweight landing page built with [Astro](https://astro.build), deployed to
[Cloudflare Pages](https://pages.cloudflare.com) via GitHub Actions on push to `main`.

Live: https://deploy-your-startup.com

## Layout

```
.
├── frontend/                 # Astro site (the only module today)
│   ├── src/
│   ├── public/
│   ├── astro.config.mjs
│   └── package.json
└── .github/workflows/        # CI/CD
    └── deploy.yml            # build + push to Cloudflare Pages
```

The `frontend/` folder follows the modulith pattern used across our projects —
new modules (e.g. `backend/`, `ai/`) drop in as siblings without restructuring.

## Development

```bash
cd frontend
npm install
npm run dev      # http://localhost:4321
npm run build    # static output in frontend/dist/
```

## Deployment

Every push to `main` that touches `frontend/**` triggers
`.github/workflows/deploy.yml`. The workflow requires two repository secrets:

- `CLOUDFLARE_API_TOKEN` — scoped token with `Cloudflare Pages: Edit` and `Account: Read`
- `CLOUDFLARE_ACCOUNT_ID` — your Cloudflare account ID (`wrangler whoami` shows it)

Both are set automatically by `startup bootstrap` in pitch mode.

## Custom Domain

Configure deploy-your-startup.com as a custom domain in the
Cloudflare Pages project settings — Cloudflare provisions the certificate
automatically.
