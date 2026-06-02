import { spawn } from "child_process";
import http from "http";
import fs from "fs";

const PORT = 8787;
const BASE_URL = `http://127.0.0.1:${PORT}`;
const PASSWORD = "test-secret-pass";
const VARS_FILE = ".dev.vars";

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function fetchText(url: string, options: any = {}): Promise<{ status: number; text: string; headers: http.IncomingHttpHeaders }> {
  return new Promise((resolve, reject) => {
    const req = http.request(url, options, (res) => {
      let data = "";
      res.on("data", (chunk) => {
        data += chunk;
      });
      res.on("end", () => {
        resolve({
          status: res.statusCode || 0,
          text: data,
          headers: res.headers,
        });
      });
    });
    req.on("error", (err) => {
      reject(err);
    });
    if (options.body) {
      req.write(options.body);
    }
    req.end();
  });
}

async function runTests() {
  console.log("Writing temporary .dev.vars for Wrangler...");
  fs.writeFileSync(VARS_FILE, `FANCYQR_PASSWORD=${PASSWORD}\n`);

  console.log("Starting local Wrangler dev server...");
  
  // Start wrangler dev in the background
  const devServer = spawn("npx", ["wrangler", "dev", "--port", String(PORT)], {
    shell: true,
  });

  // Log server output to help diagnose issues if any
  devServer.stdout.on("data", (data) => {
    // console.log(`[Wrangler] ${data}`);
  });
  devServer.stderr.on("data", (data) => {
    // console.error(`[Wrangler Error] ${data}`);
  });

  let isHealthy = false;
  console.log("Waiting for Wrangler dev server to start...");
  for (let i = 0; i < 20; i++) {
    await delay(1000);
    try {
      const res = await fetchText(`${BASE_URL}/`);
      if (res.status === 200) {
        isHealthy = true;
        break;
      }
    } catch {
      // Server not ready yet
    }
  }

  if (!isHealthy) {
    devServer.kill("SIGTERM");
    cleanupVars();
    throw new Error("Wrangler dev server failed to start or did not become healthy.");
  }

  console.log("Wrangler dev server is up and healthy! Running test cases...");

  try {
    // Test Case 1: Check Index Page serving
    console.log("\n--- Test Case 1: Fetching Index Page ---");
    const indexRes = await fetchText(`${BASE_URL}/`);
    if (indexRes.status !== 200 || !indexRes.text.includes("FancyQR Generator")) {
      throw new Error(`Index page failed. Status: ${indexRes.status}, contains 'FancyQR Generator': ${indexRes.text.includes("FancyQR Generator")}`);
    }
    console.log("PASS: Index page returned 200 and contains expected HTML.");

    // Test Case 2: Check QR Generation
    console.log("\n--- Test Case 2: Generating styled QR Code SVG ---");
    const qrRes = await fetchText(`${BASE_URL}/generate?data=https://github.com&logo=true&ec=H`);
    if (qrRes.status !== 200 || qrRes.headers["content-type"] !== "image/svg+xml") {
      throw new Error(`QR generation failed. Status: ${qrRes.status}, Content-Type: ${qrRes.headers["content-type"]}`);
    }
    if (!qrRes.text.startsWith("<?xml") || !qrRes.text.includes("<svg")) {
      throw new Error(`QR SVG content is invalid. Output starts with: ${qrRes.text.slice(0, 100)}`);
    }
    console.log("PASS: Generated styled QR code SVG successfully with content-type 'image/svg+xml'.");

    // Test Case 3: Shorten URL - Unauthorized
    console.log("\n--- Test Case 3: Shorten URL without password (Should be unauthorized) ---");
    const unauthRes = await fetchText(`${BASE_URL}/shorten`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ url: "https://example.com" }),
    });
    if (unauthRes.status !== 401) {
      throw new Error(`Expected 401 Unauthorized, got: ${unauthRes.status}`);
    }
    console.log("PASS: Unauthorized shorten request rejected with 401.");

    // Test Case 4: Shorten URL - Authorized
    console.log("\n--- Test Case 4: Shorten URL with correct password ---");
    const shortenRes = await fetchText(`${BASE_URL}/shorten`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-FancyQR-Password": PASSWORD,
      },
      body: JSON.stringify({ url: "https://example.com/target-destination", slug: "custom" }),
    });
    if (shortenRes.status !== 200) {
      throw new Error(`Expected 200 OK, got: ${shortenRes.status}, body: ${shortenRes.text}`);
    }
    const shortenBody = JSON.parse(shortenRes.text);
    if (shortenBody.slug !== "custom" || shortenBody.url !== "https://example.com/target-destination") {
      throw new Error(`Unexpected body content: ${shortenRes.text}`);
    }
    console.log("PASS: URL shortened successfully under custom slug 'custom'.");

    // Test Case 5: Redirect and Click Tracking
    console.log("\n--- Test Case 5: Visiting shortened URL and verifying redirect ---");
    const redirectRes = await fetchText(`${BASE_URL}/custom`, {
      method: "GET",
      headers: {
        "User-Agent": "TestUserAgent/1.0",
        "Referer": "http://test-referer.com",
      },
    });
    if (redirectRes.status !== 302 || redirectRes.headers["location"] !== "https://example.com/target-destination") {
      throw new Error(`Redirect failed. Status: ${redirectRes.status}, Location: ${redirectRes.headers["location"]}`);
    }
    console.log("PASS: Short URL redirected to target URL with status 302.");

    // Test Case 6: Stats Analytics Retrieval
    console.log("\n--- Test Case 6: Fetching analytics stats for slug 'custom' ---");
    const statsRes = await fetchText(`${BASE_URL}/api/stats/custom`, {
      headers: {
        "X-FancyQR-Password": PASSWORD,
      },
    });
    if (statsRes.status !== 200) {
      throw new Error(`Stats fetching failed. Status: ${statsRes.status}, body: ${statsRes.text}`);
    }
    const statsBody = JSON.parse(statsRes.text);
    if (statsBody.clicks !== 1 || statsBody.url !== "https://example.com/target-destination") {
      throw new Error(`Clicks or URL in stats is incorrect: ${statsRes.text}`);
    }
    if (statsBody.recent_visits.length !== 1 || statsBody.recent_visits[0].user_agent !== "TestUserAgent/1.0") {
      throw new Error(`Recent visits tracking is incorrect: ${statsRes.text}`);
    }
    console.log("PASS: Analytics returned correct clicks (1) and logged visit details.");

    console.log("\n=========================");
    console.log("🎉 ALL INTEGRATION TESTS PASSED PERFECTLY!");
    console.log("=========================");
  } finally {
    console.log("\nStopping Wrangler dev server...");
    devServer.kill("SIGTERM");
    cleanupVars();
    // Ensure background processes are cleaned up
    await delay(1000);
  }
}

function cleanupVars() {
  try {
    if (fs.existsSync(VARS_FILE)) {
      fs.unlinkSync(VARS_FILE);
      console.log("Removed temporary .dev.vars file.");
    }
  } catch (e) {
    console.error("Warning: Failed to remove temporary .dev.vars:", e);
  }
}

runTests().catch((err) => {
  console.error("❌ TEST RUN FAILED:", err);
  cleanupVars();
  process.exit(1);
});
