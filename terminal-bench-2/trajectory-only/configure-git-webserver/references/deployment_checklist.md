# Deployment Configuration Reference

## Service Persistence Patterns

### Systemd Service (Linux)

Create `/etc/systemd/system/git-webserver.service`:

```ini
[Unit]
Description=Git Web Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/html
ExecStart=/usr/bin/python3 -m http.server 8080
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
systemctl daemon-reload
systemctl enable git-webserver
systemctl start git-webserver
```

### Supervisor (Alternative)

Create `/etc/supervisor/conf.d/webserver.conf`:

```ini
[program:webserver]
command=python3 -m http.server 8080
directory=/var/www/html
autostart=true
autorestart=true
stderr_logfile=/var/log/webserver.err.log
stdout_logfile=/var/log/webserver.out.log
```

### Screen/tmux (Development)

```bash
screen -dmS webserver bash -c 'cd /var/www/html && python3 -m http.server 8080'
```

Reattach: `screen -r webserver`

## Post-Receive Hook Patterns

### Basic Deployment Hook

```bash
#!/bin/bash
while read oldrev newrev refname; do
    branch=$(echo $refname | sed 's/refs\/heads\///')
    if [ "$branch" = "main" ] || [ "$branch" = "master" ]; then
        GIT_WORK_TREE=/var/www/html git checkout -f $branch
    fi
done
```

### Hook with Logging

```bash
#!/bin/bash
LOG_FILE="/var/log/deploy.log"

while read oldrev newrev refname; do
    branch=$(echo $refname | sed 's/refs\/heads\///')
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    if [ "$branch" = "main" ] || [ "$branch" = "master" ]; then
        echo "[$timestamp] Deploying $branch ($oldrev -> $newrev)" >> $LOG_FILE
        GIT_WORK_TREE=/var/www/html git checkout -f $branch 2>> $LOG_FILE
        if [ $? -eq 0 ]; then
            echo "[$timestamp] Deployment successful" >> $LOG_FILE
        else
            echo "[$timestamp] Deployment FAILED" >> $LOG_FILE
        fi
    fi
done
```

### Hook with Build Step

```bash
#!/bin/bash
DEPLOY_DIR=/var/www/html
BUILD_DIR=/tmp/build-$$

while read oldrev newrev refname; do
    branch=$(echo $refname | sed 's/refs\/heads\///')

    if [ "$branch" = "main" ] || [ "$branch" = "master" ]; then
        # Checkout to temp directory
        mkdir -p $BUILD_DIR
        GIT_WORK_TREE=$BUILD_DIR git checkout -f $branch

        # Run build (if needed)
        cd $BUILD_DIR
        # npm install && npm run build  # Example for Node.js

        # Deploy
        rsync -a --delete $BUILD_DIR/ $DEPLOY_DIR/

        # Cleanup
        rm -rf $BUILD_DIR
    fi
done
```

## Permission Configuration

### Shared Group Access

```bash
# Create deployment group
groupadd deploy

# Add users to group
usermod -aG deploy gituser
usermod -aG deploy www-data

# Set directory permissions
chown -R gituser:deploy /var/www/html
chmod -R 775 /var/www/html
chmod g+s /var/www/html  # New files inherit group
```

### SSH Key Setup for Remote Access

```bash
# On client machine
ssh-keygen -t ed25519 -C "deploy-key"

# On server, add to authorized_keys
cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys

# Test connection
ssh user@server "echo 'SSH works'"
```

## Troubleshooting Commands

```bash
# Check if port is in use
ss -tlnp | grep 8080
lsof -i :8080

# Kill process on port
fuser -k 8080/tcp

# Check hook permissions
ls -la /git/server/hooks/post-receive

# Test hook syntax
bash -n /git/server/hooks/post-receive

# View recent git activity
cd /git/server && git log --oneline -5

# Check web server response
curl -I http://localhost:8080/

# Verify directory permissions
ls -la /var/www/html
stat /var/www/html
```

## Directory Structure Reference

```
/git/server/              # Bare repository
├── HEAD
├── config
├── hooks/
│   └── post-receive      # Deployment hook (executable)
├── objects/
└── refs/

/var/www/html/            # Web root (deployed content)
├── index.html
└── ...
```
