#!/bin/bash

# AliCloud Deployment Script
# This script helps deploy your site to AliCloud

echo "=========================================="
echo "AliCloud Deployment Helper"
echo "=========================================="
echo ""

# Function to deploy to ECS
deploy_to_ecs() {
    echo "Deploying to AliCloud ECS..."
    echo ""
    
    read -p "Enter your ECS IP address: " ECS_IP
    read -p "Enter SSH username (default: root): " SSH_USER
    SSH_USER=${SSH_USER:-root}
    
    echo ""
    echo "Uploading files to $SSH_USER@$ECS_IP..."
    
    # Create directory on server
    ssh $SSH_USER@$ECS_IP "mkdir -p /var/www/aidamcell.com"
    
    # Upload files
    scp index.html $SSH_USER@$ECS_IP:/var/www/aidamcell.com/
    scp nginx.conf $SSH_USER@$ECS_IP:/tmp/
    
    # Configure nginx
    ssh $SSH_USER@$ECS_IP << 'ENDSSH'
        # Install nginx if not present
        if ! command -v nginx &> /dev/null; then
            apt update && apt install nginx -y
        fi
        
        # Move nginx config
        mv /tmp/nginx.conf /etc/nginx/sites-available/aidamcell.com
        ln -sf /etc/nginx/sites-available/aidamcell.com /etc/nginx/sites-enabled/
        rm -f /etc/nginx/sites-enabled/default
        
        # Test and reload nginx
        nginx -t && systemctl reload nginx
        
        echo "Deployment complete!"
        echo "Your site should be available at http://$HOSTNAME"
ENDSSH
    
    echo ""
    echo "✅ Deployment to ECS complete!"
}

# Function to deploy to OSS
deploy_to_oss() {
    echo "Deploying to AliCloud OSS..."
    echo ""
    
    read -p "Enter your AccessKey ID: " ACCESS_KEY_ID
    read -sp "Enter your AccessKey Secret: " ACCESS_KEY_SECRET
    echo ""
    read -p "Enter your OSS bucket name: " BUCKET_NAME
    read -p "Enter your region (e.g., oss-cn-hangzhou): " REGION
    
    # Check if ossutil is installed
    if ! command -v ossutil &> /dev/null; then
        echo "ossutil not found. Installing..."
        wget http://gosspublic.alicdn.com/ossutil/1.7.14/ossutil64
        chmod 755 ossutil64
        sudo mv ossutil64 /usr/local/bin/ossutil
    fi
    
    # Configure ossutil
    ossutil config -e $REGION.aliyuncs.com -i $ACCESS_KEY_ID -k $ACCESS_KEY_SECRET
    
    # Upload files
    echo "Uploading files to OSS..."
    ossutil cp index.html oss://$BUCKET_NAME/ -f
    ossutil cp CNAME oss://$BUCKET_NAME/ -f
    
    # Set bucket to static website hosting
    ossutil website --method put oss://$BUCKET_NAME index.html index.html
    
    echo ""
    echo "✅ Deployment to OSS complete!"
    echo "Enable static website hosting in OSS console if not already enabled."
}

# Main menu
echo "Select deployment method:"
echo "1) AliCloud ECS (Virtual Server)"
echo "2) AliCloud OSS (Object Storage)"
echo "3) Manual Instructions"
echo ""
read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        deploy_to_ecs
        ;;
    2)
        deploy_to_oss
        ;;
    3)
        echo ""
        echo "Manual Deployment Instructions:"
        echo "================================"
        echo ""
        echo "For ECS:"
        echo "1. SSH into your ECS: ssh root@YOUR_ECS_IP"
        echo "2. Install nginx: apt install nginx -y"
        echo "3. Create directory: mkdir -p /var/www/aidamcell.com"
        echo "4. Upload index.html to /var/www/aidamcell.com/"
        echo "5. Configure nginx with the provided nginx.conf"
        echo "6. Reload nginx: systemctl reload nginx"
        echo ""
        echo "For OSS:"
        echo "1. Log in to AliCloud OSS Console"
        echo "2. Create or select a bucket"
        echo "3. Upload index.html and CNAME"
        echo "4. Enable static website hosting"
        echo "5. Set index.html as index document"
        echo "6. Configure custom domain in OSS console"
        echo ""
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "Next Steps:"
echo "=========================================="
echo "1. Configure your domain DNS to point to AliCloud"
echo "2. Wait for DNS propagation (24-48 hours)"
echo "3. Install SSL certificate (recommended)"
echo "4. Test your site at https://aidamcell.com"
echo ""