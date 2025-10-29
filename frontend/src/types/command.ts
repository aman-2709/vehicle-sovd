/**
 * TypeScript types for command-related API requests and responses.
 * These types match the Pydantic schemas in backend/app/schemas/command.py
 */

/**
 * Command name options
 */
export type CommandName = 'ReadDTC' | 'ClearDTC' | 'ReadDataByID';

/**
 * Command parameters for ReadDTC command
 */
export interface ReadDTCParams {
  ecuAddress: string; // Format: ^0x[0-9A-Fa-f]{2}$
}

/**
 * Command parameters for ClearDTC command
 */
export interface ClearDTCParams {
  ecuAddress: string; // Format: ^0x[0-9A-Fa-f]{2}$ (required)
  dtcCode?: string; // Format: ^P[0-9A-F]{4}$ (optional)
}

/**
 * Command parameters for ReadDataByID command
 */
export interface ReadDataByIDParams {
  ecuAddress: string; // Format: ^0x[0-9A-Fa-f]{2}$
  dataId: string; // Format: ^0x[0-9A-Fa-f]{4}$
}

/**
 * Union type for all command parameters
 */
export type CommandParams = ReadDTCParams | ClearDTCParams | ReadDataByIDParams | Record<string, unknown>;

/**
 * Request schema for submitting a new command
 * Matches backend CommandSubmitRequest schema
 */
export interface CommandSubmitRequest {
  command_name: CommandName;
  vehicle_id: string; // UUID serialized as string
  command_params: CommandParams;
}

/**
 * Response schema for command details
 * Matches backend CommandResponse schema
 */
export interface CommandResponse {
  command_id: string; // UUID serialized as string
  user_id: string; // UUID serialized as string
  vehicle_id: string; // UUID serialized as string
  command_name: string;
  command_params: CommandParams;
  status: string;
  error_message: string | null;
  submitted_at: string; // ISO datetime string
  completed_at: string | null; // ISO datetime string
}

/**
 * Form data structure for the command form
 */
export interface CommandFormData {
  vehicle_id: string;
  command_name: CommandName | '';
  ecuAddress?: string;
  dtcCode?: string;
  dataId?: string;
}
