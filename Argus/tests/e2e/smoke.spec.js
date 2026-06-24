const { test, expect } = require("@playwright/test");
const { spawn } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "../..");
const artifactsDir = path.join(root, "artifacts", "smoke");
let server;

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

test.beforeAll(async ({ request }) => {
  fs.mkdirSync(artifactsDir, { recursive: true });
  const dbPath = path.join(root, "argus.db");
  if (fs.existsSync(dbPath)) fs.unlinkSync(dbPath);
  server = spawn(
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
});

test.afterAll(async () => {
  if (server && !server.killed) {
    server.kill();
  }
});

test("ARGUS research smoke test", async ({ page }) => {
  test.setTimeout(240000);
  await page.goto(`file://${path.join(root, "index.html").replaceAll("\\", "/")}`);
  await expect(page.getByRole("heading", { name: "ARGUS" })).toBeVisible();

  await page.locator("#queryInput").fill("Cardiologists in Chennai");
  await page.getByRole("button", { name: /Run/i }).click();

  await expect(page.locator("#runState")).toContainText(/Queued|Running|Complete/, { timeout: 10000 });
  await expect(page.locator("#timelineList")).toContainText(/queued|Stage changed|Research started/i, { timeout: 10000 });
  await expect(page.locator("#metricBusinesses")).toHaveText("8", { timeout: 80000 });
  await expect(page.locator("#modeIndicator")).toContainText("Active Mode");
  await expect(page.locator("#reportChallengeMetrics")).toContainText("Fallback used");
  await expect(page.locator("#businessGrid .business-card").first()).toBeVisible();
  await expect(page.getByText(/DNA score/i).first()).toBeVisible();
  await expect(page.getByText(/reliability/i).first()).toBeVisible();
  await expect(page.locator("#evidenceFields")).toContainText("Reliability");
  await expect(page.locator("#timelineList .timeline-item").first()).toBeVisible();
  await expect(page.locator("#evidenceFields .field-card").first()).toBeVisible();
  await expect(page.locator("#evidenceGraph")).toContainText("Evidence Graph");
  await expect(page.locator("#businessGrid")).toContainText(/CONFLICT_DETECTED|HIGHLY_VERIFIED|NEEDS_HUMAN_REVIEW/);
  await expect(page.getByRole("heading", { name: "Ranked intelligence summary" })).toBeVisible();
  await expect(page.locator("#reportExecutive")).toContainText("ARGUS found 8 businesses");
  await expect(page.locator("#reportScaleMetrics")).toContainText("Raw records discovered");
  await expect(page.locator("#reportScaleMetrics")).toContainText("Duplicates removed");
  await expect(page.locator("#reportCoverage")).toContainText("Tamil Nadu supported pairs");
  await expect(page.locator("#reportChallengeMetrics")).toContainText("Offline mode");
  await expect(page.locator("#reportChallengeMetrics")).toContainText("yes");
  await expect(page.locator("#report .panel-heading")).toContainText("Executive Research Report");
  await expect(page.locator("#report")).toContainText("Challenge Requirement Coverage");
  await expect(page.getByText("Multi-source discovery from offline corpus")).toBeVisible();
  await expect(page.locator("#reportCoverage")).toContainText("Challenge: Query understanding");
  await expect(page.locator("#reportCoverage")).toContainText("Demo Command Center");
  await expect(page.locator("#reportCoverage")).toContainText("Recommended Next Actions");
  await expect(page.locator("#reportCoverage")).toContainText("Executive Intelligence");
  await expect(page.locator("#reportCoverage")).toContainText("SWOT Analysis");
  await expect(page.locator("#reportCoverage")).toContainText("Market Narrative");
  await expect(page.locator("#reportCoverage")).toContainText("Executive Scorecard");
  await expect(page.locator("#reportCoverage")).toContainText("Recommendations");
  await expect(page.locator("#reportCoverage")).toContainText("Source reliability scoring");
  await expect(page.locator("#reportCoverage")).toContainText("Source Health");
  await expect(page.locator("#reportChallengeMetrics")).toContainText("Adapter Health");
  await expect(page.locator("#reportChallengeMetrics")).toContainText("Multi-source adapters");
  await expect(page.locator("#reportChallengeMetrics")).toContainText("Job status");
  await expect(page.locator("#reportChallengeMetrics")).toContainText("Current Stage");
  await expect(page.locator("#reportChallengeMetrics")).toContainText("Progress");
  await expect(page.locator("#reportChallengeMetrics")).toContainText("URLs processed");
  await expect(page.locator("#reportChallengeMetrics")).toContainText("Deep enrichment status");
  await expect(page.locator("#reportCoverage")).toContainText("Contradiction Map");
  await expect(page.locator("#reportCoverage")).toContainText("Human Review Queue");
  await expect(page.locator("#reportCoverage")).toContainText("Market Overview");
  await expect(page.locator("#reportCoverage")).toContainText("Business Similarity");
  await expect(page.locator("#reportCoverage")).toContainText("Relationship Graph Summary");
  await expect(page.locator("#reportCoverage")).toContainText("Market Ecosystem");
  await expect(page.locator("#reportCoverage")).toContainText("Most Connected Business");
  await expect(page.locator("#reportCoverage")).toContainText("Most Similar Pair");
  await expect(page.locator("#reportCoverage")).toContainText("Most Unique Business");
  await expect(page.locator("#reportCoverage")).toContainText("Recovery events");
  await expect(page.locator("#reportCoverage")).toContainText("Market Cluster");
  await expect(page.locator("#reportCoverage")).toContainText("Market Position");
  await expect(page.locator("#reportCoverage")).toContainText("Outliers");
  await expect(page.locator("#reportCoverage")).toContainText("Knowledge Graph Summary");
  await expect(page.locator("#reportCoverage")).toContainText("Competitive Intelligence");
  await expect(page.locator("#reportCoverage")).toContainText("Strengths");
  await expect(page.locator("#reportCoverage")).toContainText("Weaknesses");
  await expect(page.locator("#evidenceGraph")).toContainText("Business Similarity");
  await expect(page.locator("#evidenceFields")).toContainText("Reliability");
  await expect(page.getByRole("button", { name: "Download JSON" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Download CSV" })).toBeVisible();

  await page.screenshot({ path: path.join(artifactsDir, "01-dashboard.png"), fullPage: true });
  await page.locator("#report").scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.join(artifactsDir, "02-final-report.png"), fullPage: true });

  await page.locator("#queryInput").fill("Cardiologists in Chennai");
  await page.getByRole("button", { name: /Run/i }).click();
  await page.locator("#report").scrollIntoViewIfNeeded();
  await expect(page.locator("#reportChallengeMetrics")).toContainText("Cache hit");
  await expect(page.locator("#reportChallengeMetrics")).toContainText("yes", { timeout: 80000 });
  await page.screenshot({ path: path.join(artifactsDir, "03-cache-hit.png"), fullPage: true });

  await page.locator("#queryInput").fill("Plumbers in Coimbatore");
  await page.getByRole("button", { name: /Run/i }).click();
  await expect(page.locator("#metricBusinesses")).toHaveText("8", { timeout: 80000 });
  await expect(page.locator("#reportExecutive")).toContainText("Plumbers in Coimbatore", { timeout: 80000 });
  await page.screenshot({ path: path.join(artifactsDir, "04-plumbers-coimbatore.png"), fullPage: true });

  await page.locator("#queryInput").fill("Cardiologists in Birmingham");
  await page.getByRole("button", { name: /Run/i }).click();
  await expect(page.locator("#metricBusinesses")).toHaveText("8", { timeout: 80000 });
  await expect(page.locator("#reportExecutive")).toContainText("Cardiologists in Birmingham", { timeout: 80000 });
  await page.screenshot({ path: path.join(artifactsDir, "05-birmingham-original.png"), fullPage: true });

  await page.locator("#queryInput").fill("Restaurants in Tokyo");
  await page.getByRole("button", { name: /Run/i }).click();
  await expect(page.locator("#metricBusinesses")).toHaveText("0", { timeout: 80000 });
  await expect(page.locator("#businessGrid .business-card")).toHaveCount(0);
  await expect(page.locator("#reportExecutive")).toContainText("No matching offline corpus was found for this query", { timeout: 80000 });
  await expect(page.locator("#businessGrid")).toContainText("Cardiologists in Birmingham");
  await expect(page.locator("#reportCoverage")).toContainText("Offline Corpus Coverage");
  await expect(page.locator("#reportChallengeMetrics")).toContainText("UNSUPPORTED_OFFLINE_QUERY");
  await page.screenshot({ path: path.join(artifactsDir, "06-unsupported-query.png"), fullPage: true });
});
