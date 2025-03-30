# Configuring Unraid Docker for Insecure Registry

When working with a local Docker registry that doesn't have proper SSL certificates (insecure registry), you'll need to configure the Docker daemon on your Unraid server to trust this registry. Here's how to do it:

## Editing daemon.json on Unraid

1. SSH into your Unraid server:
   ```bash
   ssh root@192.168.1.15
   ```

2. Check if the daemon.json file already exists:
   ```bash
   ls -la /etc/docker/
   ```

3. Edit the file using vi (or your preferred editor):
   ```bash
   vi /etc/docker/daemon.json
   ```

4. If the file is empty or doesn't exist, add the following content:
   ```json
   {
     "insecure-registries": ["192.168.1.15:5000"]
   }
   ```

5. If the file already exists and has content, add the insecure-registries array or append to it if it already exists:
   ```json
   {
     "existing-setting": "value",
     "insecure-registries": ["192.168.1.15:5000"]
   }
   ```

6. Save and exit vi:
   - Press `ESC` to exit insert mode
   - Type `:wq` and press `Enter` to save and quit

7. Restart the Docker service on Unraid:
   ```bash
   /etc/rc.d/rc.docker restart
   ```

## Verifying the Configuration

After restarting Docker, you can verify the configuration:

1. Check if Docker is using the configuration:
   ```bash
   docker info | grep -A1 "Insecure Registries"
   ```

2. Try pulling from your registry:
   ```bash
   docker pull 192.168.1.15:5000/presis:v0.1.0
   ```

## Troubleshooting

- If you still get "HTTP response to HTTPS client" errors after restarting Docker, make sure:
  - The daemon.json file is properly formatted (valid JSON)
  - The Docker service was fully restarted
  - The registry address in the configuration exactly matches what you're using

- On Unraid, changes to Docker settings sometimes require:
  - Going to the Docker tab in the Unraid web UI
  - Stopping and restarting the Docker service from there

## Using the Registry After Configuration

Once your Unraid Docker daemon is properly configured, you can use the registry normally without the `--insecure-registry` flag:

```bash
# Pull an image
docker pull 192.168.1.15:5000/presis:v0.1.0

# Run a container
docker run -d \
  --name='presis' \
  --net='bridge' \
  -e TZ="America/Los_Angeles" \
  -e HOST_OS="Unraid" \
  -p '5002:5002/tcp' \
  192.168.1.15:5000/presis:v0.1.0
