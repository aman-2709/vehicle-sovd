/**
 * TypeScript type definitions for vehicle-related data structures.
 *
 * These types match the backend Pydantic schemas defined in backend/app/schemas/vehicle.py
 */

/**
 * Vehicle response object returned by vehicle API endpoints.
 *
 * Matches VehicleResponse schema from backend.
 */
export interface VehicleResponse {
  /** UUID string identifier */
  vehicle_id: string;
  /** Vehicle Identification Number (17 characters) */
  vin: string;
  /** Vehicle manufacturer name */
  make: string;
  /** Vehicle model name */
  model: string;
  /** Vehicle manufacturing year */
  year: number;
  /** Current connection status (connected, disconnected, error) */
  connection_status: string;
  /** ISO 8601 timestamp when vehicle was last seen (nullable) */
  last_seen_at: string | null;
  /** Additional vehicle-specific attributes stored in JSONB (nullable) */
  metadata: Record<string, unknown> | null;
}

/**
 * Vehicle status response object returned by status endpoint.
 *
 * Matches VehicleStatusResponse schema from backend.
 */
export interface VehicleStatusResponse {
  /** Current connection status (connected, disconnected, error) */
  connection_status: string;
  /** ISO 8601 timestamp when vehicle was last seen (nullable) */
  last_seen_at: string | null;
  /** Health metrics like signal strength, battery voltage (nullable) */
  health: Record<string, unknown> | null;
}

/**
 * Query parameters for fetching vehicle list.
 */
export interface VehicleListParams {
  /** Filter by connection status (connected, disconnected, error) */
  status?: string;
  /** Search by VIN (partial match, case-insensitive) */
  search?: string;
  /** Maximum number of results (1-100, default: 50) */
  limit?: number;
  /** Number of results to skip (default: 0) */
  offset?: number;
}
