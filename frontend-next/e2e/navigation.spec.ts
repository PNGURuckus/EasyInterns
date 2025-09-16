import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
  test('should navigate through main pages', async ({ page }) => {
    await page.goto('/');
    
    // Test home page
    await expect(page.locator('h1')).toContainText('Find Your Perfect Internship');
    
    // Navigate to browse page
    await page.click('text=Browse Internships');
    await expect(page).toHaveURL('/browse');
    await expect(page.locator('h1')).toContainText('Find Your Perfect Internship');
    
    // Test header navigation
    await page.click('text=Home');
    await expect(page).toHaveURL('/');
  });

  test('should display responsive header', async ({ page }) => {
    await page.goto('/');
    
    // Desktop navigation should be visible
    await expect(page.locator('nav')).toBeVisible();
    await expect(page.locator('text=Browse')).toBeVisible();
    await expect(page.locator('text=Resume')).toBeVisible();
  });

  test('should handle mobile navigation', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    
    // Mobile menu button should be visible
    await expect(page.locator('[aria-label="Toggle menu"]')).toBeVisible();
  });

  test('should display footer', async ({ page }) => {
    await page.goto('/');
    
    await expect(page.locator('footer')).toBeVisible();
    await expect(page.locator('text=© 2024 EasyInterns')).toBeVisible();
  });

  test('should protect authenticated routes', async ({ page }) => {
    // Try to access protected route without auth
    await page.goto('/saved');
    
    // Should redirect to sign in
    await expect(page).toHaveURL(/\/auth\/signin/);
  });
});
