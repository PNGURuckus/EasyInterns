import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('should display sign in page', async ({ page }) => {
    await page.goto('/auth/signin');
    
    await expect(page.locator('h1')).toContainText('Sign in to EasyInterns');
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('should display sign up page', async ({ page }) => {
    await page.goto('/auth/signup');
    
    await expect(page.locator('h1')).toContainText('Join EasyInterns');
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('should validate email input', async ({ page }) => {
    await page.goto('/auth/signin');
    
    // Try to submit without email
    await page.click('button[type="submit"]');
    
    // Should show validation error
    await expect(page.locator('input[type="email"]:invalid')).toBeVisible();
  });

  test('should navigate between sign in and sign up', async ({ page }) => {
    await page.goto('/auth/signin');
    
    // Click "Create an account" link
    await page.click('text=Create an account');
    await expect(page).toHaveURL('/auth/signup');
    
    // Click "Sign in instead" link
    await page.click('text=Sign in instead');
    await expect(page).toHaveURL('/auth/signin');
  });

  test('should redirect to home from auth pages when authenticated', async ({ page }) => {
    // Mock authenticated state
    await page.addInitScript(() => {
      localStorage.setItem('supabase.auth.token', JSON.stringify({
        access_token: 'mock-token',
        user: { id: 'test-user', email: 'test@example.com' }
      }));
    });

    await page.goto('/auth/signin');
    
    // Should redirect to browse page
    await expect(page).toHaveURL('/browse');
  });
});
