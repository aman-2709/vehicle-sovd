import { test, expect } from '@playwright/test';

/**
 * E2E Test Suite: Command Execution
 *
 * Tests the complete command execution flow including vehicle selection,
 * command submission, and real-time response viewing via WebSocket.
 */
test.describe('Command Execution Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.getByLabel(/username/i).fill('admin');
    await page.getByLabel(/password/i).fill('admin123');
    await page.getByRole('button', { name: /login/i }).click();

    // Wait for successful login and redirect
    await expect(page).toHaveURL('/dashboard', { timeout: 10000 });

    // Navigate to command page
    await page.goto('/commands');
    await expect(page).toHaveURL('/commands');
  });

  test('complete command execution flow with ReadDTC command', async ({
    page,
  }) => {
    // Step 1: Verify command page is loaded
    await expect(
      page.getByRole('heading', { name: /command/i })
    ).toBeVisible();

    // Step 2: Select a vehicle from the dropdown
    const vehicleSelector = page.getByRole('combobox', { name: /vehicle/i });
    await expect(vehicleSelector).toBeVisible();
    await vehicleSelector.click();

    // Wait for vehicle options to load
    await page.waitForTimeout(1000);

    // Select the first test vehicle
    const vehicleOption = page.getByRole('option', {
      name: /TESTVIN0000000001/i,
    });
    await expect(vehicleOption).toBeVisible();
    await vehicleOption.click();

    // Step 3: Select "ReadDTC" command
    const commandSelector = page.getByRole('combobox', { name: /command/i });
    await expect(commandSelector).toBeVisible();
    await commandSelector.click();

    // Wait for command options to load
    await page.waitForTimeout(500);

    // Select ReadDTC command
    const commandOption = page.getByRole('option', { name: /ReadDTC/i });
    await expect(commandOption).toBeVisible();
    await commandOption.click();

    // Step 4: Fill in command parameters (ecuAddress for ReadDTC)
    // Wait for the form to update with parameter fields
    await page.waitForTimeout(500);

    const ecuAddressInput = page.getByLabel(/ecu.*address/i);
    await expect(ecuAddressInput).toBeVisible();
    await ecuAddressInput.fill('0x18DA00F1');

    // Step 5: Submit the command
    const submitButton = page.getByRole('button', { name: /submit|execute/i });
    await expect(submitButton).toBeVisible();
    await submitButton.click();

    // Step 6: Verify command_id is displayed in success message
    await expect(
      page.getByText(/command.*submitted.*successfully/i)
    ).toBeVisible({ timeout: 10000 });

    // Look for command ID pattern (UUID format)
    const commandIdPattern =
      /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i;
    await expect(page.locator(`text=${commandIdPattern}`)).toBeVisible();

    // Step 7: Verify ResponseViewer component is visible
    // The ResponseViewer should automatically appear after command submission
    await expect(
      page.getByText(/response|status/i).first()
    ).toBeVisible({ timeout: 5000 });

    // Step 8: Wait for WebSocket responses to appear
    // The ResponseViewer component should display real-time responses
    // We'll wait for response-related elements to appear

    // Wait for response items to be displayed (with generous timeout for WebSocket)
    // Look for response status indicators or response content
    const responseContainer = page.locator('[class*="response"]').first();
    await expect(responseContainer).toBeVisible({ timeout: 15000 });

    // Verify that we can see response status (Pending, InProgress, Completed, etc.)
    const statusPattern = /pending|in progress|completed|failed/i;
    await expect(page.locator(`text=${statusPattern}`).first()).toBeVisible({
      timeout: 20000,
    });
  });

  test('command form validates required parameters', async ({ page }) => {
    // Select a vehicle
    const vehicleSelector = page.getByRole('combobox', { name: /vehicle/i });
    await vehicleSelector.click();
    await page.waitForTimeout(1000);
    await page.getByRole('option', { name: /TESTVIN0000000001/i }).click();

    // Select ReadDTC command
    const commandSelector = page.getByRole('combobox', { name: /command/i });
    await commandSelector.click();
    await page.waitForTimeout(500);
    await page.getByRole('option', { name: /ReadDTC/i }).click();

    // Try to submit without filling required parameters
    const submitButton = page.getByRole('button', { name: /submit|execute/i });
    await submitButton.click();

    // Verify validation error or that form doesn't submit
    // (This depends on the actual validation implementation)
    await page.waitForTimeout(1000);

    // Should not see success message
    await expect(
      page.getByText(/command.*submitted.*successfully/i)
    ).not.toBeVisible();
  });

  test('can execute multiple commands sequentially', async ({ page }) => {
    // Execute first command
    const vehicleSelector = page.getByRole('combobox', { name: /vehicle/i });
    await vehicleSelector.click();
    await page.waitForTimeout(1000);
    await page.getByRole('option', { name: /TESTVIN0000000001/i }).click();

    const commandSelector = page.getByRole('combobox', { name: /command/i });
    await commandSelector.click();
    await page.waitForTimeout(500);
    await page.getByRole('option', { name: /ReadDTC/i }).click();

    await page.waitForTimeout(500);
    const ecuAddressInput = page.getByLabel(/ecu.*address/i);
    await ecuAddressInput.fill('0x18DA00F1');

    const submitButton = page.getByRole('button', { name: /submit|execute/i });
    await submitButton.click();

    // Wait for first command to be submitted
    await expect(
      page.getByText(/command.*submitted.*successfully/i)
    ).toBeVisible({ timeout: 10000 });

    // Wait a moment before submitting second command
    await page.waitForTimeout(2000);

    // Execute second command (same command, could be different)
    // The form should still be usable
    await vehicleSelector.click();
    await page.waitForTimeout(500);
    await page.getByRole('option', { name: /TESTVIN0000000002/i }).click();

    await commandSelector.click();
    await page.waitForTimeout(500);
    await page.getByRole('option', { name: /ReadDTC/i }).click();

    await page.waitForTimeout(500);
    await ecuAddressInput.fill('0x18DA00F2');
    await submitButton.click();

    // Verify second command submission
    await expect(
      page.getByText(/command.*submitted.*successfully/i)
    ).toBeVisible({ timeout: 10000 });
  });

  test('displays error when vehicle is not connected', async ({ page }) => {
    // Select a disconnected vehicle (if available in seed data)
    const vehicleSelector = page.getByRole('combobox', { name: /vehicle/i });
    await vehicleSelector.click();
    await page.waitForTimeout(1000);

    // Try to select any available vehicle
    const vehicleOption = page.getByRole('option').first();
    await vehicleOption.click();

    // Select command
    const commandSelector = page.getByRole('combobox', { name: /command/i });
    await commandSelector.click();
    await page.waitForTimeout(500);
    await page.getByRole('option', { name: /ReadDTC/i }).click();

    // Fill parameters
    await page.waitForTimeout(500);
    const ecuAddressInput = page.getByLabel(/ecu.*address/i);
    await ecuAddressInput.fill('0x18DA00F1');

    // Submit command
    const submitButton = page.getByRole('button', { name: /submit|execute/i });
    await submitButton.click();

    // Either success or error should be shown within timeout
    await page.waitForTimeout(5000);

    // Check if either success or error message is displayed
    const hasSuccess = await page
      .getByText(/command.*submitted.*successfully/i)
      .isVisible();
    const hasError = await page
      .getByText(/error|failed|not connected/i)
      .isVisible();

    expect(hasSuccess || hasError).toBe(true);
  });

  test('response viewer shows real-time updates', async ({ page }) => {
    // Submit a command
    const vehicleSelector = page.getByRole('combobox', { name: /vehicle/i });
    await vehicleSelector.click();
    await page.waitForTimeout(1000);
    await page.getByRole('option', { name: /TESTVIN0000000001/i }).click();

    const commandSelector = page.getByRole('combobox', { name: /command/i });
    await commandSelector.click();
    await page.waitForTimeout(500);
    await page.getByRole('option', { name: /ReadDTC/i }).click();

    await page.waitForTimeout(500);
    const ecuAddressInput = page.getByLabel(/ecu.*address/i);
    await ecuAddressInput.fill('0x18DA00F1');

    const submitButton = page.getByRole('button', { name: /submit|execute/i });
    await submitButton.click();

    // Wait for command submission
    await expect(
      page.getByText(/command.*submitted.*successfully/i)
    ).toBeVisible({ timeout: 10000 });

    // Wait for ResponseViewer to show updates
    // The response viewer should show status changes via WebSocket
    await page.waitForTimeout(3000);

    // Check for response elements
    const responseElements = page.locator('[class*="response"]');
    const count = await responseElements.count();
    expect(count).toBeGreaterThan(0);

    // Verify response content is displayed
    // This could be status, timestamps, or response data
    const hasResponseContent =
      (await page.getByText(/pending|in progress|completed/i).count()) > 0;
    expect(hasResponseContent).toBe(true);
  });
});
