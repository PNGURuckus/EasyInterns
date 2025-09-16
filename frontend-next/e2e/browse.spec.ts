import { test, expect } from '@playwright/test';

test.describe('Browse Internships', () => {
  test('should display browse page with search functionality', async ({ page }) => {
    await page.goto('/browse');
    
    await expect(page.locator('h1')).toContainText('Find Your Perfect Internship');
    await expect(page.locator('input[placeholder*="Search internships"]')).toBeVisible();
    await expect(page.locator('text=Filters')).toBeVisible();
  });

  test('should perform search', async ({ page }) => {
    await page.goto('/browse');
    
    // Enter search query
    await page.fill('input[placeholder*="Search internships"]', 'software engineer');
    
    // Should update URL with query parameter
    await expect(page).toHaveURL(/.*query=software%20engineer/);
  });

  test('should toggle filters panel', async ({ page }) => {
    await page.goto('/browse');
    
    // Click filters button
    await page.click('text=Filters');
    
    // Filters panel should appear
    await expect(page.locator('text=Filter Internships')).toBeVisible();
    await expect(page.locator('select')).toHaveCount(3); // Field, Work Mode, Location
  });

  test('should apply filters', async ({ page }) => {
    await page.goto('/browse');
    
    // Open filters
    await page.click('text=Filters');
    
    // Select field filter
    await page.selectOption('select >> nth=0', 'software_engineering');
    
    // Select work mode filter
    await page.selectOption('select >> nth=1', 'remote');
    
    // Enter location
    await page.fill('input[placeholder*="City, Province"]', 'Toronto');
    
    // URL should update with filters
    await expect(page).toHaveURL(/.*field_tags=software_engineering/);
    await expect(page).toHaveURL(/.*modality=remote/);
    await expect(page).toHaveURL(/.*locations=Toronto/);
  });

  test('should clear filters', async ({ page }) => {
    await page.goto('/browse?field_tags=software_engineering&modality=remote');
    
    // Open filters
    await page.click('text=Filters');
    
    // Click clear all
    await page.click('text=Clear All');
    
    // URL should be clean
    await expect(page).toHaveURL('/browse');
  });

  test('should display loading state', async ({ page }) => {
    // Mock slow API response
    await page.route('/api/internships*', async route => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            total: 0,
            internships: [],
            facets: { field_tags: [], modality: [], locations: [] }
          }
        })
      });
    });

    await page.goto('/browse');
    
    // Should show loading spinner
    await expect(page.locator('.animate-spin')).toBeVisible();
    await expect(page.locator('text=Loading internships')).toBeVisible();
  });

  test('should display empty state', async ({ page }) => {
    // Mock empty API response
    await page.route('/api/internships*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            total: 0,
            internships: [],
            facets: { field_tags: [], modality: [], locations: [] }
          }
        })
      });
    });

    await page.goto('/browse');
    
    // Should show "0 internships found"
    await expect(page.locator('text=0 internships found')).toBeVisible();
  });

  test('should display internship cards', async ({ page }) => {
    // Mock API response with sample data
    await page.route('/api/internships*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            total: 1,
            internships: [{
              id: 'test-internship-1',
              title: 'Software Engineering Intern',
              company: { name: 'Tech Corp', domain: 'techcorp.com' },
              location: 'Toronto, ON',
              description: 'Join our development team...',
              modality: 'hybrid',
              field_tag: 'software_engineering',
              salary_min: 50000,
              salary_max: 60000,
              posting_date: '2024-01-15',
              apply_url: 'https://example.com/apply'
            }],
            facets: {
              field_tags: [{ value: 'software_engineering', count: 1 }],
              modality: [{ value: 'hybrid', count: 1 }],
              locations: [{ value: 'Toronto, ON', count: 1 }]
            }
          }
        })
      });
    });

    await page.goto('/browse');
    
    // Should display internship card
    await expect(page.locator('text=Software Engineering Intern')).toBeVisible();
    await expect(page.locator('text=Tech Corp')).toBeVisible();
    await expect(page.locator('text=Toronto, ON')).toBeVisible();
    await expect(page.locator('text=$50,000 - $60,000')).toBeVisible();
  });

  test('should handle pagination', async ({ page }) => {
    // Mock API response with pagination
    await page.route('/api/internships*', async route => {
      const url = new URL(route.request().url());
      const page_num = url.searchParams.get('page') || '1';
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            total: 50, // More than 20 to trigger pagination
            internships: Array.from({ length: 20 }, (_, i) => ({
              id: `internship-${page_num}-${i}`,
              title: `Internship ${page_num}-${i}`,
              company: { name: 'Company', domain: 'company.com' },
              location: 'Toronto, ON',
              modality: 'remote',
              field_tag: 'software_engineering',
              apply_url: 'https://example.com/apply'
            })),
            facets: { field_tags: [], modality: [], locations: [] }
          }
        })
      });
    });

    await page.goto('/browse');
    
    // Should show pagination
    await expect(page.locator('text=Page 1 of 3')).toBeVisible();
    await expect(page.locator('text=Next')).toBeVisible();
    
    // Click next page
    await page.click('text=Next');
    await expect(page.locator('text=Page 2 of 3')).toBeVisible();
  });
});
