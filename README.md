# PRESIS

- Marketing/business site: `presis.pro`
- App site: `app.presis.pro`
- Dev site: `dev.presis.pro`

## Docker Container

To run the app in a Docker container:

```bash
# Build the Docker image
docker build -f infra/Dockerfile -t presis-app .

# Run the container with custom admin credentials
docker run -p 3000:3000 \
  -e ADMIN_EMAIL=your_admin@example.com \
  -e ADMIN_PASSWORD=your_password \
  presis-app
```

The container will automatically create an admin user on startup if one doesn't exist yet.
Default admin credentials (if not overridden):
- Email: admin@example.com
- Password: adminpassword

## App Development

```
python3 -m venv .venv
source .venv/bin/activate
pip install .
```

### CLI

`$ presis -h`

```
u$ presis -h
usage: presis [-h] [-p PATH] [-r] [-d] [-P] project

positional arguments:
  project               project name

options:
  -h, --help            show this help message and exit
  -p PATH, --path PATH  Path to the JSON data file
  -r, --report          Calculate and display a report of the time spent in the project
  -d, --daily-report    Generate a daily report of hours worked per day in the project
  -P, --plot            Graph the time spent in the project
```

## Web App

```bash
source .venv/bin/activate
pip install -r requirements-app.txt
python app/app.py
```

## Kivy App

```bash
source .venv/bin/activate
python kivy_presis/main.py
```

## Infra

Ensure all values in terraform/prod/.tf.deploy-env

```
./deploy.sh prod plan
./deploy.sh prod apply
```

## Architecture

```
                          +---------------------------+
                          |       Web Service         |
                          |         Cluster           |
                          |                           |
      +------------+      |  +-------------------+    |
      |  CLI User  +---------+                   |    |
      +------------+      |  |                   |    |
                          |  |                   |    |
      +------------+      |  |                   |    |
      |  App User  +---------+    Flask App      |    |
      +------------+      |  |  (Handles Auth    |    |
                          |  |  and Proxies)     |    |
      +------------+      |  |                   |    |
      |  Web User  +---------+                   |    |
      +------------+      |  |                   |    |
                          |  +-------------------+    |
                          |           |               |
                          |           v               |
                          |  +-------------------+    |
                          |  |                   |    |
                          |  |                   |    |
                          |  |   Redis Server    |    |
                          |  |                   |    |
                          |  |  (Data Store)     |    |
                          |  |                   |    |
                          |  +-------------------+    |
                          +---------------------------+
```
