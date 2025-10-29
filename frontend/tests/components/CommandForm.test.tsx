/**
 * CommandForm Component Tests
 *
 * Tests for form rendering, validation, submission, and error handling.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CommandForm } from '../../src/components/commands/CommandForm';

describe('CommandForm', () => {
  const mockOnSubmit = vi.fn();
  const defaultProps = {
    vehicleId: 'test-vehicle-id',
    onSubmit: mockOnSubmit,
    isSubmitting: false,
    submitError: null,
    submitSuccess: null,
  };

  beforeEach(() => {
    mockOnSubmit.mockClear();
  });

  describe('Form Rendering', () => {
    it('should render command form with all base elements', () => {
      render(<CommandForm {...defaultProps} />);

      expect(screen.getByLabelText(/command/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /submit command/i })).toBeInTheDocument();
    });

    it('should have submit button disabled when no command is selected', () => {
      render(<CommandForm {...defaultProps} />);

      const submitButton = screen.getByRole('button', { name: /submit command/i });
      expect(submitButton).toBeDisabled();
    });

    it('should render command dropdown with correct options', () => {
      render(<CommandForm {...defaultProps} />);

      const commandSelect = screen.getByLabelText(/command/i);

      expect(commandSelect).toBeInTheDocument();
      // Options will be available when dropdown is opened, so we just verify the select exists
      expect(commandSelect).toHaveAttribute('aria-haspopup', 'listbox');
    });
  });

  describe('Dynamic Field Rendering', () => {
    it('should show only ecuAddress field when ReadDTC is selected', async () => {
      const user = userEvent.setup();
      render(<CommandForm {...defaultProps} />);

      const commandSelect = screen.getByLabelText(/command/i);
      await user.click(commandSelect);
      await user.click(screen.getByRole('option', { name: /ReadDTC/i }));

      await waitFor(() => {
        expect(screen.getByLabelText(/ECU Address/i)).toBeInTheDocument();
      });

      expect(screen.queryByLabelText(/DTC Code/i)).not.toBeInTheDocument();
      expect(screen.queryByLabelText(/Data ID/i)).not.toBeInTheDocument();
    });

    it('should show ecuAddress and dtcCode fields when ClearDTC is selected', async () => {
      const user = userEvent.setup();
      render(<CommandForm {...defaultProps} />);

      const commandSelect = screen.getByLabelText(/command/i);
      await user.click(commandSelect);
      await user.click(screen.getByRole('option', { name: /ClearDTC/i }));

      await waitFor(() => {
        expect(screen.getByLabelText(/ECU Address/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/DTC Code \(Optional\)/i)).toBeInTheDocument();
      });

      expect(screen.queryByLabelText(/^Data ID$/i)).not.toBeInTheDocument();
    });

    it('should show ecuAddress and dataId fields when ReadDataByID is selected', async () => {
      const user = userEvent.setup();
      render(<CommandForm {...defaultProps} />);

      const commandSelect = screen.getByLabelText(/command/i);
      await user.click(commandSelect);
      await user.click(screen.getByRole('option', { name: /ReadDataByID/i }));

      await waitFor(() => {
        expect(screen.getByLabelText(/ECU Address/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/^Data ID$/i)).toBeInTheDocument();
      });

      expect(screen.queryByLabelText(/DTC Code/i)).not.toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    it('should show error when submitting without command selection', () => {
      render(<CommandForm {...defaultProps} />);

      // Try to enable and click submit (button should be disabled)
      const submitButton = screen.getByRole('button', { name: /submit command/i });
      expect(submitButton).toBeDisabled();
    });

    it('should validate ecuAddress format for ReadDTC', async () => {
      const user = userEvent.setup();
      render(<CommandForm {...defaultProps} />);

      // Select ReadDTC
      const commandSelect = screen.getByLabelText(/command/i);
      await user.click(commandSelect);
      await user.click(screen.getByRole('option', { name: /ReadDTC/i }));

      await waitFor(() => {
        expect(screen.getByLabelText(/ECU Address/i)).toBeInTheDocument();
      });

      // Enter invalid ecuAddress
      const ecuAddressInput = screen.getByLabelText(/ECU Address/i);
      await user.type(ecuAddressInput, 'invalid');

      // Submit form
      const submitButton = screen.getByRole('button', { name: /submit command/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(
          screen.getByText(/ECU Address must be in format 0xXX/i)
        ).toBeInTheDocument();
      });

      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('should validate dtcCode format for ClearDTC', async () => {
      const user = userEvent.setup();
      render(<CommandForm {...defaultProps} />);

      // Select ClearDTC
      const commandSelect = screen.getByLabelText(/command/i);
      await user.click(commandSelect);
      await user.click(screen.getByRole('option', { name: /ClearDTC/i }));

      await waitFor(() => {
        expect(screen.getByLabelText(/ECU Address/i)).toBeInTheDocument();
      });

      // Enter valid ecuAddress but invalid dtcCode
      const ecuAddressInput = screen.getByLabelText(/ECU Address/i);
      await user.type(ecuAddressInput, '0x10');

      const dtcCodeInput = screen.getByLabelText(/DTC Code/i);
      await user.type(dtcCodeInput, 'invalid');

      // Submit form
      const submitButton = screen.getByRole('button', { name: /submit command/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(
          screen.getByText(/DTC Code must be in format PXXXX/i)
        ).toBeInTheDocument();
      });

      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('should validate dataId format for ReadDataByID', async () => {
      const user = userEvent.setup();
      render(<CommandForm {...defaultProps} />);

      // Select ReadDataByID
      const commandSelect = screen.getByLabelText(/command/i);
      await user.click(commandSelect);
      await user.click(screen.getByRole('option', { name: /ReadDataByID/i }));

      await waitFor(() => {
        expect(screen.getByLabelText(/ECU Address/i)).toBeInTheDocument();
      });

      // Enter valid ecuAddress but invalid dataId
      const ecuAddressInput = screen.getByLabelText(/ECU Address/i);
      await user.type(ecuAddressInput, '0x10');

      const dataIdInput = screen.getByLabelText(/^Data ID$/i);
      await user.type(dataIdInput, 'invalid');

      // Submit form
      const submitButton = screen.getByRole('button', { name: /submit command/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(
          screen.getByText(/Data ID must be in format 0xXXXX/i)
        ).toBeInTheDocument();
      });

      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('should allow submission with valid ReadDTC data', async () => {
      const user = userEvent.setup();
      mockOnSubmit.mockResolvedValue(undefined);
      render(<CommandForm {...defaultProps} />);

      // Select ReadDTC
      const commandSelect = screen.getByLabelText(/command/i);
      await user.click(commandSelect);
      await user.click(screen.getByRole('option', { name: /ReadDTC/i }));

      await waitFor(() => {
        expect(screen.getByLabelText(/ECU Address/i)).toBeInTheDocument();
      });

      // Enter valid data
      const ecuAddressInput = screen.getByLabelText(/ECU Address/i);
      await user.type(ecuAddressInput, '0x10');

      // Submit form
      const submitButton = screen.getByRole('button', { name: /submit command/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith({
          vehicle_id: 'test-vehicle-id',
          command_name: 'ReadDTC',
          ecuAddress: '0x10',
          dtcCode: '',
          dataId: '',
        });
      });
    });

    it('should allow submission with valid ClearDTC data including optional dtcCode', async () => {
      const user = userEvent.setup();
      mockOnSubmit.mockResolvedValue(undefined);
      render(<CommandForm {...defaultProps} />);

      // Select ClearDTC
      const commandSelect = screen.getByLabelText(/command/i);
      await user.click(commandSelect);
      await user.click(screen.getByRole('option', { name: /ClearDTC/i }));

      await waitFor(() => {
        expect(screen.getByLabelText(/ECU Address/i)).toBeInTheDocument();
      });

      // Enter valid data
      const ecuAddressInput = screen.getByLabelText(/ECU Address/i);
      await user.type(ecuAddressInput, '0x10');

      const dtcCodeInput = screen.getByLabelText(/DTC Code/i);
      await user.type(dtcCodeInput, 'P0420');

      // Submit form
      const submitButton = screen.getByRole('button', { name: /submit command/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith({
          vehicle_id: 'test-vehicle-id',
          command_name: 'ClearDTC',
          ecuAddress: '0x10',
          dtcCode: 'P0420',
          dataId: '',
        });
      });
    });

    it('should allow submission with valid ReadDataByID data', async () => {
      const user = userEvent.setup();
      mockOnSubmit.mockResolvedValue(undefined);
      render(<CommandForm {...defaultProps} />);

      // Select ReadDataByID
      const commandSelect = screen.getByLabelText(/command/i);
      await user.click(commandSelect);
      await user.click(screen.getByRole('option', { name: /ReadDataByID/i }));

      await waitFor(() => {
        expect(screen.getByLabelText(/ECU Address/i)).toBeInTheDocument();
      });

      // Enter valid data
      const ecuAddressInput = screen.getByLabelText(/ECU Address/i);
      await user.type(ecuAddressInput, '0x10');

      const dataIdInput = screen.getByLabelText(/^Data ID$/i);
      await user.type(dataIdInput, '0x1234');

      // Submit form
      const submitButton = screen.getByRole('button', { name: /submit command/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith({
          vehicle_id: 'test-vehicle-id',
          command_name: 'ReadDataByID',
          ecuAddress: '0x10',
          dtcCode: '',
          dataId: '0x1234',
        });
      });
    });
  });

  describe('Submission States', () => {
    it('should disable form fields when isSubmitting is true', () => {
      render(<CommandForm {...defaultProps} isSubmitting={true} />);

      // Check that the select has aria-disabled attribute (MUI Select uses aria-disabled instead of disabled)
      const commandSelect = screen.getByLabelText(/command/i);
      expect(commandSelect).toHaveAttribute('aria-disabled', 'true');

      const submitButton = screen.getByRole('button', { name: /submitting/i });
      expect(submitButton).toBeDisabled();
    });

    it('should show loading indicator when submitting', () => {
      render(<CommandForm {...defaultProps} isSubmitting={true} />);

      expect(screen.getByRole('button', { name: /submitting/i })).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('should display error message when submitError is provided', () => {
      render(
        <CommandForm {...defaultProps} submitError="An error occurred" />
      );

      expect(screen.getByText(/An error occurred/i)).toBeInTheDocument();
    });

    it('should display success message when submitSuccess is provided', () => {
      render(
        <CommandForm
          {...defaultProps}
          submitSuccess="Command submitted successfully!"
        />
      );

      expect(screen.getByText(/Command submitted successfully!/i)).toBeInTheDocument();
    });
  });

  describe('Form Reset on Vehicle Change', () => {
    it('should reset form when vehicleId changes', async () => {
      const user = userEvent.setup();
      const { rerender } = render(<CommandForm {...defaultProps} />);

      // Select command and fill form
      const commandSelect = screen.getByLabelText(/command/i);
      await user.click(commandSelect);
      await user.click(screen.getByRole('option', { name: /ReadDTC/i }));

      await waitFor(() => {
        expect(screen.getByLabelText(/ECU Address/i)).toBeInTheDocument();
      });

      const ecuAddressInput = screen.getByLabelText(/ECU Address/i);
      await user.type(ecuAddressInput, '0x10');

      // Verify form has values
      expect(ecuAddressInput).toHaveValue('0x10');

      // Change vehicleId
      rerender(<CommandForm {...defaultProps} vehicleId="new-vehicle-id" />);

      // Form should be reset - check that ecuAddress field is no longer visible (because command is reset)
      await waitFor(() => {
        expect(screen.queryByLabelText(/ECU Address/i)).not.toBeInTheDocument();
      });
    });
  });
});
