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


test("Learn and Quiz explain readiness before a session starts", async ({ page }) => {
  await page.getByRole("button", { name: "Learn", exact: true }).click();
  await expect(page.getByText("Learning availability", { exact: true })).toBeVisible();
  await expect(
    page.getByText("No card is due within the normal learning plan right now.", { exact: true }),
  ).toBeVisible();
  await expect(page.getByText("Cards already started", { exact: true })).toBeVisible();
  await expect(page.getByText("Cards left to discover in this Track", { exact: true })).toBeVisible();
  await expect(page.getByText("New cards still allowed today", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Continue now" })).toBeVisible();

  await page.getByRole("button", { name: "Quiz", exact: true }).click();
  await expect(page.getByText("Quiz readiness", { exact: true })).toBeVisible();
  await expect(page.getByText(/1 cards ready for quiz/)).toBeVisible();
});

test("Undo of an already-known introduction uses the canonical reversal", async ({ page }) => {
  await page.getByRole("button", { name: "Learn", exact: true }).click();
  await page.getByRole("button", { name: "Start learning" }).click();
  await page.evaluate(() => {
    const hass = (window as unknown as {
      __LOCKLEARN_E2E_HASS__: {
        callWS: (message: Record<string, unknown>) => Promise<unknown>;
      };
    }).__LOCKLEARN_E2E_HASS__;
    const original = hass.callWS.bind(hass);
    const calls: string[] = [];
    hass.callWS = async (message) => {
      calls.push(String(message.type));
      return original(message);
    };
    Object.assign(window, { __LOCKLEARN_E2E_CALLS__: calls });
  });

  await page.getByRole("button", { name: "I already know this card" }).click();
  await page.getByRole("button", { name: "Undo" }).click();
  await expect(page.getByText("The already-known mark was undone.")).toBeVisible();
  const calls = await page.evaluate(() =>
    (window as unknown as { __LOCKLEARN_E2E_CALLS__: string[] }).__LOCKLEARN_E2E_CALLS__,
  );
  expect(calls).toContain("locklearn/cards/learn_instead");
  expect(calls).not.toContain("locklearn/progress/undo_last");
});

test("Save and leave keeps the selected Profile when refresh returns late", async ({ page }) => {
  await page.getByRole("button", { name: "Tracks", exact: true }).click();
  await page.evaluate(() => {
    const hass = (window as unknown as {
      __LOCKLEARN_E2E_HASS__: {
        callWS: (message: Record<string, unknown>) => Promise<unknown>;
      };
    }).__LOCKLEARN_E2E_HASS__;
    const original = hass.callWS.bind(hass);
    let saved = false;
    hass.callWS = async (message) => {
      if (message.type === "locklearn/tracks/update") saved = true;
      if (saved && message.type === "locklearn/profiles/list") {
        await new Promise((resolve) => setTimeout(resolve, 250));
      }
      return original(message);
    };
  });
  const name = page.locator("locklearn-management-view form.track-form").first().locator('input[name="name"]');
  await name.fill("Japanese Core edited");
  await page.getByRole("combobox").first().selectOption("profile-other");
  await page.getByRole("dialog", { name: "Unsaved changes" })
    .getByRole("button", { name: "Save and leave" }).click();
  await expect(page.getByRole("combobox").first()).toHaveValue("profile-other");
  await page.waitForTimeout(350);
  await expect(page.getByRole("combobox").first()).toHaveValue("profile-other");
});

test("Discard restores saved Track details and plan values", async ({ page }) => {
  await page.getByRole("button", { name: "Tracks", exact: true }).click();
  const details = page.locator('locklearn-management-view form[data-save-scope="track-ja:details"]');
  const name = details.locator('input[name="name"]');
  await name.fill("Unsaved name");
  await details.getByRole("button", { name: "Discard changes" }).click();
  await expect(name).toHaveValue("Japanese Core");
  await expect(details.getByText("No unsaved changes")).toBeVisible();

  await page.locator("summary").filter({ hasText: "Learning pace & goal" }).first().click();
  const plan = page.locator('locklearn-management-view form[data-save-scope="track-ja:plan"]');
  const newPerDay = plan.locator('input[name="new"]');
  const savedValue = await newPerDay.inputValue();
  await newPerDay.fill("5");
  await plan.getByRole("button", { name: "Discard changes" }).click();
  await expect(newPerDay).toHaveValue(savedValue);
  await expect(plan.getByText("No unsaved changes")).toBeVisible();
});

test("multi-Track cards keep advanced settings and plans attached to each Track", async ({ page }) => {
  await page.getByRole("button", { name: "Tracks", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Japanese Core" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "French Core" })).toBeVisible();

  const advanced = page.locator("summary").filter({ hasText: "Advanced Track settings" });
  const plans = page.locator("summary").filter({ hasText: "Learning pace & goal" });
  await expect(advanced).toHaveCount(2);
  await expect(plans).toHaveCount(2);

  const japaneseCard = page
    .getByRole("heading", { name: "Japanese Core" })
    .locator("xpath=ancestor::article[1]");
  const cardBox = await japaneseCard.boundingBox();
  const sectionBox = await japaneseCard.locator("details").first().boundingBox();
  expect(cardBox).not.toBeNull();
  expect(sectionBox).not.toBeNull();
  expect((sectionBox?.width ?? 0) / (cardBox?.width ?? 1)).toBeGreaterThan(0.8);

  await advanced.first().click();
  await plans.nth(1).click();
  await expect(japaneseCard.getByText("Priority", { exact: true })).toBeVisible();
  const frenchCard = page
    .getByRole("heading", { name: "French Core" })
    .locator("xpath=ancestor::article[1]");
  await expect(frenchCard.getByRole("spinbutton", { name: /New cards \/ day/ })).toBeVisible();
});

test("Companion targets render as separate readable cards", async ({ page }) => {
  await page.getByRole("button", { name: "Settings", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Pixel 9 Pro" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Galaxy Tab" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Test notification" })).toHaveCount(2);
  await expect(page.locator("summary").filter({ hasText: "Advanced target settings" })).toHaveCount(2);
});

test("management cards do not overflow a mobile viewport", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("button", { name: "Tracks", exact: true }).click();
  await page.locator("summary").filter({ hasText: "Advanced Track settings" }).first().click();

  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
  expect(overflow).toBeLessThanOrEqual(1);
});
