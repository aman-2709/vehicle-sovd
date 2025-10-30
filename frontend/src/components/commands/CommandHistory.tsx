/**
 * CommandHistory Component
 *
 * Displays a table of command history with columns: Command Name, Vehicle (VIN),
 * Status, Submitted At, User, and Actions.
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  CircularProgress,
  Alert,
  Typography,
  Button,
  Box,
} from '@mui/material';
import VisibilityIcon from '@mui/icons-material/Visibility';
import type { CommandResponse } from '../../types/command';
import { formatRelativeTime } from '../../utils/dateUtils';

interface VehicleInfo {
  vin: string;
  make: string;
  model: string;
}

export interface CommandHistoryProps {
  commands: CommandResponse[];
  isLoading: boolean;
  error: Error | null;
  showUserColumn?: boolean; // Show user column (admin only)
  vehicleMap?: Map<string, VehicleInfo>;
  userMap?: Map<string, string>; // Map of user_id to username
}

/**
 * Get color for command status chip
 */
const getStatusColor = (
  status: string
): 'default' | 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success' => {
  switch (status.toLowerCase()) {
    case 'completed':
      return 'success';
    case 'failed':
      return 'error';
    case 'in_progress':
      return 'primary';
    case 'pending':
      return 'warning';
    default:
      return 'default';
  }
};

const CommandHistory: React.FC<CommandHistoryProps> = ({
  commands,
  isLoading,
  error,
  showUserColumn = false,
  vehicleMap = new Map<string, VehicleInfo>(),
  userMap = new Map<string, string>(),
}) => {
  const navigate = useNavigate();

  const handleViewDetails = (commandId: string) => {
    navigate(`/commands/${commandId}`);
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        Error loading command history: {error.message}
      </Alert>
    );
  }

  if (commands.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <Typography variant="body1" color="text.secondary">
          No commands found
        </Typography>
      </Box>
    );
  }

  return (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Command Name</TableCell>
            <TableCell>Vehicle (VIN)</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Submitted At</TableCell>
            {showUserColumn && <TableCell>User</TableCell>}
            <TableCell align="right">Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {commands.map((command) => {
            const vehicle: VehicleInfo | undefined = vehicleMap.get(command.vehicle_id);
            const username: string | undefined = userMap.get(command.user_id);

            return (
              <TableRow key={command.command_id} hover>
                <TableCell>
                  <Typography variant="body2" fontWeight="medium">
                    {command.command_name}
                  </Typography>
                </TableCell>
                <TableCell>
                  {vehicle ? (
                    <Box>
                      <Typography variant="body2">{vehicle.vin}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {vehicle.make} {vehicle.model}
                      </Typography>
                    </Box>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      {command.vehicle_id.substring(0, 8)}...
                    </Typography>
                  )}
                </TableCell>
                <TableCell>
                  <Chip label={command.status} color={getStatusColor(command.status)} size="small" />
                </TableCell>
                <TableCell>
                  <Typography variant="body2">{formatRelativeTime(command.submitted_at)}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {new Date(command.submitted_at).toLocaleString()}
                  </Typography>
                </TableCell>
                {showUserColumn && (
                  <TableCell>
                    <Typography variant="body2">
                      {username || command.user_id.substring(0, 8) + '...'}
                    </Typography>
                  </TableCell>
                )}
                <TableCell align="right">
                  <Button
                    size="small"
                    variant="outlined"
                    startIcon={<VisibilityIcon />}
                    onClick={() => handleViewDetails(command.command_id)}
                  >
                    View Details
                  </Button>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default CommandHistory;
