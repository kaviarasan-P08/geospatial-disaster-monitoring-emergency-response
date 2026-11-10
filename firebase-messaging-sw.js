// firebase-messaging-sw.js
importScripts("https://www.gstatic.com/firebasejs/10.12.1/firebase-app-compat.js");
importScripts("https://www.gstatic.com/firebasejs/10.12.1/firebase-messaging-compat.js");

firebase.initializeApp({
  apiKey: "AIzaSyCQzqDPhshzzCA0RhER-x8llnuBi-IZ7eQ",
  authDomain: "disaster-alert-dashboard-b8d9a.firebaseapp.com",
  projectId: "disaster-alert-dashboard-b8d9a",
  storageBucket: "disaster-alert-dashboard-b8d9a.appspot.com",
  messagingSenderId: "752799548733",
  appId: "1:752799548733:web:279754e0b4fb9015eb3154"
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage(payload => {
  console.log("📩 Background Notification:", payload);
  const { title, body } = payload.notification;
  self.registration.showNotification(title, {
    body,
    icon: "/icon.png"
  });
});
