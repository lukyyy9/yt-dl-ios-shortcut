# 📱 yt-dl-ios-shortcut

A lightweight server based on FastAPI and `yt-dlp` designed to work seamlessly with the iOS Shortcuts app. It allows you to download YouTube videos to your iPhone by simply sharing the video to a shortcut. The server handles the download process asynchronously, ensuring no timeouts. Videos are automatically cleaned up from the server once fetched by your iPhone, keeping your storage tidy.

## 🚀 Features

- **Fully Asynchronous:** Bypasses Apple's strict shortcut timeout limits. Trigger the download, close the shortcut, and let the server do the heavy lifting.
- **Quality Limiter:** Automatically downloads the best available quality capped at 1080p to save storage space.
- **Auto-Cleanup:** Video files are automatically deleted from your server as soon as they are successfully fetched by your iPhone.
- **Clean Naming Convention:** Videos are saved as `Video Title - Channel Name.mp4`.
- **Tailscale Friendly:** Designed to work from anywhere over 4G/5G without exposing any ports on your local router.

## 📖 Usage

1. **Find a Video:** Open the YouTube app (or any browser) on your iPhone and go to the video you want to download.
2. **Trigger the Download:** Tap the **Share** button and select the **"Request a download"** shortcut. The server starts downloading the video in the background.
3. **Fetch the Video:** Open the Shortcuts app and run the **"Get downloaded videos"** shortcut (or rely on the background iOS Automation if configured).
4. **Enjoy:** The video is safely moved to your iPhone's "YouTube" directory and automatically deleted from the server.

## 💻 Server Installation

The server is dockerized and optimized for easy deployment on **CasaOS**, Unraid, or any standard Docker environment.

### Option A: Docker CLI

Run the following command on your server:

```bash
docker run -d \
  --name yt-dl-ios-shortcut \
  -p 8007:8007 \
  imluky/yt-dl-ios-shortcut:latest
```

### Option B: CasaOS

1. Open CasaOS and click on the **App Store** icon.
2. Click on **Custom Install** (top right).
3. Fill in the fields:
   - **Docker Image:** `imluky/yt-dl-ios-shortcut:latest` (or your local build name)
   - **Title:** YT-DLP iOS Shortcut
   - **Port:** Host 8007 -> Container 8007
4. Click **Install**.

## 📱 iOS Setup

### Step 1: Prepare the iPhone file system

Before running the shortcuts, you need to create a text file to store the download tickets:

1. Download this empty [yt_queue.txt](https://raw.githubusercontent.com/imluky/yt-dl-ios-shortcut/main/yt_queue.txt) file and place it in the iCloud Drive → Shortcuts folder.
2. Open the **Files** app on your iPhone.
3. Navigate to **On My iPhone** main directory and create a new folder named `YouTube`.

### Step 2: Install the Shortcuts

Download and install the two required shortcuts directly to your iPhone using the links below:

- 📥 [Shortcut 1: Request a download](https://www.icloud.com/shortcuts/5d2badce5c0c4cb2a68d922e773a6818)
- 🔄 [Shortcut 2: Get downloaded videos](https://www.icloud.com/shortcuts/063ce79dd22a410d8c13bf8766a5f7ef)

### Step 3: Configure the IP Address

Once installed, open both shortcuts in the Shortcuts app to edit them:

1. Find the **"Get contents of URL"** actions.
2. Replace the TAILSCALE_IP placeholder with your actual server IP.

### Step 4: Set up the iOS Automation (Recommended)

To make the system truly seamless, set up your iPhone to fetch videos while you sleep or when you leave the house:

1. Open the **Shortcuts** app and go to the **Automation** tab.
2. Tap the **+** button to create a new **Personal Automation**.
3. Choose **Time of Day** (e.g., 2:00 AM) or **When I Leave** (to trigger when you leave home).
4. Select **Run Immediately** (and disable **"Notify When Run"** for a silent experience).
5. Tap **Next**, search for the **Get downloaded videos** shortcut, and select it.

You are all set! Share any YouTube video to the **"Request a download"** shortcut, and wake up to find it saved in your iPhone's "YouTube" directory.

## 🛠️ CI/CD

This repository includes a GitHub Actions pipeline. Every push to the main branch automatically triggers a new Docker build and pushes the updated image to Docker Hub.
