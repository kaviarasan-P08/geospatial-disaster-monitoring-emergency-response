import { initializeApp } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-app.js";
import { getMessaging, getToken, onMessage } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-messaging.js";

const firebaseConfig = {
  apiKey: "AIzaSyCQzqDPhshzzCA0RhER-x8llnuBi-IZ7eQ",
  authDomain: "disaster-alert-dashboard-b8d9a.firebaseapp.com",
  projectId: "disaster-alert-dashboard-b8d9a",
  storageBucket: "disaster-alert-dashboard-b8d9a.appspot.com",
  messagingSenderId: "752799548733",
  appId: "1:752799548733:web:279754e0b4fb9015eb3154"
};

const app = initializeApp(firebaseConfig);
const messaging = getMessaging(app);

async function requestPermissionAndSaveToken() {
  try {
    const permission = await Notification.requestPermission();
    if (permission !== "granted") {
      console.warn("❌ Notification permission not granted.");
      return;
    }

    const token = await getToken(messaging, {
      vapidKey: "BLjb5M-5xdXwQPhXAmV_teix0OekN71bDzEkFx20mLHb3PUcX1m1KQF08sJhgqFK37iI9XJ02fVQ8gmw0HZq3Hc"
    });

    if (token) {
      console.log("🔐 FCM Token:", token);
      // Try to get user's current location
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(async (pos) => {
          const lat = pos.coords.latitude;
          const lon = pos.coords.longitude;
          await fetch("/save_token", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ token, lat, lon })
          });
        }, async (err) => {
          // If location not allowed, still save token but with null location
          await fetch("/save_token", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ token, lat: null, lon: null })
          });
        });
      } else {
        // Geolocation not supported
        await fetch("/save_token", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token, lat: null, lon: null })
        });
      }
    } else {
      console.warn("⚠️ No FCM token retrieved.");
    }
  } catch (err) {
    console.error("❌ Error getting token:", err);
  }
}

onMessage(messaging, (payload) => {
  console.log("📩 Foreground Notification:", payload);
  const { title, body } = payload.notification;
  alert(`🔔 ${title}\n${body}`);
});

requestPermissionAndSaveToken();
