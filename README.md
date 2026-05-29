# FancyQR

FancyQR is a web service and CLI tool for generating styled SVG QR codes. It includes a built-in, password-protected URL shortener with basic statistics tracking.

## Features

- Generate customizable SVG QR codes (colors, error correction, embedded logos).
- URL shortening service with visit tracking (clicks, user-agent, referer).
- Admin dashboard for managing links (list, update, delete).
- Native Nix and NixOS compatibility.

## Running Locally

The project uses `uv` for dependency management.

```bash
# Start the web server
uv run python app.py --port 8000
```

Access the generator at `http://localhost:8000`.

## Configuration

The service is configured using environment variables:

- `FANCYQR_PASSWORD`: Sets a password to protect the link shortening endpoint, statistics, and the admin dashboard. If left unset, shortening is public.
- `FANCYQR_DB_PATH`: Path to the SQLite database file. Defaults to `links.db` in the current directory.

## Admin Dashboard

Access the dashboard at `/dashboard` to view link statistics, update destination URLs, and manage your shortened links. Authentication requires the `FANCYQR_PASSWORD` to be set.

## Reverse Proxy (Nginx)

When running behind a reverse proxy like Nginx, ensure that the `X-FancyQR-Password` header is passed through to the application.

```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # Ensure custom auth header is passed
    proxy_set_header X-FancyQR-Password $http_x_fancyqr_password;
}
```

## NixOS Deployment

A Nix flake is provided, including a NixOS module for systemd service management.

```nix
services.fancyqr = {
  enable = true;
  port = 8000;
  # Securely load the FANCYQR_PASSWORD from a file
  passwordFile = "/path/to/your/secret/password-file";
};
```
