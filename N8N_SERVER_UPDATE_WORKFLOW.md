# Ubuntu/Debian Server Updates Workflow

**Workflow ID**: `Ikau3rRnpRG1okvq`
**Status**: Created (inactive)
**Created**: 2025-11-22

## Overview

This n8n workflow automates system updates for Ubuntu and Debian servers via SSH. It can run updates on multiple servers in parallel and aggregates the results.

## Workflow Structure

The workflow consists of 6 nodes:

1. **Manual Trigger** - Starts the workflow manually
2. **Set Server List** - Defines which servers to update
3. **Split Servers** - Processes each server individually
4. **Update Packages** - Executes apt update commands via SSH
5. **Format Results** - Formats the output for readability
6. **Aggregate Results** - Collects results from all servers

## Update Commands Executed

The workflow runs the following commands on each server:
```bash
sudo apt update && \
sudo apt upgrade -y && \
sudo apt autoremove -y && \
sudo apt autoclean
```

This will:
- Update package lists
- Upgrade all packages (auto-confirm with -y)
- Remove unnecessary packages
- Clean the package cache

## Configuration Steps

### 1. Add Your Servers

In the n8n UI, edit the **"Set Server List"** node and update the servers array:

```javascript
[
  { "hostname": "server1.homelab.com", "name": "Server 1" },
  { "hostname": "server2.homelab.com", "name": "Server 2" },
  { "hostname": "server3.homelab.com", "name": "Server 3" }
]
```

### 2. Configure SSH Credentials

The **"Update Packages"** node requires SSH credentials:

1. Click on the "Update Packages" node
2. Under "Credentials", add SSH credentials for your servers
3. Choose either:
   - **Password authentication** (current default)
   - **SSH key authentication** (recommended)

**Note**: You'll need to create SSH credentials in n8n that can access all your servers. Consider:
- Using the same user account across all servers
- Setting up SSH key-based authentication
- Ensuring the user has sudo privileges without password (or configure sudo password)

### 3. Handle Sudo Password (if needed)

If your servers require a password for sudo, you have two options:

**Option A: Configure passwordless sudo (recommended)**
```bash
# On each server, add to /etc/sudoers.d/nopasswd
your-username ALL=(ALL) NOPASSWD: /usr/bin/apt, /usr/bin/apt-get
```

**Option B: Modify the command to include password**
Update the command in the "Update Packages" node:
```bash
echo 'your-password' | sudo -S apt update && \
echo 'your-password' | sudo -S apt upgrade -y && \
echo 'your-password' | sudo -S apt autoremove -y && \
echo 'your-password' | sudo -S apt autoclean
```
⚠️ **Security Warning**: This stores the password in plain text in the workflow.

### 4. Optional: Add Schedule Trigger

To run updates automatically (e.g., weekly), replace the "Manual Trigger" node:

1. Delete the "Manual Trigger" node
2. Add a "Schedule Trigger" node
3. Configure schedule (example: every Sunday at 2 AM)
4. Connect it to the "Set Server List" node

### 5. Optional: Add Notifications

To get notified of results, add nodes after "Aggregate Results":

**Email Notification:**
- Add "Send Email" node
- Configure with your SMTP settings
- Include the results data

**Slack/Discord/Teams:**
- Add appropriate webhook node
- Format the message with results
- Send to your notification channel

## Testing the Workflow

1. **Start Small**: Test with one server first
2. **Manual Execution**: Use the manual trigger to test
3. **Check Output**: Review the output in the "Aggregate Results" node
4. **Verify Updates**: SSH into a server and check if updates were applied

## Activating the Workflow

Once tested and configured:

```bash
# Using the n8n MCP server
# Activate the workflow
```

Or in the n8n UI:
- Toggle the workflow to "Active"

## Output Format

The workflow returns aggregated results with:
- `server_name`: Friendly name of the server
- `hostname`: Server hostname
- `status`: "success" or "failed"
- `timestamp`: When the update ran

## Troubleshooting

### SSH Connection Failures
- Verify SSH credentials in n8n
- Check network connectivity to servers
- Ensure SSH is enabled on target servers
- Verify firewall rules allow SSH (port 22)

### Sudo Permission Errors
- Ensure user has sudo privileges
- Configure passwordless sudo (see above)
- Check sudoers configuration

### Package Update Failures
- Check server disk space (`df -h`)
- Verify internet connectivity from servers
- Check apt lock files (`sudo rm /var/lib/apt/lists/lock`)
- Review error output in workflow results

### Timeout Issues
- Increase SSH timeout in node settings
- Some updates may take 10+ minutes
- Consider splitting into separate update stages

## Best Practices

1. **Schedule During Low-Traffic Hours**: Run updates at 2-4 AM
2. **Test First**: Always test on a non-production server
3. **Monitor Results**: Set up notifications for failures
4. **Stagger Updates**: For critical servers, update one at a time
5. **Backup Before Updates**: Ensure backups are current
6. **Review Logs**: Check the workflow execution history regularly

## Security Considerations

- Use SSH key authentication instead of passwords
- Limit sudo privileges to only apt commands
- Store credentials securely in n8n
- Use a dedicated update user with minimal privileges
- Consider using a bastion/jump host for SSH access
- Audit update logs regularly

## Future Enhancements

Potential improvements:
- Add pre-update snapshot/backup step
- Check for pending reboots after updates
- Send detailed reports via email
- Add error handling and retry logic
- Check server load before updating
- Skip updates if critical services are running
- Add rollback capability

## Access

**n8n Workflow URL**: https://n8n.homelab.com/workflow/Ikau3rRnpRG1okvq

**Workflow ID**: Ikau3rRnpRG1okvq
