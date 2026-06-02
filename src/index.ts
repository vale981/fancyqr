import { Hono } from "hono";
import { generateQrSvg, parseColor } from "./fancy_qr";

// Text assets bundled by Wrangler/esbuild
import indexHtml from "../static/index.html";
import dashboardHtml from "../static/dashboard.html";
import statsHtml from "../static/stats.html";
import logoSvg from "../logo.svg";

type Bindings = {
  DB: D1Database;
  FANCYQR_PASSWORD?: string;
};

const app = new Hono<{ Bindings: Bindings }>();

// Helper for basic password protection
function isAuthorized(passwordHeader: string | undefined, requiredPassword?: string): boolean {
  if (requiredPassword) {
    const trimmed = requiredPassword.trim();
    if (trimmed && passwordHeader !== trimmed) {
      return false;
    }
  }
  return true;
}

// Helper to generate a random slug
function generateSlug(length = 6): string {
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  let result = "";
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

// 1. QR Code Generation Endpoint
app.get("/generate", async (c) => {
  const data = c.req.query("data");
  if (!data) {
    return c.text("Error: Missing 'data' query parameter", 400);
  }

  const fc = c.req.query("fc") || "#ff9232";
  const bc = c.req.query("bc") || "255,255,255,0";
  const sizeQuery = parseInt(c.req.query("size") || "100", 10);
  const size = Math.max(10, Math.min(500, isNaN(sizeQuery) ? 100 : sizeQuery));
  
  const ecQuery = c.req.query("ec") || "L";
  const ec = ["L", "M", "Q", "H"].includes(ecQuery) ? (ecQuery as "L" | "M" | "Q" | "H") : "L";

  const logo = c.req.query("logo") === "true";
  
  const lsQuery = parseFloat(c.req.query("ls") || "0.9");
  const ls = Math.max(0.1, Math.min(1.0, isNaN(lsQuery) ? 0.9 : lsQuery));
  
  const lmQuery = parseFloat(c.req.query("lm") || "0.2");
  const lm = Math.max(0.1, Math.min(0.5, isNaN(lmQuery) ? 0.2 : lmQuery));

  try {
    const frontColor = parseColor(fc);
    const backColor = parseColor(bc);

    const svgContent = generateQrSvg(
      data,
      frontColor,
      backColor,
      size,
      ec,
      logo,
      ls,
      lm,
      logoSvg
    );

    c.header("Content-Type", "image/svg+xml");
    return c.body(svgContent);
  } catch (err: any) {
    return c.text(`Error: ${err.message}`, 400);
  }
});

// 2. Shorten URL Endpoint
app.post("/shorten", async (c) => {
  const authHeader = c.req.header("X-FancyQR-Password");
  if (!isAuthorized(authHeader, c.env.FANCYQR_PASSWORD)) {
    return c.json({ detail: "Unauthorized: Invalid password" }, 401);
  }

  let body: { url: string; slug?: string };
  try {
    body = await c.req.json();
  } catch {
    return c.json({ detail: "Invalid JSON body" }, 400);
  }

  const { url, slug } = body;
  if (!url) {
    return c.json({ detail: "URL is required" }, 400);
  }

  let activeSlug = slug ? slug.trim() : "";
  if (activeSlug) {
    if (activeSlug.length < 1 || activeSlug.length > 50) {
      return c.json({ detail: "Slug must be between 1 and 50 characters" }, 400);
    }
    // Check if slug already exists
    const existing = await c.env.DB.prepare("SELECT slug FROM links WHERE slug = ?")
      .bind(activeSlug)
      .first<{ slug: string }>();
    if (existing) {
      return c.json({ detail: `Slug '${activeSlug}' already exists` }, 400);
    }
  } else {
    // Generate unique slug
    let attempts = 0;
    while (attempts < 10) {
      activeSlug = generateSlug();
      const existing = await c.env.DB.prepare("SELECT slug FROM links WHERE slug = ?")
        .bind(activeSlug)
        .first<{ slug: string }>();
      if (!existing) break;
      attempts++;
    }
    if (attempts === 10) {
      return c.json({ detail: "Failed to generate a unique slug" }, 500);
    }
  }

  try {
    await c.env.DB.prepare("INSERT INTO links (slug, url) VALUES (?, ?)")
      .bind(activeSlug, url)
      .run();
    return c.json({ slug: activeSlug, url });
  } catch (err: any) {
    return c.json({ detail: err.message }, 500);
  }
});

// 3. List Links Endpoint
app.get("/links", async (c) => {
  const authHeader = c.req.header("X-FancyQR-Password");
  if (!isAuthorized(authHeader, c.env.FANCYQR_PASSWORD)) {
    return c.json({ detail: "Unauthorized" }, 401);
  }

  try {
    const { results } = await c.env.DB.prepare(
      "SELECT slug, url, clicks, created_at FROM links ORDER BY created_at DESC"
    ).all<{ slug: string; url: string; clicks: number; created_at: string }>();

    return c.json(results);
  } catch (err: any) {
    return c.json({ detail: err.message }, 500);
  }
});

// 4. Update Link Endpoint
app.patch("/links/:slug", async (c) => {
  const authHeader = c.req.header("X-FancyQR-Password");
  if (!isAuthorized(authHeader, c.env.FANCYQR_PASSWORD)) {
    return c.json({ detail: "Unauthorized" }, 401);
  }

  const slug = c.req.param("slug");
  let body: { url: string };
  try {
    body = await c.req.json();
  } catch {
    return c.json({ detail: "Invalid JSON body" }, 400);
  }

  if (!body.url) {
    return c.json({ detail: "URL is required" }, 400);
  }

  try {
    const result = await c.env.DB.prepare("UPDATE links SET url = ? WHERE slug = ?")
      .bind(body.url, slug)
      .run();
    
    if (result.meta.changes === 0) {
      return c.json({ detail: "Link not found" }, 404);
    }
    return c.json({ status: "updated", slug, url: body.url });
  } catch (err: any) {
    return c.json({ detail: err.message }, 500);
  }
});

// 5. Delete Link Endpoint
app.delete("/links/:slug", async (c) => {
  const authHeader = c.req.header("X-FancyQR-Password");
  if (!isAuthorized(authHeader, c.env.FANCYQR_PASSWORD)) {
    return c.json({ detail: "Unauthorized" }, 401);
  }

  const slug = c.req.param("slug");

  try {
    // Delete in batch
    await c.env.DB.batch([
      c.env.DB.prepare("DELETE FROM visits WHERE slug = ?").bind(slug),
      c.env.DB.prepare("DELETE FROM links WHERE slug = ?").bind(slug)
    ]);
    return c.json({ status: "deleted", slug });
  } catch (err: any) {
    return c.json({ detail: err.message }, 500);
  }
});

// 6. Get Link Analytics Endpoint (API)
app.get("/api/stats/:slug", async (c) => {
  const authHeader = c.req.header("X-FancyQR-Password");
  if (!isAuthorized(authHeader, c.env.FANCYQR_PASSWORD)) {
    return c.json({ detail: "Unauthorized: Invalid password" }, 401);
  }

  const slug = c.req.param("slug");

  try {
    const linkResult = await c.env.DB.prepare("SELECT url, clicks, created_at FROM links WHERE slug = ?")
      .bind(slug)
      .first<{ url: string; clicks: number; created_at: string }>();

    if (!linkResult) {
      return c.json({ detail: "Slug not found" }, 404);
    }

    const visitsResult = await c.env.DB.prepare(
      "SELECT timestamp, user_agent FROM visits WHERE slug = ? ORDER BY timestamp DESC LIMIT 10"
    )
      .bind(slug)
      .all<{ timestamp: string; user_agent: string }>();

    return c.json({
      url: linkResult.url,
      clicks: linkResult.clicks,
      created_at: linkResult.created_at,
      recent_visits: visitsResult.results.map((v) => ({
        timestamp: v.timestamp,
        user_agent: v.user_agent
      }))
    });
  } catch (err: any) {
    return c.json({ detail: err.message }, 500);
  }
});

// 7. Pages Serving Endpoints (Self-contained via text asset imports)
app.get("/", (c) => {
  return c.html(indexHtml);
});

app.get("/dashboard", (c) => {
  return c.html(dashboardHtml);
});

app.get("/stats/:slug", (c) => {
  return c.html(statsHtml);
});

// 8. Redirect Handler (Must be registered last to avoid routing conflicts)
app.get("/:slug", async (c) => {
  const slug = c.req.param("slug");
  
  if (slug === "favicon.ico") {
    return c.notFound();
  }

  try {
    const linkResult = await c.env.DB.prepare("SELECT url FROM links WHERE slug = ?")
      .bind(slug)
      .first<{ url: string }>();

    if (linkResult) {
      const userAgent = c.req.header("user-agent") || null;
      const referer = c.req.header("referer") || null;

      // Record visit and increment click count in batch
      await c.env.DB.batch([
        c.env.DB.prepare("UPDATE links SET clicks = clicks + 1 WHERE slug = ?").bind(slug),
        c.env.DB.prepare("INSERT INTO visits (slug, user_agent, referer) VALUES (?, ?, ?)").bind(slug, userAgent, referer)
      ]);

      return c.redirect(linkResult.url);
    }

    return c.text("Not found", 404);
  } catch (err: any) {
    return c.text(`Internal Server Error: ${err.message}`, 500);
  }
});

export default app;
