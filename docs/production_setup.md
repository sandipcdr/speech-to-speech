# Production Deployment Guide (Domain + SSL)

To make your application accessible to anyone with a secure connection (enabling microphone access), follow these steps.

## 1. Get a Domain Name
*   Buy a domain from a registrar (Namecheap, GoDaddy, Google Domains, etc.).
*   Example: `myspeechapp.com`

## 2. Configure DNS
*   Go to your domain registrar's DNS settings.
*   Add an **A Record**:
    *   **Name**: `@` (or `www`)
    *   **Value**: `119.82.96.68` (Your server IP)
    *   **TTL**: Automatic or 1 hour.

## 3. Install Nginx and Certbot on Server
SSH into your server and run:
```bash
sudo apt update
sudo apt install nginx certbot python3-certbot-nginx
```

## 4. Configure Nginx
1.  Copy the example config provided in this repo (`nginx.conf.example`) to `/etc/nginx/sites-available/speech-app`.
    ```bash
    sudo nano /etc/nginx/sites-available/speech-app
    # Paste content, replace 'your-domain.com' with your actual domain
    ```
2.  Link it to enabled sites:
    ```bash
    sudo ln -s /etc/nginx/sites-available/speech-app /etc/nginx/sites-enabled/
    sudo rm /etc/nginx/sites-enabled/default  # Remove default logic
    ```
3.  Test configuration:
    ```bash
    sudo nginx -t
    ```
4.  Restart Nginx:
    ```bash
    sudo systemctl restart nginx
    ```

## 5. Enable SSL (HTTPS)
Run Certbot to automatically get a free Let's Encrypt certificate and update Nginx:
```bash
sudo certbot --nginx -d your-domain.com
```
*   Follow the prompts.
*   Certbot will automatically modify your Nginx config to add the SSL paths.

## 6. Verification
*   Open `https://your-domain.com` in your browser.
*   The "Secure" lock icon should appear.
*   Microphone access will now work without any SSH tunneling!
