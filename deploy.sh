cat > /var/www/aidamcell.com/deploy.sh << 'EOF'
#!/bin/bash
echo "=== Redeploying AI Teaching Assistant ==="

# Stop old backend
pkill -f api_server.py

# Start backend
cd /var/www/aidamcell.com
nohup python3 api_server.py > api.log 2>&1 &

sleep 2

# Check
if ps aux | grep -v grep | grep api_server.py > /dev/null; then
    echo "✓ Backend running"
else
    echo "✗ Backend failed"
    exit 1
fi

# Restart nginx
sudo systemctl restart nginx
echo "✓ Nginx restarted"

echo "✅ Deployment complete - http://8.211.150.68/"
EOF

chmod +x /var/www/aidamcell.com/deploy.sh