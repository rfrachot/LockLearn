import { expect, test } from "@playwright/test";

test("capture canonical documentation screenshot", async ({ page }) => {
  await page.goto("/e2e/");
  await expect(page.getByRole("heading", { name: "E2E Profile" })).toBeVisible();

  if (process.env.LOCKLEARN_DOCS_CAPTURE !== "1") {
    return;
  }

  await page.screenshot({
    path: "../docs/assets/locklearn-home.png",
    fullPage: true,
  });
});
