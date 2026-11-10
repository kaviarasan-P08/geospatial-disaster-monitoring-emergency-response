# Geospatial Disaster Monitoring and Emergency Response System

An integrated GIS-based disaster monitoring and emergency response platform that combines real-time environmental data, spatial visualisation, location intelligence and emergency communication to support disaster awareness and community-level response.

## 1. Project Overview

Natural disasters such as floods, earthquakes, wildfires and other environmental hazards can have significant impacts on communities. Access to timely geographical information and location-specific alerts is essential for understanding disaster events and supporting emergency response.

This project develops a web-based **Geospatial Disaster Monitoring and Emergency Response System** that integrates external disaster data sources with interactive mapping, community-based incident reporting and location-based emergency notifications.

The platform uses geospatial technologies to visualise disaster events, identify affected locations, collect user-submitted reports and facilitate communication with users in potentially affected areas.

## 2. Project Objectives

- Integrate external environmental and disaster-related data through public APIs.
- Visualise geographical disaster events using interactive web mapping.
- Enable community members to submit location-based incident reports.
- Support spatial proximity analysis for identifying users within a specified distance of reported events.
- Provide location-specific emergency notifications through push notifications and SMS.
- Develop a centralised dashboard for monitoring and managing incident reports.

## 3. Key GIS and Spatial Capabilities

### 3.1 Geospatial Data Integration

- **NASA EONET API:** Integrated to retrieve natural hazard and environmental event information, supporting the monitoring of events such as wildfires, floods and other natural phenomena.
- **USGS Earthquake API:** Connected to retrieve earthquake-related information and geographical coordinates.
- Processes geographical coordinates to represent disaster events and reported incidents spatially.

### 3.2 Interactive Spatial Visualisation

- Developed an interactive web-based mapping interface using **Leaflet.js**.
- Displays geographical disaster events through map markers.
- Supports visual exploration of incident locations and environmental events.
- Combines information from multiple external data sources within a single spatial interface.

### 3.3 Location Intelligence and Proximity Analysis

- Implemented the **Haversine formula** to calculate geographical distances between disaster locations and registered users.
- Identifies users within a configurable geographical radius of an incident.
- Supports location-based alert distribution using proximity calculations.
- Stores and processes user location coordinates for targeted emergency communication.

### 3.4 Community-Based Incident Reporting

- Developed a user reporting mechanism for submitting disaster-related incidents.
- Captures incident categories, descriptions, geographical coordinates and timestamps.
- Implements an administrative review process for submitted reports.
- Includes report approval and rejection functionality.
- Incorporates a user trust and rating mechanism to support report credibility.

### 3.5 Emergency Communication and Notification

- **Firebase Cloud Messaging (FCM):** Integrated for delivering push notifications to registered users.
- **Twilio SMS API:** Implemented as an additional SMS communication mechanism.
- Supports proximity-based notification logic to identify users potentially affected by reported incidents.
- Combines geospatial information with communication services to support emergency awareness.

## 4. Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python, JavaScript |
| Backend Framework | Flask |
| Frontend | HTML, CSS, JavaScript |
| Web GIS | Leaflet.js |
| Geospatial Analysis | Haversine Distance Calculation |
| Environmental Data | NASA EONET API |
| Earthquake Data | USGS Earthquake API |
| Push Notifications | Firebase Cloud Messaging |
| SMS Communication | Twilio API |
| Data Storage | JSON-based storage |
| Development Environment | Visual Studio Code, Python |

## 5. System Architecture

The platform follows an integrated architecture connecting external geographical data sources, a Flask-based backend, an interactive mapping interface and emergency communication services.

**System Workflow:**

1. **External Data Collection:** Retrieve disaster and environmental event information from NASA EONET and USGS APIs.
2. **Backend Processing:** Flask handles API requests, application logic, user submissions and incident management.
3. **Spatial Visualisation:** Leaflet.js displays geographical events and incident locations on an interactive map.
4. **Community Reporting:** Users submit incident information with geographical coordinates.
5. **Proximity Analysis:** The Haversine formula calculates distances between incidents and registered users.
6. **Emergency Notifications:** Firebase Cloud Messaging and Twilio support location-based communication.
7. **Administrative Monitoring:** Administrators review, approve or reject submitted incident reports.

## 6. Project Structure

```text
geospatial-disaster-monitoring/
│
├── app.py
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── templates/
│   ├── index.html
│   ├── login.html
│   └── admin.html
│
├── requirements.txt
├── package.json
├── package-lock.json
├── .gitignore
├── .env.example
└── README.md
```

*Note: The directory structure may be updated as the application evolves.*

## 7. Installation and Setup

### Prerequisites

- Python 3.9 or later
- Node.js and npm
- Git
- Firebase project and service account configuration
- Twilio account for SMS functionality

### Step 1: Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/geospatial-disaster-monitoring.git
```

### Step 2: Navigate to the Project Directory

```bash
cd geospatial-disaster-monitoring
```

### Step 3: Create a Virtual Environment

```bash
python -m venv venv
```

Activate the environment:

**macOS / Linux**

```bash
source venv/bin/activate
```

**Windows**

```bash
venv\Scripts\activate
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

If the frontend has Node.js dependencies:

```bash
npm install
```

### Step 5: Configure Environment Variables

Create a `.env` file using `.env.example` and provide the required configuration values.

```env
FLASK_SECRET_KEY=your_secret_key
TWILIO_SID=your_twilio_account_sid
TWILIO_AUTH=your_twilio_auth_token
TWILIO_PHONE=your_twilio_phone_number
```

Configure Firebase Admin SDK credentials separately using a securely stored service account file.

**Important:** Never commit API credentials, service account keys, authentication tokens or private user information to GitHub.

### Step 6: Run the Application

```bash
python app.py
```

Open the local application in your browser using the Flask development server address displayed in the terminal.

## 8. Data Sources and External Integrations

| Data Source / Service | Purpose |
|---|---|
| NASA EONET | Natural hazard and environmental event information |
| USGS Earthquake API | Earthquake-related geographical information |
| Firebase Cloud Messaging | Push notification delivery |
| Twilio | SMS-based emergency communication |
| Leaflet.js | Interactive geographical visualisation |

## 9. Potential Applications

- Geographical monitoring of natural disaster events.
- Spatial visualisation of environmental hazards.
- Community-based disaster reporting.
- Location-specific emergency awareness.
- Proximity-based notification systems.
- Geospatial decision support for disaster response.

## 10. Future Enhancements

- Integration of additional geospatial datasets and environmental monitoring services.
- Advanced spatial analysis for identifying potentially vulnerable locations.
- Integration of flood-risk and hazard-susceptibility datasets.
- Development of a more scalable spatial database using PostgreSQL and PostGIS.
- Enhanced geospatial dashboards and analytical visualisations.
- Deployment of the application on a cloud infrastructure.

## 11. Project Status

**Development Status:** Ongoing

The project demonstrates the integration of GIS technologies, external geospatial data services, spatial proximity calculations, interactive mapping and emergency communication within a unified web-based application.

## 12. Author

**Kaviarasan P**

MSc Urban Data Analytics  
University College Dublin (UCD), Ireland

**Areas of Interest:** Geographic Information Systems (GIS), Spatial Data Analytics, Geospatial Technologies, Urban Analytics and Location Intelligence.

---

*Developed as a geospatial technology project exploring the integration of spatial data, interactive mapping and location-based emergency response.*
