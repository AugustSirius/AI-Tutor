# AI Chat Interface - aidamcell.com

A minimalistic chat interface for AI conversations.

## Features

- 🎨 Clean, minimal design
- 📱 Mobile responsive
- 📚 Sidebar with system prompt and class materials (read-only)
- 💬 Chat interface similar to Claude
- 🚀 Easy deployment to GitHub Pages or AliCloud

## Deployment Options

### Option 1: GitHub Pages (Recommended for Static Sites)

#### Step 1: Create a GitHub Repository
1. Go to https://github.com/new
2. Name your repository: `aidamcell.com` or `your-username.github.io`
3. Set to **Public**
4. DO NOT initialize with README

#### Step 2: Push Your Code
```bash
# Navigate to your project folder
cd /path/to/your/project

# Initialize git
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit"

# Add your GitHub repository as remote
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git

# Push to GitHub
git branch -M main
git push -u origin main
```

#### Step 3: Enable GitHub Pages
1. Go to your repository on GitHub
2. Click **Settings** → **Pages**
3. Under "Source", select **main** branch
4. Click **Save**

#### Step 4: Configure Custom Domain
1. In the same Pages settings, under "Custom domain"
2. Enter: `aidamcell.com`
3. Click **Save**
4. The CNAME file in your repo will be automatically recognized

#### Step 5: DNS Configuration
Add these DNS records at your domain registrar:

**For apex domain (aidamcell.com):**
```
Type: A
Name: @
Value: 185.199.108.153

Type: A
Name: @
Value: 185.199.109.153

Type: A
Name: @
Value: 185.199.110.153

Type: A
Name: @
Value: 185.199.111.153
```

**For www subdomain (optional):**
```
Type: CNAME
Name: www
Value: YOUR-USERNAME.github.io
```

**Wait 24-48 hours for DNS propagation.**

---

### Option 2: AliCloud (For Dynamic/Full Stack Apps)

AliCloud offers several hosting options:

#### A. AliCloud OSS (Object Storage - Best for Static Sites)

**Information Needed:**
- AccessKey ID
- AccessKey Secret
- OSS Bucket name
- Region (e.g., oss-cn-hangzhou)

**Deployment Steps:**
1. Install ossutil
2. Configure credentials
3. Upload files
4. Enable static website hosting
5. Configure CDN (optional)

**Command Example:**
```bash
# Configure ossutil
./ossutil config

# Upload files
./ossutil cp -r ./ oss://your-bucket-name/
```

#### B. AliCloud ECS (Elastic Compute Service - For Full Apps)

**Information Needed:**
- ECS Instance IP address
- SSH username (usually root)
- SSH password or key file
- Region

**Deployment Steps:**
1. SSH into your ECS instance
2. Install nginx or web server
3. Upload files via SCP/SFTP
4. Configure nginx
5. Set up SSL certificate

**Command Example:**
```bash
# SSH into server
ssh root@YOUR_ECS_IP

# Install nginx
apt update && apt install nginx -y

# Upload files
scp -r ./* root@YOUR_ECS_IP:/var/www/html/

# Configure nginx (see nginx config below)
```

#### C. AliCloud Web Hosting

**Information Needed:**
- FTP hostname
- FTP username
- FTP password
- Control panel login

**Deployment:**
Use FileZilla or any FTP client to upload files to the web root directory.

---

## Customization

### Update System Prompt
Edit line 148 in `index.html`:
```javascript
You are a helpful AI assistant...
```

### Update Class Materials
Edit line 154 in `index.html`:
```javascript
No class materials loaded yet...
```

### Connect Real AI API

#### For Anthropic Claude API:
1. Get API key from: https://console.anthropic.com/
2. Edit line 235 in `index.html`:
```javascript
const API_KEY = 'YOUR_ANTHROPIC_API_KEY';
```
3. Uncomment the API call section (lines 262-279)

#### For OpenAI API:
Change the API endpoint and adjust the request format accordingly.

#### For Custom Backend:
Update `API_URL` to your backend endpoint.

---

## Security Notes

⚠️ **IMPORTANT**: Never expose API keys in frontend code in production!

For production, you should:
1. Create a backend server to handle API calls
2. Store API keys on the server
3. Frontend calls your backend, which then calls the AI API

Example backend setup (Node.js):
```javascript
// server.js
const express = require('express');
const app = express();

app.post('/api/chat', async (req, res) => {
    // Call AI API with server-side API key
    // Return response to frontend
});

app.listen(3000);
```

---

## File Structure

```
.
├── index.html          # Main chat interface
├── CNAME              # Custom domain configuration
└── README.md          # This file
```

---

## What Information I Need for AliCloud Deployment

Please provide:

### For OSS (Static Site):
- [ ] AccessKey ID
- [ ] AccessKey Secret  
- [ ] Preferred region (e.g., cn-hangzhou, cn-shanghai)
- [ ] Bucket name (or I can help create one)

### For ECS (Server):
- [ ] ECS Instance IP address
- [ ] SSH username
- [ ] SSH password or private key
- [ ] Operating system (Ubuntu/CentOS/etc.)

### For Web Hosting:
- [ ] FTP hostname
- [ ] FTP username
- [ ] FTP password

---

## Support

For issues or questions, check:
- GitHub Pages: https://docs.github.com/pages
- AliCloud Docs: https://www.alibabacloud.com/help

---

## License

Free to use and modify for personal and commercial projects.