const { test, expect } = require("@playwright/test");
const { spawn } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "../..");
const artifactsDir = path.join(root, "artifacts", "smoke");
const frontendUrl = "http://127.0.0.1:3100";
let backend;
let frontend;

async function waitForBackend(request) {
  for (let index = 0; index < 120; index += 1) {
    try {
      const response = await request.get("http://127.0.0.1:8000/api/health");
      if (response.ok()) return;
    } catch (error) {
      // Keep polling until uvicorn is ready.
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw new Error("Backend did not become ready");
}

async function waitForFrontend(page) {
  for (let index = 0; index < 120; index += 1) {
    try {
      await page.goto(frontendUrl, { waitUntil: "domcontentloaded", timeout: 5000 });
      if (await page.getByRole("heading", { name: "ARGUS" }).isVisible()) {
        await page.waitForLoadState("networkidle", { timeout: 10000 }).catch(() => undefined);
        await page.waitForTimeout(1000);
        return;
      }
    } catch (error) {
      // Keep polling until Next.js is ready.
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw new Error("Next.js frontend did not become ready");
}

test.beforeAll(async ({ request }) => {
  fs.mkdirSync(artifactsDir, { recursive: true });
  const dbPath = path.join(root, "argus.db");
  if (fs.existsSync(dbPath)) fs.unlinkSync(dbPath);

  backend = spawn(
    path.join(root, ".venv", "Scripts", "python.exe"),
    ["-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
    {
      cwd: root,
      shell: false,
      stdio: "ignore",
      env: { ...process.env, ARGUS_MODE: "auto", ARGUS_MAX_SOURCE_QUERIES: "0" },
    },
  );
  await waitForBackend(request);

  frontend = spawn("cmd.exe", ["/c", "npm", "--prefix", "frontend", "run", "dev", "--", "--hostname", "127.0.0.1", "--port", "3100"], {
    cwd: root,
    shell: false,
    stdio: "ignore",
    env: { ...process.env, NEXT_PUBLIC_ARGUS_API_URL: "http://127.0.0.1:8000" },
  });
});

test.afterAll(async () => {
  if (frontend && !frontend.killed) {
    spawn("taskkill", ["/pid", String(frontend.pid), "/T", "/F"], { stdio: "ignore" });
  }
  if (backend && !backend.killed) backend.kill();
});

test("ARGUS Next.js command center smoke test", async ({ page }) => {
  test.setTimeout(240000);
  await page.setViewportSize({ width: 1440, height: 900 });
  const browserMessages = [];
  page.on("console", (message) => browserMessages.push(`${message.type()}: ${message.text()}`));
  page.on("pageerror", (error) => browserMessages.push(`pageerror: ${error.message}`));
  page.on("requestfailed", (request) => {
    if (request.url().includes("/api/research")) {
      browserMessages.push(`requestfailed: ${request.method()} ${request.url()} ${request.failure()?.errorText}`);
    }
  });
  page.on("response", (response) => {
    if (response.url().includes("/api/research")) {
      browserMessages.push(`response: ${response.request().method()} ${response.url()} ${response.status()}`);
    }
  });
  await waitForFrontend(page);
  await page.screenshot({ path: path.join(artifactsDir, "next-01-hero-dashboard.png") });

  await page.getByPlaceholder("Cardiologists in Chennai").fill("Cardiologists in Chennai");
  await page.getByRole("combobox").selectOption("offline");
  await page.waitForTimeout(250);
  await page.getByRole("button", { name: "Run Research" }).click();

  await expect(page.getByText("Research Progress")).toBeVisible();
  await expect(page.locator("section").filter({ hasText: "Research Progress" }).last()).toContainText(/running|completed|queued/i, { timeout: 15000 });
  await page.screenshot({ path: path.join(artifactsDir, "next-02-research-workspace.png") });
  await expect(page.getByRole("heading", { name: "Top Business Results" })).toBeVisible();
  const topRecommendation = page.locator("section").filter({ hasText: "Top Recommendation" }).first();
  await expect(topRecommendation).not.toContainText("Run research to identify", { timeout: 90000 });
  await expect(topRecommendation).not.toContainText("DNA--", { timeout: 90000 });
  await expect(topRecommendation).not.toContainText("RiskPending", { timeout: 90000 });
  try {
    await expect(page.getByRole("button", { name: /Intelligence/i })).toBeVisible({ timeout: 90000 });
  } catch (error) {
    throw new Error(`${error.message}\nBrowser messages:\n${browserMessages.join("\n")}`);
  }
  await page.getByRole("button", { name: /Intelligence/i }).click();
  await expect(page.getByText("Executive Intelligence")).toBeVisible({ timeout: 90000 });
  await expect(page.getByText("Most Important Findings")).toBeVisible({ timeout: 90000 });
  await page.screenshot({ path: path.join(artifactsDir, "next-03-executive-intelligence.png") });

  await page.getByRole("button", { name: /Evidence/i }).click();
  await expect(page.getByRole("heading", { name: "Evidence Graph" })).toBeVisible();
  await expect(page.getByText("Relationship Workspace")).toBeVisible();
  await page.screenshot({ path: path.join(artifactsDir, "next-04-evidence-graph.png") });

  await page.getByRole("button", { name: /Intelligence/i }).click();
  await expect(page.getByText("Most Important Findings")).toBeVisible();
  await page.screenshot({ path: path.join(artifactsDir, "next-05-editorial-insights.png") });

  await page.getByRole("button", { name: /Operations/i }).click();
  await expect(page.getByRole("heading", { name: "Challenge Coverage" })).toBeVisible();
  await expect(page.getByText("Coverage and System Health")).toBeVisible();
  await page.screenshot({ path: path.join(artifactsDir, "next-06-operations.png") });

  await page.getByRole("button", { name: /Intelligence/i }).click();
  await expect(page.getByText("Executive Scorecard")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Recommendations", exact: true })).toBeVisible();
  await page.getByRole("button", { name: /^Research Live progress/i }).click();
  await expect(page.getByRole("button", { name: "Download JSON" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Download CSV" })).toBeVisible();

  await page.goto(frontendUrl, { waitUntil: "domcontentloaded" });
  await page.waitForLoadState("networkidle", { timeout: 10000 }).catch(() => undefined);
  await page.getByPlaceholder("Cardiologists in Chennai").fill("Cardiologists in Chennai");
  await page.getByRole("combobox").selectOption("offline");
  await page.waitForTimeout(250);
  await page.getByRole("button", { name: "Run Research" }).click();
  await expect(page.getByRole("heading", { name: "Top Business Results" })).toBeVisible({ timeout: 90000 });
  await expect(page.getByText(/Cached research reused/i)).toBeVisible({ timeout: 90000 });
  const cachedTopRecommendation = page.locator("section").filter({ hasText: "Top Recommendation" }).first();
  await expect(cachedTopRecommendation).not.toContainText("Run research to identify", { timeout: 90000 });
  await expect(cachedTopRecommendation).not.toContainText("DNA--", { timeout: 90000 });
  await expect(page.getByRole("button", { name: "Run Research" })).toBeEnabled({ timeout: 90000 });

  await page.goto(frontendUrl, { waitUntil: "domcontentloaded" });
  await page.waitForLoadState("networkidle", { timeout: 10000 }).catch(() => undefined);
  await page.getByPlaceholder("Cardiologists in Chennai").fill("Restaurants in Tokyo");
  await page.getByRole("combobox").selectOption("offline");
  await page.waitForTimeout(250);
  await page.getByRole("button", { name: "Run Research" }).click();
  try {
    await expect(page.getByText("Unsupported Offline Query")).toBeVisible({ timeout: 90000 });
  } catch (error) {
    throw new Error(`${error.message}\nBrowser messages:\n${browserMessages.join("\n")}`);
  }
  await expect(page.getByText("No matching offline corpus was found for this query").first()).toBeVisible();
});
