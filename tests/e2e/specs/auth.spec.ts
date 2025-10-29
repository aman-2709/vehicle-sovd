import { test, expect } from '@playwright/test';

/**
 * E2E Test Suite: Authentication Flow
 *
 * Tests the complete authentication lifecycle including login, session
 * verification, and logout functionality.
 */
test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the login page before each test
    await page.goto('/login');
  });

  test('complete auth flow: login -> dashboard -> logout', async ({ page }) => {
    // Step 1: Verify we're on the login page
    await expect(page).toHaveURL('/login');
    await expect(page.getByRole('heading', { name: /login/i })).toBeVisible();

    // Step 2: Fill in login credentials (using seed data)
    await page.getByLabel(/username/i).fill('admin');
    await page.getByLabel(/password/i).fill('admin123');

    // Step 3: Submit the login form
    await page.getByRole('button', { name: /login/i }).click();

    // Step 4: Verify redirect to dashboard
    await expect(page).toHaveURL('/dashboard', { timeout: 10000 });

    // Step 5: Verify header shows the username
    // The username should be visible in the header/app bar after login
    await expect(page.getByText('admin')).toBeVisible();

    // Step 6: Verify we can see dashboard content
    await expect(
      page.getByRole('heading', { name: /dashboard/i })
    ).toBeVisible();

    // Step 7: Perform logout
    // Look for logout button in the header/menu
    const logoutButton = page.getByRole('button', { name: /logout/i });
    await logoutButton.click();

    // Step 8: Verify redirect back to login page
    await expect(page).toHaveURL('/login', { timeout: 10000 });

    // Step 9: Verify we can't access protected routes after logout
    await page.goto('/dashboard');
    await expect(page).toHaveURL('/login');
  });

  test('login with invalid credentials shows error', async ({ page }) => {
    // Fill in invalid credentials
    await page.getByLabel(/username/i).fill('invaliduser');
    await page.getByLabel(/password/i).fill('wrongpassword');

    // Submit the login form
    await page.getByRole('button', { name: /login/i }).click();

    // Verify error message is displayed
    await expect(page.getByText(/invalid credentials/i)).toBeVisible();

    // Verify we stay on the login page
    await expect(page).toHaveURL('/login');
  });

  test('login with empty credentials shows validation error', async ({
    page,
  }) => {
    // Try to submit without filling credentials
    await page.getByRole('button', { name: /login/i }).click();

    // Verify we stay on the login page (form validation should prevent submission)
    await expect(page).toHaveURL('/login');
  });

  test('session persistence: refresh page maintains authentication', async ({
    page,
  }) => {
    // Login
    await page.getByLabel(/username/i).fill('engineer');
    await page.getByLabel(/password/i).fill('engineer123');
    await page.getByRole('button', { name: /login/i }).click();

    // Wait for redirect to dashboard
    await expect(page).toHaveURL('/dashboard');

    // Refresh the page
    await page.reload();

    // Verify we're still on dashboard (session persisted)
    await expect(page).toHaveURL('/dashboard');
    await expect(page.getByText('engineer')).toBeVisible();
  });

  test('protected routes redirect to login when not authenticated', async ({
    page,
  }) => {
    // Try to access protected routes directly without authentication
    const protectedRoutes = ['/dashboard', '/vehicles', '/commands'];

    for (const route of protectedRoutes) {
      await page.goto(route);
      // Should be redirected to login
      await expect(page).toHaveURL('/login', { timeout: 5000 });
    }
  });
});
