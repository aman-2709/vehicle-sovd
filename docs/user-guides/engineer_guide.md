# Engineer User Guide

Welcome to the SOVD Web Application! This guide will walk you through the user interface and show you how to interact with vehicles using SOVD commands.

## Table of Contents

- [Getting Started](#getting-started)
- [Logging In](#logging-in)
- [Dashboard Overview](#dashboard-overview)
- [Managing Vehicles](#managing-vehicles)
- [Executing Commands](#executing-commands)
- [Viewing Command History](#viewing-command-history)
- [Real-Time Command Updates](#real-time-command-updates)
- [User Profile and Settings](#user-profile-and-settings)
- [Troubleshooting](#troubleshooting)
- [Common Use Cases](#common-use-cases)

---

## Getting Started

### What is the SOVD Web Application?

The SOVD (Service-Oriented Vehicle Diagnostics) Web Application allows engineers to remotely interact with vehicles using standardized SOVD commands. You can:

- View and manage a fleet of vehicles
- Execute diagnostic commands (ReadDTC, ClearDTC, etc.)
- Receive real-time responses from vehicles
- Track command execution history
- Monitor vehicle connectivity status

### Prerequisites

Before you begin, ensure you have:
- Access credentials (username and password provided by your administrator)
- A modern web browser (Chrome, Firefox, Safari, or Edge)
- Network access to the SOVD application (local or production URL)

---

## Logging In

### Step 1: Navigate to the Application

Open your web browser and go to:
- **Local Development**: http://localhost:5173
- **Production**: https://sovd.yourdomain.com (replace with actual domain)

### Step 2: Enter Your Credentials

You'll see a login screen with two fields:

1. **Username**: Enter your username (e.g., `admin` or `engineer`)
2. **Password**: Enter your password

**Default Credentials (Development)**:
- **Admin User**:
  - Username: `admin`
  - Password: `admin123`
  - Role: Administrator (full access)

- **Engineer User**:
  - Username: `engineer`
  - Password: `engineer123`
  - Role: Engineer (standard access)

### Step 3: Click "Log In"

After entering your credentials, click the **Log In** button.

**What Happens Next**:
- Your credentials are validated
- A JWT (JSON Web Token) is generated and stored securely
- You're redirected to the dashboard

**Troubleshooting**:
- **"Invalid credentials"**: Check username and password, ensure Caps Lock is off
- **401 Unauthorized**: Contact your administrator to verify your account exists
- **Connection error**: Check network connectivity, ensure backend is running

**Security Note**: Your session expires after 30 minutes of inactivity. You'll need to log in again.

---

## Dashboard Overview

After logging in, you'll see the main dashboard with the following elements:

### Navigation Bar (Top)

- **SOVD Logo**: Click to return to dashboard
- **Vehicles**: Navigate to vehicle list
- **Commands**: Navigate to command execution page
- **History**: View command history
- **User Menu** (right): Shows your username and role
  - Profile settings
  - Log out

### Main Content Area

The dashboard provides:
- **Quick Stats**: Total vehicles, active connections, commands today
- **Recent Activity**: Latest command executions
- **System Status**: Backend health, database connectivity

### Status Indicators

- **Green Dot**: Service is healthy and connected
- **Yellow Dot**: Service is degraded or slow
- **Red Dot**: Service is down or disconnected

---

## Managing Vehicles

### Viewing the Vehicle List

**Step 1**: Click **Vehicles** in the navigation bar.

You'll see a table with all registered vehicles:

| Column | Description |
|--------|-------------|
| **VIN** | Vehicle Identification Number |
| **IP Address** | Network address of the vehicle |
| **Status** | Connection status (Connected/Disconnected) |
| **Last Seen** | Timestamp of last communication |
| **Actions** | View details, execute command |

**Example Vehicle (Seed Data)**:
- VIN: `WDD1234567890ABCD`
- IP: `192.168.1.10`
- Status: Connected
- Last Seen: 2025-10-30 14:32:01

### Viewing Vehicle Details

**Step 2**: Click the **View** button next to a vehicle.

The vehicle detail page shows:
- **Vehicle Information**: VIN, IP address, connection status
- **Recent Commands**: Last 10 commands executed on this vehicle
- **Statistics**: Total commands, success rate, average response time
- **Connection History**: Timeline of connection/disconnection events

### Filtering and Searching

Use the search bar to find vehicles:
- Search by VIN: `WDD1234`
- Search by IP: `192.168`
- Filter by status: Click "Connected" or "Disconnected" tabs

---

## Executing Commands

### Step 1: Navigate to the Commands Page

Click **Commands** in the navigation bar.

### Step 2: Select a Vehicle

In the **Vehicle Selection** dropdown:
1. Click the dropdown menu
2. Browse the list of vehicles (shows VIN and status)
3. Select the vehicle you want to command

**Note**: You can only select vehicles that are currently connected (green status indicator).

### Step 3: Choose a Command Type

Select a command from the **Command Type** dropdown:

| Command | Description | Use Case |
|---------|-------------|----------|
| **ReadDTC** | Read Diagnostic Trouble Codes | Retrieve error codes from vehicle |
| **ClearDTC** | Clear Diagnostic Trouble Codes | Reset error codes after repair |
| **ReadDataByIdentifier** | Read specific data points | Get vehicle speed, RPM, temperature, etc. |
| **WriteDataByIdentifier** | Write configuration data | Update vehicle settings |
| **RoutineControl** | Execute diagnostic routines | Run self-tests, calibrations |
| **RequestDownload** | Initiate software download | Prepare for firmware update |
| **TransferData** | Transfer data blocks | Upload firmware or configuration |
| **RequestTransferExit** | Complete data transfer | Finalize firmware update |

### Step 4: Enter Command Parameters (Optional)

Some commands require additional parameters in JSON format.

**Example for ReadDataByIdentifier**:
```json
{
  "identifier": "0x0100"
}
```

**Example for RoutineControl**:
```json
{
  "routine_id": "0x0202",
  "control_type": "start"
}
```

**Tip**: Leave parameters empty for commands that don't require them (e.g., ReadDTC, ClearDTC).

### Step 5: Submit the Command

Click the **Execute Command** button.

**What Happens Next**:
1. The command is validated and sent to the backend
2. The backend forwards the command to the vehicle connector
3. The vehicle connector sends the SOVD command to the vehicle
4. You'll see a "Command submitted successfully" message
5. Real-time updates appear as the vehicle responds

### Step 6: View Real-Time Response

The response section displays:

**Status Badges**:
- **Pending** (yellow): Command sent, waiting for vehicle response
- **Success** (green): Command executed successfully
- **Failed** (red): Command failed (see error message)

**Response Data**:
- **Timestamp**: When the response was received
- **Status Code**: HTTP status code (200 = success)
- **Data**: Response payload from the vehicle (JSON format)
- **Duration**: How long the command took to execute

**Example Response**:
```json
{
  "status": "success",
  "data": {
    "dtc_codes": [
      "P0171 - System Too Lean (Bank 1)",
      "P0420 - Catalyst System Efficiency Below Threshold"
    ]
  },
  "timestamp": "2025-10-30T14:35:12.345Z"
}
```

---

## Viewing Command History

### Step 1: Navigate to History Page

Click **History** in the navigation bar.

### Step 2: Browse Command History

The history page shows all commands you've executed (or all commands system-wide for admins):

| Column | Description |
|--------|-------------|
| **Timestamp** | When the command was submitted |
| **Vehicle** | VIN of the target vehicle |
| **Command Type** | Type of command executed |
| **Status** | Result (Success/Failed) |
| **Duration** | Execution time |
| **Actions** | View details |

### Step 3: View Command Details

Click **View** next to a command to see:
- **Full request payload** (parameters sent)
- **Full response payload** (data received)
- **Execution timeline** (sent → processing → completed)
- **Error details** (if command failed)

### Step 4: Filter and Search

Use the filters to narrow down history:
- **Date Range**: Last 24 hours, last 7 days, last 30 days, custom range
- **Vehicle**: Filter by specific VIN
- **Command Type**: Filter by command type
- **Status**: Show only successful or failed commands

**Example Search**:
- Show all failed ReadDTC commands on vehicle `WDD1234567890ABCD` in the last 7 days

### Step 5: Export History (Admin Only)

Admins can export command history to CSV:
1. Apply desired filters
2. Click **Export to CSV** button
3. Open the downloaded file in Excel or Google Sheets

**CSV Format**:
```csv
timestamp,vehicle_vin,command_type,status,duration_ms,user
2025-10-30 14:35:12,WDD1234567890ABCD,ReadDTC,success,1234,engineer
2025-10-30 14:40:23,WDD0987654321ZYXW,ClearDTC,success,2345,admin
```

---

## Real-Time Command Updates

The SOVD application uses WebSockets to provide real-time updates without refreshing the page.

### What You'll See

When you execute a command:

1. **Immediate Feedback**: "Command submitted" notification
2. **Status Updates**: Command status changes (Pending → Processing → Success/Failed)
3. **Response Data**: Vehicle response appears as soon as it's received
4. **Error Notifications**: Instant alerts if something goes wrong

### Connection Status Indicator

In the bottom-right corner, you'll see a **WebSocket Status** indicator:

- **Connected** (green): Real-time updates active
- **Connecting** (yellow): Establishing connection
- **Disconnected** (red): Real-time updates unavailable

**If Disconnected**:
1. Check your network connection
2. Refresh the page (Ctrl+R or Cmd+R)
3. If problem persists, contact support (see [Troubleshooting](#troubleshooting))

### Push Notifications

You'll receive browser notifications for:
- Command completion (when you're on a different tab)
- Command failures
- Vehicle disconnections (if you're monitoring a specific vehicle)

**To Enable**:
- Click "Allow" when prompted for notification permissions
- Or enable in browser settings: Site Settings → Notifications → Allow

---

## User Profile and Settings

### Viewing Your Profile

**Step 1**: Click your username in the top-right corner.

**Step 2**: Select **Profile** from the dropdown menu.

Your profile shows:
- **Username**: Your login username
- **Role**: Your permission level (Engineer or Admin)
- **Email**: Contact email (if configured)
- **Last Login**: Timestamp of your last successful login
- **Total Commands**: Number of commands you've executed

### Changing Your Password

**Step 1**: In your profile, click **Change Password**.

**Step 2**: Enter:
- Current password
- New password (minimum 8 characters)
- Confirm new password

**Step 3**: Click **Update Password**.

**Security Tip**: Use a strong password with a mix of letters, numbers, and symbols.

### Notification Preferences

Configure which notifications you want to receive:
- [ ] Command completion notifications
- [ ] Command failure alerts
- [ ] Vehicle connection status changes
- [ ] System maintenance alerts

**Note**: Email notifications require email configuration by your administrator.

---

## Troubleshooting

### Issue: Cannot Log In

**Symptoms**: "Invalid credentials" error

**Solutions**:
1. Verify username and password (check for typos)
2. Ensure Caps Lock is off
3. Contact your administrator to reset your password
4. Check that backend is running: http://localhost:8000/docs

### Issue: No Vehicles Showing

**Symptoms**: Vehicle list is empty

**Solutions**:
1. Verify database has been initialized (see [deployment.md](../runbooks/deployment.md))
2. Check backend logs: `docker-compose logs backend`
3. Contact administrator to add vehicles to the system

### Issue: Cannot Execute Commands

**Symptoms**: "Command submission failed" error

**Solutions**:
1. Verify vehicle is connected (green status indicator)
2. Check WebSocket connection status (bottom-right)
3. Ensure your session hasn't expired (log out and log back in)
4. Check command parameters are valid JSON

### Issue: Real-Time Updates Not Working

**Symptoms**: Command status doesn't update automatically

**Solutions**:
1. Check WebSocket status indicator (should be green)
2. Refresh the page (Ctrl+R or Cmd+R)
3. Check browser console for errors (F12 → Console tab)
4. Verify Redis is running: `docker-compose ps redis`

### Issue: Slow Command Execution

**Symptoms**: Commands take >5 seconds to complete

**Solutions**:
1. Check vehicle network connectivity
2. Verify vehicle is powered on and responsive
3. Check backend performance: http://localhost:9090 (Prometheus)
4. Review [monitoring.md](../runbooks/monitoring.md) for performance diagnostics

### Getting Help

If you cannot resolve an issue:
1. **Check Documentation**: [troubleshooting.md](../runbooks/troubleshooting.md)
2. **Contact Support**: support@yourdomain.com
3. **Slack Channel**: #sovd-support
4. **Emergency**: Call on-call engineer (PagerDuty)

---

## Common Use Cases

### Use Case 1: Diagnosing a Vehicle Error

**Scenario**: A vehicle has a "Check Engine" light illuminated.

**Steps**:
1. Log in to the SOVD application
2. Navigate to **Vehicles** and find the vehicle by VIN
3. Click **View** to check vehicle status (ensure it's connected)
4. Navigate to **Commands**
5. Select the vehicle from the dropdown
6. Choose **ReadDTC** command type
7. Leave parameters empty
8. Click **Execute Command**
9. Wait for response (should take 1-3 seconds)
10. Review the DTC codes in the response data

**Example Response**:
```json
{
  "dtc_codes": [
    "P0171 - System Too Lean (Bank 1)",
    "P0420 - Catalyst System Efficiency Below Threshold"
  ]
}
```

**Next Steps**:
- Research the DTC codes to understand the issue
- Perform necessary repairs
- Return to clear the codes (see Use Case 2)

---

### Use Case 2: Clearing Error Codes After Repair

**Scenario**: After repairing a vehicle, you need to clear the stored error codes.

**Steps**:
1. Navigate to **Commands**
2. Select the repaired vehicle
3. Choose **ClearDTC** command type
4. Leave parameters empty
5. Click **Execute Command**
6. Wait for confirmation: `{"status": "success", "message": "DTCs cleared"}`
7. Optionally, execute **ReadDTC** again to verify codes are cleared

**Warning**: Only clear DTCs after confirming repairs are complete. Clearing codes without fixing the underlying issue will cause them to return.

---

### Use Case 3: Reading Vehicle Data (Speed, RPM, Temperature)

**Scenario**: You need to monitor vehicle data in real-time.

**Steps**:
1. Navigate to **Commands**
2. Select the vehicle
3. Choose **ReadDataByIdentifier** command type
4. Enter parameters to specify which data point to read

**Example Parameters**:

**For Vehicle Speed**:
```json
{
  "identifier": "0x010D"
}
```

**For Engine RPM**:
```json
{
  "identifier": "0x010C"
}
```

**For Coolant Temperature**:
```json
{
  "identifier": "0x0105"
}
```

5. Click **Execute Command**
6. Review the response data

**Example Response**:
```json
{
  "identifier": "0x010D",
  "value": 65,
  "unit": "km/h"
}
```

**Tip**: You can execute multiple ReadDataByIdentifier commands in sequence to monitor multiple parameters.

---

### Use Case 4: Monitoring Fleet Health

**Scenario**: As a fleet manager, you want to monitor the health of all vehicles.

**Steps**:
1. Navigate to **Vehicles**
2. Review the status column for all vehicles
3. Note any vehicles showing "Disconnected" status
4. For each connected vehicle, click **View** to see recent activity
5. Navigate to **History** to review recent commands across the fleet
6. Filter by "Failed" status to identify vehicles with issues
7. Open Grafana dashboards (http://localhost:3001) to view fleet metrics

**Key Metrics to Monitor**:
- **Vehicle Connectivity**: All vehicles should be "Connected"
- **Command Success Rate**: Should be >95%
- **Response Time**: Should be <3 seconds (P95)

**Proactive Actions**:
- Investigate vehicles with repeated command failures
- Schedule maintenance for vehicles with persistent DTCs
- Alert vehicle owners if connectivity issues arise

---

### Use Case 5: Auditing User Activity (Admin Only)

**Scenario**: As an administrator, you need to audit who executed commands on a specific vehicle.

**Steps**:
1. Navigate to **History**
2. Apply filters:
   - **Vehicle**: Select specific VIN
   - **Date Range**: Choose audit period (e.g., last 30 days)
3. Review the command history table
4. Note the **User** column showing who executed each command
5. Click **View** on suspicious commands to see full details
6. Optionally, export to CSV for external analysis

**Audit Use Cases**:
- Compliance reporting
- Investigating unauthorized access
- Performance reviews
- Incident investigation

**Audit Log Retention**: Audit logs are retained for 90 days (see [disaster_recovery.md](../runbooks/disaster_recovery.md)).

---

### Use Case 6: Performing a Software Update (Advanced)

**Scenario**: You need to update vehicle firmware over-the-air.

**Steps**:

**Phase 1: Initiate Download**
1. Navigate to **Commands**
2. Select the vehicle
3. Choose **RequestDownload** command type
4. Enter parameters:
```json
{
  "data_format_identifier": "0x00",
  "address_and_length_format_identifier": "0x44",
  "memory_address": "0x00100000",
  "memory_size": "0x00010000"
}
```
5. Click **Execute Command**
6. Wait for confirmation: `{"status": "success"}`

**Phase 2: Transfer Data**
7. Choose **TransferData** command type
8. Enter firmware data in chunks (repeat for each block):
```json
{
  "block_sequence_counter": 1,
  "transfer_request_parameter_record": "<base64_encoded_firmware_data>"
}
```
9. Repeat for all data blocks (monitor progress in response)

**Phase 3: Complete Transfer**
10. Choose **RequestTransferExit** command type
11. Leave parameters empty
12. Click **Execute Command**
13. Wait for confirmation: `{"status": "success", "message": "Transfer complete"}`

**Verification**:
14. Read firmware version to confirm update:
```json
{
  "identifier": "0xF195"
}
```

**Warning**: Software updates can brick vehicles if interrupted. Ensure stable network connection and sufficient battery power before starting.

---

## Best Practices

### For Engineers

1. **Always verify vehicle status** before executing commands
2. **Use meaningful command parameters** with clear identifiers
3. **Document unusual responses** in your team's knowledge base
4. **Monitor command history** to avoid duplicate operations
5. **Log out when done** to protect your session

### For Administrators

1. **Regularly review audit logs** for security and compliance
2. **Monitor fleet connectivity** using Grafana dashboards
3. **Set up alerts** for critical issues (vehicle disconnections, high error rates)
4. **Backup command history** regularly (see [disaster_recovery.md](../runbooks/disaster_recovery.md))
5. **Train users** on safe command execution practices

### Security Guidelines

1. **Never share your credentials** with other users
2. **Use strong passwords** (minimum 8 characters, mixed case, numbers, symbols)
3. **Change passwords regularly** (every 90 days recommended)
4. **Log out on shared computers** to prevent unauthorized access
5. **Report suspicious activity** immediately to your administrator

---

## Keyboard Shortcuts

Speed up your workflow with these keyboard shortcuts:

| Shortcut | Action |
|----------|--------|
| `Alt+V` | Navigate to Vehicles page |
| `Alt+C` | Navigate to Commands page |
| `Alt+H` | Navigate to History page |
| `Ctrl+Enter` | Execute command (when on Commands page) |
| `Ctrl+K` | Open search bar |
| `Esc` | Close modal/dialog |
| `F5` | Refresh page |

**Note**: Shortcuts may vary by browser and operating system.

---

## FAQs

**Q: How long does a command take to execute?**
A: Typically 1-3 seconds. Commands taking >5 seconds may indicate network issues.

**Q: Can I execute commands on multiple vehicles simultaneously?**
A: Not directly in the UI. You can use the REST API for batch operations (see API docs at `/docs`).

**Q: What happens if a vehicle disconnects during command execution?**
A: The command will fail with a timeout error after 10 seconds. You'll see a "Vehicle unreachable" message.

**Q: Can I undo a command (e.g., ClearDTC)?**
A: No, commands are not reversible. Always confirm before executing destructive operations.

**Q: How do I add a new vehicle to the system?**
A: Contact your administrator. Vehicles must be registered in the database with their VIN and IP address.

**Q: What's the difference between Engineer and Admin roles?**
A: Engineers can execute commands and view history for their own actions. Admins can view all users' history, manage vehicles, and access system settings.

**Q: Can I access the application from my mobile phone?**
A: Yes, the UI is responsive and works on mobile devices. However, a desktop browser is recommended for the best experience.

**Q: What browsers are supported?**
A: Chrome, Firefox, Safari, and Edge (latest versions). Internet Explorer is not supported.

---

## Additional Resources

- **Deployment Guide**: [deployment.md](../runbooks/deployment.md) - How to set up the application
- **Troubleshooting Guide**: [troubleshooting.md](../runbooks/troubleshooting.md) - Detailed diagnostic procedures
- **Monitoring Guide**: [monitoring.md](../runbooks/monitoring.md) - Understanding metrics and dashboards
- **API Documentation**: http://localhost:8000/docs - REST API reference for automation
- **SOVD Specification**: [Official SOVD documentation](https://www.asam.net/standards/detail/sovd/) - Protocol details

---

## Feedback and Support

We're constantly improving the SOVD Web Application. Your feedback is valuable!

**Report Issues**:
- **Email**: support@yourdomain.com
- **Slack**: #sovd-support
- **GitHub**: https://github.com/your-org/sovd (for bug reports and feature requests)

**Request Features**:
- Submit feature requests via GitHub Issues
- Discuss ideas in the Slack channel

**Training**:
- New user onboarding: Contact your manager
- Advanced training: Quarterly workshops (check calendar)

---

**Document Version**: 1.0
**Last Updated**: 2025-10-30
**Owner**: Product Team
**For**: Engineers and Administrators

Thank you for using the SOVD Web Application! Happy diagnosing! 🚗🔧
