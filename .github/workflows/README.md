# GitHub Actions Workflows

## Deploy to Develop

This workflow automatically deploys the iCards MCP server when code is pushed to the `develop` branch.

### Required GitHub Secrets

You need to configure the following secrets in your GitHub repository settings:

#### Environment Secrets (recommended)
Create an environment called `hostinger` and add these secrets:

- `SSH_HOST`: **IMPORTANT**: Your server's actual IP address (like `123.45.67.89`) or resolvable hostname. **NOT** "hostinger" - that won't work!
- `SSH_PASSWORD`: The SSH password for the root user
- `PROJECT_PATH`: (Optional) Path to your project on the server. Defaults to `/root/iCardsMCP`

#### Alternative: Repository Secrets
You can also add them as repository secrets (not environment-specific).

### Setup Steps

1. Go to your repository on GitHub
2. Navigate to Settings → Environments
3. Create a new environment called `hostinger`
4. In the environment settings, add the required secrets:
   - `SSH_HOST`: Your server's IP address
   - `SSH_PASSWORD`: SSH password for root user
   - `PROJECT_PATH`: Path where the project is located on your server (optional, defaults to `/root/iCardsMCP`)

**Note**: The workflow is configured to use the `hostinger` environment where your secrets are already defined.

### What the workflow does

1. Triggers on push to `develop` branch
2. Connects to your server via SSH
3. Pulls the latest code changes
4. Installs uv if not present
5. Updates dependencies with `uv sync`
6. Stops any existing server process
7. Starts the new server with `uv run python server.py`
8. Verifies the server is running and responding

### Monitoring

The server runs in the background and logs to `server.log` in your project directory. You can monitor it by:

```bash
# Check if server is running
ps aux | grep "python server.py"

# View recent logs
tail -f server.log

# Check server health
curl http://localhost:3001/sse
```
