from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import requests
import json
import time
import os
import hashlib
from functools import wraps
from flask import send_from_directory
from google.oauth2 import service_account
import google.auth.transport.requests
import math

# Optional Twilio import - guarded so app still runs if twilio not installed
try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except Exception:
    TWILIO_AVAILABLE = False

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Change this in production!

REPORT_FILE = "reports.json"
FCM_TOKEN_FILE = "fcm_tokens.json"
USER_LOC_FILE = "user_locations.json"
FIREBASE_PROJECT_ID = "disaster-alert-dashboard-b8d9a"
SERVICE_ACCOUNT_FILE = "firebase-key.json"
USERS_FILE = "users.json"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = hashlib.sha256("admin123".encode()).hexdigest()  # Change admin password!

# Twilio configuration (set these as env vars in real deployment)
TWILIO_SID = os.getenv("TWILIO_SID", "")
TWILIO_AUTH = os.getenv("TWILIO_AUTH", "")
TWILIO_PHONE = os.getenv("TWILIO_PHONE", "")  # e.g. "+1234567890"
SMS_ENABLED = bool(TWILIO_SID and TWILIO_AUTH and TWILIO_PHONE and TWILIO_AVAILABLE)

# NASA cache
cached_nasa_data = None
nasa_last_fetched = 0

# Utility functions
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session or session.get("user") != ADMIN_USERNAME:
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated_function

# Google FCM token and notification functions
def get_access_token():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/firebase.messaging"]
    )
    request = google.auth.transport.requests.Request()
    credentials.refresh(request)
    return credentials.token

# Haversine formula to calculate distance between two lat/lon points in km
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    dphi = math.radians(float(lat2) - float(lat1))
    dlambda = math.radians(float(lon2) - float(lon1))
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def send_sms_alert(to_phone, message):
    """
    Send SMS via Twilio if configured. If Twilio is not available or not configured,
    fall back to printing to console (demo mode).
    """
    try:
        if SMS_ENABLED:
            client = TwilioClient(TWILIO_SID, TWILIO_AUTH)
            client.messages.create(body=message, from_=TWILIO_PHONE, to=to_phone)
            print(f"📱 SMS sent to {to_phone}")
        else:
            # Demo fallback (safe for presentation): print to server log
            print(f"[SMS DEMO] To: {to_phone} | Message: {message}")
    except Exception as e:
        print("❌ SMS send error:", e)

# Send notification only to users within radius_km of incident (default 50km)
def send_fcm_notification(title, body, incident_lat=None, incident_lon=None, radius_km=50):
    try:
        if not os.path.exists(FCM_TOKEN_FILE):
            print("⚠️ No token file found")
            return
        if not os.path.exists(USER_LOC_FILE):
            print("⚠️ No user locations file found")
            return

        with open(FCM_TOKEN_FILE, "r") as f:
            tokens_data = [line.strip() for line in f if line.strip()]

        with open(USER_LOC_FILE, "r") as f:
            user_locations = json.load(f)

        # Build list of tokens for nearby users
        notify_tokens = []
        notify_phones = []  # for SMS
        for entry in tokens_data:
            # Expected token format: username:token
            if ":" not in entry:
                continue
            username, token = entry.split(":", 1)
            loc = user_locations.get(username)
            if not loc or incident_lat is None or incident_lon is None:
                continue
            user_lat = loc.get("lat")
            user_lon = loc.get("lon")
            if user_lat is None or user_lon is None:
                continue
            try:
                dist = haversine(incident_lat, incident_lon, user_lat, user_lon)
            except Exception:
                continue
            if dist <= radius_km:
                notify_tokens.append(token)
                # get phone from users.json if present
                users = load_users()
                u = users.get(username, {})
                phone = u.get("phone")
                if phone:
                    notify_phones.append(phone)

        if not notify_tokens and not notify_phones:
            print("ℹ️ No nearby users to notify.")
            return

        access_token = get_access_token()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; UTF-8"
        }

        # Send FCM notifications
        for token in notify_tokens:
            message = {
                "message": {
                    "token": token,
                    "notification": {
                        "title": title,
                        "body": body
                    }
                }
            }
            try:
                response = requests.post(
                    f"https://fcm.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/messages:send",
                    headers=headers,
                    json=message
                )
                print(f"📤 Notification to {token[:20]}... — Status: {response.status_code}")
            except Exception as e:
                print("FCM send error:", e)

        # Send SMS alerts to nearby phones (Twilio or demo)
        sms_message = f"{title}\n{body}"
        for phone in set(notify_phones):
            send_sms_alert(phone, sms_message)

    except Exception as e:
        print("❌ Notification Error:", str(e))

