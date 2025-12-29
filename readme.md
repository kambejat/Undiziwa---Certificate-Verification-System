# Undiziwa – Fast Certificate Verification System

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3-green?logo=flask)](https://flask.palletsprojects.com/)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-3.3-blue?logo=tailwind-css)](https://tailwindcss.com/)
[![Chart.js](https://img.shields.io/badge/Chart.js-4-orange?logo=chart.js)](https://www.chartjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-lightgrey)](LICENSE)

**Undiziwa** is a secure, fast certificate verification system. Institutions verify certificates, users submit them for validation, and recruiters can fast-track verification for hiring or credential checks.

---

## 🔹 Features

* **Institution Verification:** Certificates are verified before being marked valid
* **User Submission:** Upload certificates for verification
* **Fast-track Verification:** Recruiters verify multiple certificates quickly
* **Secure Storage & Audit:** Verification activities logged for transparency
* **QR Code Support:** Verified certificates include unique QR codes
* **Analytics Dashboard:** Track verifications using interactive Chart.js charts

---

## 🛠 Tech Stack

* **Backend:** Flask
* **Frontend:** Tailwind CSS
* **Charts & Visualization:** Chart.js
* **Database:**  MySQL / SQLite
* **Authentication:** Flask-Login


---

## Demo

Try the live demo: [🔗 https://undiziwa-certificate-verification-system.onrender.com/login](#)  
*Insert screenshots or GIFs to showcase your system.*

Example dashboard screenshot:  
![Dashboard ](./screen_undiziwa/dashboard.png)
![Stats](./screen_undiziwa/stats.png)

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/undiziwa.git
cd undiziwa

# Install dependencies
pip install -r requirements.txt

# Create .env file
FLASK_APP=app.py
FLASK_ENV=development
DATABASE_URL=your_database_url

# Run the application
flask run
