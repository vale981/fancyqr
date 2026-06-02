# FancyQR (Cloudflare Workers + HonoJS + D1 Database)

FancyQR is a serverless styled SVG QR Code Generator and a built-in, password-protected URL shortener with visit analytics. The project has been rewritten from Python/FastAPI to TypeScript, running on **Cloudflare Workers**, utilizing the **HonoJS** router, and storing link analytics in a serverless **Cloudflare D1** SQLite database.

## Architecture & Tech Stack

- **Runtime & Deployment:** [Cloudflare Workers](https://workers.cloudflare.com/) (high performance, serverless edge-computing platform).
- **Web Framework:** [HonoJS](https://hono.dev/) (ultralight, type-safe, sub-millisecond routing).
- **Database:** [Cloudflare D1](https://developers.cloudflare.com/d1/) (serverless SQL database built on SQLite).
- **QR Code Engine:** Core custom SVG path generator ported from Python with exact rendering accuracy (independent custom eyes and horizontal neighbor anti-aliased module bars, and dynamic logo scaling and embedding).
- **Frontend Serving:** Serving index, dashboard, and stats pages directly from worker edge memory for instant loading.

---

## Getting Started

### Development Environment with Nix

This project provides a native Nix flake to provision the development environment. To enter the shell with the required tools (Node.js 22, TypeScript Language Server, and npm):

```bash
nix develop
```

### 1. Installation

Install npm dependencies (including Hono, Wrangler, TypeScript, and QR Code generation packages):

```bash
npm install
```

### 2. Local Database Initialization

Initialize your local Cloudflare D1 development database and apply the table definitions from `schema.sql`:

```bash
npx wrangler d1 execute fancyqr-db --local --file=schema.sql
```

### 3. Run Automated Integration Tests

To run end-to-end integration tests (which verifies page rendering, SVG QR generation, password security, URL shortening, redirect behaviors, and click-tracking analytics):

```bash
npx tsx test-integration.ts
```

### 4. Local Development Server

To start Wrangler's local development emulator (hosting on `http://127.0.0.1:8787`):

```bash
npm run dev
```

---

## Configuration & Environments

The worker is configured using environment variables:

- `FANCYQR_PASSWORD`: Sets a password to protect the URL shortening endpoints, listing, and statistics.

### Local Development
To configure your local password, create a `.dev.vars` file in the root of your project:
```env
FANCYQR_PASSWORD=your-secret-password
```

### Production Deployment
Before deploying to production, upload your `FANCYQR_PASSWORD` securely as a Wrangler Secret:
```bash
npx wrangler secret put FANCYQR_PASSWORD
```

---

## Cloudflare Production Deployment

There are two ways to deploy your application to Cloudflare's global edge network:

---

### Option A: Secure Continuous Deployment via Cloudflare Dashboard (Recommended)

If you are hosting your repository in a **public GitHub repository**, you can deploy automatically on every push without committing your private D1 Database UUIDs to Git by injecting the database ID at build-time.

#### 1. Create a remote D1 database
Run this command once in your local terminal to create your live database:
```bash
npx wrangler d1 create fancyqr-db
```
*Make a note of the returned database UUID (e.g., `4ab04e1c-0712-31d5-4e63-782f766e5b56`).*

#### 2. Apply migrations to your live D1 database
```bash
npx wrangler d1 execute fancyqr-db --remote --file=schema.sql
```

#### 3. Connect Repository on the Cloudflare Dashboard
1. Log in to your **Cloudflare Dashboard** and navigate to your Worker project (**Workers & Pages** -> **fancyqr**).
2. Go to the **Settings** tab.
3. Click on **Builds** (or **Build & deployments**) in the left sidebar and click **Edit**.
4. Set the **Build command** to:
   ```bash
   sed -i "s/your-d1-database-id/$D1_DATABASE_ID/g" wrangler.toml
   ```
5. Leave the **Build output directory** blank.
6. Scroll down to the **Environment variables** section and click **Add variable**:
   * **Name:** `D1_DATABASE_ID`
   * **Value:** *(Paste your real production D1 database UUID here)*
7. Click **Save and Deploy**.

Now, whenever you push code to GitHub, Cloudflare's CI will securely inject your production database ID and deploy your worker automatically!

---

### Option B: Manual CLI Deployment

For private repositories or direct local-to-production manual deploys:

#### 1. Create a remote D1 database
```bash
npx wrangler d1 create fancyqr-db
```

#### 2. Apply migrations to the production D1 database
```bash
npx wrangler d1 execute fancyqr-db --remote --file=schema.sql
```

#### 3. Update `wrangler.toml`
Open `wrangler.toml` and replace `your-d1-database-id` with your real database UUID:
```toml
database_id = "4ab04e1c-0712-31d5-4e63-782f766e5b56"
```

#### 4. Upload your secret password
Set your dashboard admin password securely in Cloudflare:
```bash
npx wrangler secret put FANCYQR_PASSWORD
```

#### 5. Deploy your Worker
```bash
npm run deploy
```

---

## License

MIT License. See `LICENSE` for details.