# Routes for user authentication
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        data = request.form
        # Be defensive: data.get may return None
        username_raw = data.get("username")
        password = data.get("password")
        username = (username_raw or "").strip()
        if not username or not password:
            return render_template("signup.html", error="Username and password required.")
        # Prevent registering reserved admin username
        if username == ADMIN_USERNAME:
            return render_template("signup.html", error="This username is reserved.")
        users = load_users()
        if username in users:
            return render_template("signup.html", error="Username already exists.")
        users[username] = {
            "password_hash": hash_password(password),
            # New users start with 0 stars and not blocked. Admin must approve first report.
            "stars": 0,
            "blocked": False,
            # Number of approved reports the user has
            "report_count": 0,
            # optional phone (can be set later via profile or save_token)
            "phone": None
        }
        save_users(users)
        # Auto-login new user so they can immediately submit their first report
        session["user"] = username
        return redirect(url_for("dashboard"))
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = request.form
        username = (data.get("username") or "").strip()
        password = data.get("password")
        users = load_users()
        user = users.get(username)
        if user and user["password_hash"] == hash_password(password):
            # Prevent blocked users from logging in
            if user.get("blocked"):
                return render_template("login.html", error="Account blocked. Contact admin.")
            session["user"] = username
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid username or password")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        data = request.form
        username = (data.get("username") or "").strip()
        password = data.get("password")
        if username == ADMIN_USERNAME and hash_password(password) == ADMIN_PASSWORD_HASH:
            session["user"] = ADMIN_USERNAME
            return redirect(url_for("admin_dashboard"))
        else:
            return render_template("admin_login.html", error="Invalid admin credentials")
    return render_template("admin_login.html")

@app.route("/admin-logout")
def admin_logout():
    session.pop("user", None)
    return redirect(url_for("admin_login"))

# Main pages
@app.route("/")
def index():
    if "user" in session:
        return redirect(url_for("dashboard"))
    else:
        return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    users = load_users()
    user_obj = users.get(session["user"], {})
    user_stars = user_obj.get("stars", 0)
    user_report_count = user_obj.get("report_count", 0)
    blocked = user_obj.get("blocked", False)
    # allow submit if not blocked and either already has stars or it's their first report
    can_submit = (not blocked) and (user_stars > 0 or user_report_count == 0)

    # check if the current user has a pending report
    has_pending_report = False
    if os.path.exists(REPORT_FILE):
        with open(REPORT_FILE, 'r') as f:
            try:
                reports = json.load(f)
            except Exception:
                reports = []
        has_pending_report = any(r.get('username') == session["user"] and r.get('status') == 'pending' for r in reports)

    return render_template("dashboard.html", username=session["user"], stars=user_stars, can_submit=can_submit, has_pending_report=has_pending_report)

@app.route("/admin-dashboard")
@admin_required
def admin_dashboard():
    reports = []
    if os.path.exists(REPORT_FILE):
        with open(REPORT_FILE, "r") as f:
            try:
                reports = json.load(f)
            except json.JSONDecodeError:
                reports = []
    users = load_users()
    # Separate pending reports for admin action
    pending = [r for r in reports if r.get('status') == 'pending']
    approved = [r for r in reports if r.get('status') == 'approved']
    declined = [r for r in reports if r.get('status') == 'declined']
    return render_template("admin_dashboard.html", reports=reports, users=users, pending=pending, approved=approved, declined=declined)


