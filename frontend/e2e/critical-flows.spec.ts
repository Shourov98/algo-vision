import { expect, test } from "@playwright/test";

test("home leads to algorithm explorer", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: /explore algorithms/i }).click();
  await expect(page).toHaveURL(/\/algorithms/);
  await expect(page.getByRole("heading", { name: "Algorithms" })).toBeVisible();
});

test("algorithm explorer filter route renders catalog", async ({ page }) => {
  await page.goto("/algorithms?category=Sorting&difficulty=Easy");
  await expect(page.getByText("Bubble Sort")).toBeVisible();
});

test("problems filtering route renders catalog", async ({ page }) => {
  await page.goto("/problems?topic=Arrays&difficulty=Easy");
  await expect(page.getByRole("heading", { name: "Problems" })).toBeVisible();
  await expect(page.getByText("Two Sum")).toBeVisible();
});

test("sign-in route renders the authentication form", async ({ page }) => {
  await page.goto("/sign-in");
  await expect(page.getByRole("heading", { name: "Welcome back" })).toBeVisible();
  await expect(page.getByLabel("Email")).toBeVisible();
});
