# 🚀 Quick Deployment to Digital Ocean

## Step-by-Step Deployment Commands

### **Step 1: SSH into Your Digital Ocean Droplet**

```bash
ssh root@YOUR_DROPLET_IP
```

### **Step 2: Create Application Directory**

```bash
mkdir -p /root/text_extractor
cd /root/text_extractor
```

### **Step 3: Pull the Latest Docker Image**

```bash
docker pull abubakar486/text-extractor:latest
```

### **Step 4: Run the Application**

```bash
docker run -d \
  --name text-extractor-app \
  --restart unless-stopped \
  -p 8501:8501 \
  -p 8000:8000 \
  -v /root/text_extractor/output:/app/output \
  abubakar486/text-extractor:latest
```

### **Step 5: Check if Running**

```bash
docker ps
```

You should see the container running.

### **Step 6: View Logs**

```bash
docker logs -f text-extractor-app
```

Press `Ctrl+C` to exit logs.

### **Step 7: Access the Application**

Open your browser:
- **Streamlit App**: `http://YOUR_DROPLET_IP:8501`

---

## ✅ What's Included in This Version (v2.0.0)

- ✅ Support for MM/DD/YY date format (2-digit years)
- ✅ Fixed date validator (6 date formats supported)
- ✅ Fixed date filter (correct 2-digit year conversion)
- ✅ No transaction rejection based on amount
- ✅ Complete transaction descriptions
- ✅ Absolute values in amounts (no +/- signs)
- ✅ Production logging and error handling

---

## 🔧 Useful Commands

**View logs:**
```bash
docker logs -f text-extractor-app
```

**Restart container:**
```bash
docker restart text-extractor-app
```

**Stop container:**
```bash
docker stop text-extractor-app
```

**Update to latest version:**
```bash
docker stop text-extractor-app
docker rm text-extractor-app
docker pull abubakar486/text-extractor:latest
docker run -d --name text-extractor-app --restart unless-stopped -p 8501:8501 -p 8000:8000 -v /root/text_extractor/output:/app/output abubakar486/text-extractor:latest
```

---

## 🎯 Docker Image Info

- **Image**: `abubakar486/text-extractor:latest`
- **Version**: v2.0.0
- **Size**: ~1.5GB
- **Platform**: linux/amd64

---

## ✨ All Done!

Your application is now running with all the latest fixes! 🎉