@app.route('/admin/approve_report/<int:report_id>', methods=['POST'])
@admin_required
def admin_approve_report(report_id):
    if not os.path.exists(REPORT_FILE):
        return jsonify({'status': 'error', 'message': 'No reports file'})
    with open(REPORT_FILE, 'r') as f:
        reports = json.load(f)
    found = False
    for r in reports:
        if r.get('id') == report_id:
            r['status'] = 'approved'
            # Update user's approved report count and give stars on first approved
            users = load_users()
            u = users.get(r.get('username'))
            if u:
                u['report_count'] = u.get('report_count', 0) + 1
                if u['report_count'] == 1:
                    u['stars'] = 5
                u['blocked'] = False
                save_users(users)
            # Notify nearby users about approved incident (FCM + SMS)
            send_fcm_notification(
                f"New {r.get('type')} Report",
                r.get('description'),
                incident_lat=r.get('lat'),
                incident_lon=r.get('lon')
            )
            found = True
            break
    if found:
        with open(REPORT_FILE, 'w') as f:
            json.dump(reports, f, indent=2)
        return jsonify({'status': 'success', 'message': 'Report approved'})
    return jsonify({'status': 'error', 'message': 'Report not found'})


@app.route('/admin/decline_report/<int:report_id>', methods=['POST'])
@admin_required
def admin_decline_report(report_id):
    if not os.path.exists(REPORT_FILE):
        return jsonify({'status': 'error', 'message': 'No reports file'})
    with open(REPORT_FILE, 'r') as f:
        reports = json.load(f)
    for r in reports:
        if r.get('id') == report_id:
            r['status'] = 'declined'
            # Block the user so they cannot submit further reports
            users = load_users()
            u = users.get(r.get('username'))
            if u:
                u['blocked'] = True
                save_users(users)
            with open(REPORT_FILE, 'w') as f:
                json.dump(reports, f, indent=2)
            return jsonify({'status': 'success', 'message': 'Report declined and user blocked'})
    return jsonify({'status': 'error', 'message': 'Report not found'})

# External APIs cached & fetched
@app.route('/nasa-data')
def nasa_data():
    global cached_nasa_data, nasa_last_fetched
    if time.time() - nasa_last_fetched < 900 and cached_nasa_data:
        return jsonify(cached_nasa_data)

    url = "https://eonet.gsfc.nasa.gov/api/v3/events"
    response = requests.get(url)
    if response.status_code == 200:
        cached_nasa_data = response.json()
        nasa_last_fetched = time.time()
        return jsonify(cached_nasa_data)
    else:
        return jsonify({"error": "NASA API error"})

@app.route('/earthquake-data')
def earthquake_data():
    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
    response = requests.get(url)
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({"error": "USGS API error"})

