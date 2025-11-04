# 🚀 Quick Start Guide - aidamcell.com

## 📦 Files Included

1. **index.html** - Your minimalistic chat interface
2. **CNAME** - GitHub Pages domain configuration
3. **README.md** - Complete deployment instructions
4. **nginx.conf** - Nginx configuration for AliCloud ECS
5. **deploy.sh** - Automated deployment script for AliCloud

## ⚡ Fastest Deployment: GitHub Pages (5 minutes)

```bash
# 1. Create a new GitHub repository
# Go to: https://github.com/new

# 2. Upload files or use command line:
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO.git
git push -u origin main

# 3. Enable GitHub Pages
# Settings → Pages → Source: main branch → Save

# 4. Add custom domain
# Settings → Pages → Custom domain: aidamcell.com → Save

# 5. Configure DNS at your domain registrar:
# Type: A, Name: @, Value: 185.199.108.153
# Type: A, Name: @, Value: 185.199.109.153
# Type: A, Name: @, Value: 185.199.110.153
# Type: A, Name: @, Value: 185.199.111.153
```

**Done!** Your site will be live at aidamcell.com in 24-48 hours.

---

## 🌐 AliCloud Deployment

### Option A: OSS (Static Site - Easiest)

**What I need from you:**
- AccessKey ID
- AccessKey Secret
- Preferred region (e.g., cn-hangzhou)

**Then run:**
```bash
./deploy.sh
# Choose option 2
```

### Option B: ECS (Full Server - More Control)

**What I need from you:**
- ECS Instance IP
- SSH username (usually root)
- SSH password or key file

**Then run:**
```bash
./deploy.sh
# Choose option 1
```

---

## 🎨 Customize Your Chat

### Change System Prompt
Edit `index.html` line 148:
```html
<div class="sidebar-content" id="systemPrompt">
Your custom system prompt here...
</div>
```

### Add Class Materials
Edit `index.html` line 154:
```html
<div class="sidebar-content" id="classMaterials">
Your class materials, notes, and resources here...
</div>
```

### Connect Real AI
Edit `index.html` line 235:
```javascript
const API_KEY = 'your-api-key-here';
```

Then uncomment lines 262-279 to enable the API call.

⚠️ **For production:** Use a backend server to keep API keys secure!

---

## 🔒 Security Note

**Never expose API keys in frontend code!**

For production:
1. Create a backend (Node.js, Python, etc.)
2. Store API key on server
3. Frontend → Backend → AI API

---

## 📞 Need Help?

Reply with:
- Your preferred deployment method (GitHub/AliCloud)
- Required credentials (see above)
- Any customization requests

I'll help you deploy!

---

## ✅ Test Your Site Locally

```bash
# Simple HTTP server
python3 -m http.server 8000
# Or
npx serve

# Open: http://localhost:8000
```

---

**Ready to deploy? Let's do it! 🚀**