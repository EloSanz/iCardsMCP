# GitHub Actions Workflows

## Deploy to Develop (PR)

This workflow automatically deploys the iCards MCP server when a Pull Request targets the `develop` branch.

### Required GitHub Secrets

You need to configure the following secrets in your GitHub repository settings:

#### Environment Secrets (recommended)
Create an environment called `hostinger` and add these secrets:

- `SSH_HOST`: **IMPORTANT**: Your server's actual IP address (like `123.45.67.89`) or resolvable hostname. **NOT** "hostinger" - that won't work!
- `SSH_PASSWORD`: The SSH password for the root user
- `PROJECT_PATH`: (Optional) Path to your project on the server. Defaults to `/root/iCardsMCP`

### Setup Steps

1. Go to your repository on GitHub
2. Navigate to Settings → Environments
3. Create a new environment called `hostinger`
4. In the environment settings, add the required secrets:
   - `SSH_HOST`: Your server's IP address
   - `SSH_PASSWORD`: SSH password for root user
   - `PROJECT_PATH`: Path where the project is located on your server (optional, defaults to `/root/iCardsMCP`)

**Note**: The workflow is configured to use the `hostinger` environment where your secrets are already defined.

### When it runs

The workflow runs automatically when:
- A Pull Request is created targeting the `develop` branch
- A Pull Request targeting `develop` is updated (new commits, etc.)

### What the workflow does

1. Triggers on Pull Requests to `develop` branch
2. Connects to your server via SSH
3. Pulls the latest code changes
4. Updates dependencies with `uv sync`
5. Stops any existing server process
6. Tests that the server can start successfully
7. Starts the production server and leaves it running

### Monitoring

The server runs continuously on your server. You can monitor it by:

```bash
# Check if server is running
ps aux | grep "python server.py"

# View server logs (if configured)
tail -f server.log

# Check server health
curl http://localhost:3001/sse
```

**Note**: The workflow assumes the server starts successfully. If you need more detailed health checks, you can add them to your server's startup scripts.
