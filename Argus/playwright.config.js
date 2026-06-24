module.exports = {
  testDir: "./tests/e2e",
  timeout: 60000,
  use: {
    headless: true,
    viewport: { width: 1440, height: 1100 },
  },
  projects: [
    {
      name: "chromium",
      use: { browserName: "chromium" },
    },
  ],
};