# Firebase messaging token save (now stores username and location and optional phone)
@app.route('/save_token', methods=['POST'])
def save_token():
    try:
        data = request.get_json()
        token = data.get("token")
        lat = data.get("lat")
        lon = data.get("lon")
        phone = data.get("phone")  # optional phone number
        username = session.get("user")
        if not token or username is None or lat is None or lon is None:
            return jsonify({"status": "error", "message": "Token, username, and location required"})
        # Save token as username:token
        tokens = set()
        if os.path.exists(FCM_TOKEN_FILE):
            with open(FCM_TOKEN_FILE, "r") as f:
                tokens = set(line.strip() for line in f if line.strip())
        token_entry = f"{username}:{token}"
        if token_entry in tokens:
            # still update location/phone if provided
            user_locations = {}
            if os.path.exists(USER_LOC_FILE):
                with open(USER_LOC_FILE, "r") as f:
                    user_locations = json.load(f)
            user_locations[username] = {"lat": lat, "lon": lon}
            with open(USER_LOC_FILE, "w") as f:
                json.dump(user_locations, f, indent=2)
            if phone:
                users = load_users()
                if username in users:
                    users[username]['phone'] = phone
                    save_users(users)
            return jsonify({"status": "success", "message": "Token already saved."})
        tokens.add(token_entry)
        with open(FCM_TOKEN_FILE, "w") as f:
            for t in tokens:
                f.write(t + "\n")
        # Save user location
        user_locations = {}
        if os.path.exists(USER_LOC_FILE):
            with open(USER_LOC_FILE, "r") as f:
                user_locations = json.load(f)
        user_locations[username] = {"lat": lat, "lon": lon}
        with open(USER_LOC_FILE, "w") as f:
            json.dump(user_locations, f, indent=2)
        # Save phone if provided
        if phone:
            users = load_users()
            if username in users:
                users[username]['phone'] = phone
                save_users(users)
        return jsonify({"status": "success", "message": "Token and location saved"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# Submit report linked to user
@app.route('/submit-report', methods=['POST'])
@login_required
def submit_report():
    try:
        # Prevent blocked users from submitting reports
        username = session.get("user")
        users = load_users()
        if users.get(username, {}).get('blocked'):
            return jsonify({"status": "error", "message": "User blocked. Cannot submit reports."})

        report = request.get_json()
        report['timestamp'] = time.strftime("%Y-%m-%d %H:%M:%S")
        report['username'] = username
        # unique id for report
        report['id'] = int(time.time() * 1000)
        # Ensure keys consistent with frontend
        report['lat'] = report.pop('latitude', report.get('lat', None))
        report['lon'] = report.pop('longitude', report.get('lon', None))

        if not os.path.exists(REPORT_FILE):
            with open(REPORT_FILE, "w") as f:
                json.dump([], f)

        with open(REPORT_FILE, "r") as f:
            try:
                reports = json.load(f)
            except json.JSONDecodeError:
                reports = []

        # Determine if this is the user's first report
        user_reports_for_user = [r for r in reports if r.get('username') == username]
        if not user_reports_for_user:
            # First report -> require admin approval
            report['status'] = 'pending'
        else:
            # Subsequent reports are auto-marked approved
            report['status'] = 'approved'

        reports.append(report)
        with open(REPORT_FILE, "w") as f:
            json.dump(reports, f, indent=2)

        # If report is auto-approved, increment user's approved report_count and notify nearby users
        if report.get('status') == 'approved':
            users = load_users()
            u = users.get(username)
            if u is not None:
                u['report_count'] = u.get('report_count', 0) + 1
                # If this is their first approved report, grant 5 stars and ensure not blocked
                if u.get('report_count', 0) == 1:
                    u['stars'] = 5
                    u['blocked'] = False
                save_users(users)

            send_fcm_notification(
                f"New {report.get('type')} Report", report.get('description'),
                incident_lat=report.get('lat'), incident_lon=report.get('lon')
            )

        return jsonify({"status": "success", "message": "Report submitted."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# Return all user reports
@app.route('/user-reports')
def user_reports():
    try:
        if not os.path.exists(REPORT_FILE):
            return jsonify([])
        with open(REPORT_FILE, 'r') as f:
            reports = json.load(f)
        # Only return approved reports to the public/user dashboard
        approved = [r for r in reports if r.get('status') == 'approved']
        return jsonify(approved)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# Admin reduces star rating of user
@app.route("/decrement-star/<username>", methods=["POST"])
@admin_required
def decrement_star(username):
    users = load_users()
    if username not in users or username == ADMIN_USERNAME:
        return jsonify({"status": "error", "message": "User not found or invalid"})
    # Only decrement if user has at least one star
    if users[username]["stars"] > 0:
        users[username]["stars"] -= 1

        # If stars drop to zero, block the user and remove their approved reports
        removed_reports = 0
        if users[username]["stars"] == 0:
            users[username]["blocked"] = True
            # Remove approved reports by this user from the reports file (dashboard)
            if os.path.exists(REPORT_FILE):
                try:
                    with open(REPORT_FILE, 'r') as f:
                        try:
                            reports = json.load(f)
                        except Exception:
                            reports = []
                    # Keep reports that are NOT approved by this username
                    new_reports = [r for r in reports if not (r.get('username') == username and r.get('status') == 'approved')]
                    removed_reports = len(reports) - len(new_reports)
                    if removed_reports > 0:
                        with open(REPORT_FILE, 'w') as f:
                            json.dump(new_reports, f, indent=2)
                except Exception as e:
                    # If report file can't be processed, still continue with blocking
                    print(f"⚠️ Warning removing reports for {username}: {e}")

        save_users(users)

        msg = f"{username} star rating decremented"
        if users[username]["stars"] == 0:
            msg += ". User has zero stars, has been blocked"
            if removed_reports:
                msg += f" and {removed_reports} approved report(s) removed from dashboard"

        return jsonify({
            "status": "success",
            "message": msg,
            "removed_reports": removed_reports,
            "new_stars": users[username]["stars"]
        })
    else:
        return jsonify({"status": "error", "message": "User has zero stars already"})

@app.route('/firebase-messaging-sw.js')
def service_worker():
    return send_from_directory('.', 'firebase-messaging-sw.js')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)
