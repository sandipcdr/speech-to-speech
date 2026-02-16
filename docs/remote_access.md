# Remote Access Guide

Browsers block microphone access on insecure connections (HTTP) unless the origin is `localhost`. Since you are running the application on a remote server (`119.82.96.68`) and accessing it via HTTP, the browser refuses to open the microphone.

Here are the two ways to fix this:

## Option 1: SSH Port Forwarding (Recommended for Testing)

This "tricks" your browser into thinking the remote app is running on your local machine.

1.  **On your local computer** (not the server), open a terminal.
2.  Run this command (replace `user` with your server username):
    ```bash
    ssh -L 3001:localhost:3001 -L 8001:localhost:8001 your-username@119.82.96.68
    ```
3.  Leave this terminal window open.
4.  Open your browser to `http://localhost:3001`.
5.  Microphone access will now work because `localhost` is considered a Secure Context.

## Option 2: Set up HTTPS (Recommended for Production)

If you want to share the link with others, you must set up HTTPS. This is more complex and requires a domain name.

1.  **Get a Domain**: Buy a domain (e.g., `translator.com`) and point it to `119.82.96.68`.
2.  **Reverse Proxy**: Install Nginx or Caddy on your server.
3.  **SSL Certificate**: Use Certbot (Let's Encrypt) to get a free SSL certificate.
4.  **Configuration**:
    *   Forward `https://your-domain.com` -> `http://localhost:3001`
    *   Forward `wss://your-domain.com/ws` -> `http://localhost:8001/ws`
