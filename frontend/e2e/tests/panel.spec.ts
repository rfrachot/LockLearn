import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.goto("/e2e/");
  await expect(page.getByRole("heading", { name: "E2E Profile" })).toBeVisible();
});

test("core shell routes through Home, Learn, Quiz, Stats and Profiles", async ({ page }) => {
  await expect(page.getByText("Japanese Core", { exact: true })).toBeVisible();

  await page.getByRole("button", { name: "Learn", exact: true }).click();
  await expect(page.getByRole("button", { name: "Start learning" })).toBeVisible();
  await page.getByRole("button", { name: "Start learning" }).click();
  await expect(page.locator('[lang="ja"] ruby').first()).toBeVisible();
  await expect(page.locator('[lang="ja"] rt').first()).toContainText("に");

  await page.getByRole("button", { name: "Quiz", exact: true }).click();
  await expect(page.getByRole("button", { name: "Start quiz" })).toBeVisible();
  await page.getByRole("button", { name: "Start quiz" }).click();
  await expect(page.getByText("日本", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: /1\. Japan/ }).click();
  await expect(page.getByText("Correct", { exact: true })).toBeVisible();

  await page.getByRole("button", { name: "Stats", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Stats & difficulties" })).toBeVisible();
  await expect(page.getByText("80%")).toBeVisible();

  await page.getByRole("button", { name: "Profiles", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Profiles" })).toBeVisible();
});

test("keyboard navigation exposes visible focus without polling", async ({ page }) => {
  await page.keyboard.press("Tab");
  const focused = page.getByRole("combobox").first();
  await expect(focused).toBeFocused();

  const outlineStyle = await focused.evaluate((element) => {
    const style = getComputedStyle(element);
    return { style: style.outlineStyle, width: style.outlineWidth };
  });
  expect(outlineStyle.style).not.toBe("none");
  expect(outlineStyle.width).not.toBe("0px");

  await page.waitForTimeout(250);
  await expect(page.getByRole("heading", { name: "E2E Profile" })).toBeVisible();
});
