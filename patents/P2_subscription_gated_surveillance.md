# Provisional Patent Application

**Title:** Subscription-Gated Autonomous Surveillance System with Automatic Feature Deactivation

**Inventor:** Spevino LLC

---

## 1. Field of the Invention
The present invention relates to computer vision surveillance systems, and more particularly to a method and system for autonomously managing software feature access and operational states based on a cryptographically verified subscription status at the edge or on-premise.

## 2. Background of the Invention
Modern computer vision (CV) surveillance systems for retail loss prevention utilize high-value artificial intelligence models to detect complex behaviors like shoplifting, restricted area breaches, and cash register theft. Developing and maintaining these models requires significant investment. Traditional "software as a service" (SaaS) models often rely on a persistent cloud connection to validate licenses. However, surveillance systems frequently operate in environments with intermittent connectivity or where security requirements mandate on-premise autonomy.

A significant problem in the industry is "unpaid usage," where software continues to provide high-value detection and alerting services after a subscription has lapsed or been cancelled. This represents a loss of revenue and unauthorized access to proprietary intellectual property. There is a need for a system that can autonomously detect its licensing state and automatically deactivate or "pause" core high-performance functionality without requiring an external "kill signal," while still maintaining basic dashboard access for historical data review.

## 3. Summary of the Invention
The present invention provides a "Loss Prevention Operating System" (LP-OS) that integrates a behavioral detection pipeline with an autonomous licensing engine. The system periodically validates a locally stored, cryptographically-signed license key. 

Key features include:
1.  **Autonomous State Management:** The system moves between 'Active', 'Grace Period', and 'Disabled' states based on the expiration date embedded in the signed license.
2.  **Automatic Feature Deactivation:** Upon transition to an 'Expired' or 'Disabled' state, the system automatically pauses computer vision inference (detection) and alert dispatching (SMS/Push notifications) while leaving the management UI accessible.
3.  **Tiered Resource Gating:** The system enforces hardware limits (number of locations and cameras) and software limits (types of AI detections) dynamically based on the verified tier.
4.  **Cryptographic Integrity:** Subscription data is protected using HMAC-SHA256 signatures to prevent tampering with expiry dates or feature sets.

## 4. Detailed Description

### 4.1 License Key Architecture
The system utilizes a secure license format: `spevino-[BASE64_DATA]-[HMAC_SIGNATURE]`. 
The `BASE64_DATA` contains a JSON object with the following fields:
*   `customer`: Identifier for the license holder.
*   `tier`: The authorized subscription level.
*   `max_stores`: Maximum number of authorized physical locations.
*   `max_cameras`: Maximum number of authorized video streams per location.
*   `expiry`: ISO 8601 timestamp for subscription termination.
*   `features`: A list of authorized detection algorithms (e.g., `sms_alerts`, `restricted_area_detection`).

The `HMAC_SIGNATURE` is a 16-character SHA-256 hash generated using a server-side secret, ensuring the system can verify the key's authenticity without needing to contact a licensing server on every boot.

### 4.2 The 6-Tier Subscription Model
The invention implements a structured capability ladder designed for different retail scales:
1.  **SOLO Tier:** Designed for single locations with up to 4 cameras. Includes basic concealment and trajectory detection.
2.  **PRO Tier:** Designed for single locations with up to 12 cameras. Adds SMS alerts and restricted area breach detection.
3.  **GROWTH Tier:** Designed for multi-location SMBs (up to 3 locations, 30 cameras). Adds cash register theft detection and API access.
4.  **BUSINESS Tier:** Scaled for 5 locations and 60 cameras. Adds advanced AI analytics and custom detection zones.
5.  **ENTERPRISE Tier:** Designed for large chains (20 locations, 200 cameras). Adds custom integrations and Service Level Agreements (SLA).
6.  **GLOBAL Tier:** Unlimited scaling for international chains. Includes white-labeling and global data center support.

### 4.3 Feature Gating & Resource Enforcement
The system includes a gating module (`gating.py`) that acts as a middleware for all operational requests.
*   **Location/Camera Limits:** When a user attempts to add a store or camera, the system queries the current count. If `current_count >= tier_limit`, the system rejects the request with a `403 Forbidden` error (e.g., "Maximum number of stores reached for your tier").
*   **Detection Type Gating:** Before the CV engine processes a frame for a specific event type (e.g., `register_theft_detection`), the gating module verifies if that feature string exists in the authorized `features` list for the tier. If not, detection is skipped.

### 4.4 Expiry & Grace Period Mechanism
The system maintains an `installed_at` timestamp. 
*   **14-Day Free Trial:** On fresh installations without a key, the system defaults to a `GRACE` state for 14 days, providing full functionality of the base tier to allow for evaluation.
*   **Deactivation Logic:** Upon reaching the `expiry` date (plus any configured grace period), the `license_manager.can_detect` and `license_manager.can_alert` properties return `False`.
*   **Interlock:** The `/events` ingestion endpoint and the `process_alerts` background task check these properties. If `False`, the system returns a `402 Payment Required` error to the CV module and suppresses all SMS notifications.

## 5. Claims
1. A computer vision surveillance system comprising a video ingestion module, an inference engine, and a licensing controller, wherein the licensing controller autonomously modifies the operational state of the inference engine based on a locally validated cryptographic license.
2. The system of Claim 1, wherein the operational state includes a "Paused" state where video frames are received but behavioral detection algorithms are not executed.
3. The system of Claim 1, wherein the licensing controller validates the license using an HMAC-SHA256 signature to prevent local modification of expiration dates.
4. A method for tiered feature gating in a surveillance system, comprising:
    - Identifying a subscription tier from a signed payload;
    - Mapping said tier to a set of authorized detection types including concealment detection, restricted area detection, and cash register theft detection;
    - Dynamically enabling or disabling specific algorithms in the CV pipeline based on said mapping.
5. The system of Claim 1, where the licensing controller enforces a physical location limit by returning a 403 Forbidden response when a user attempts to provision resources beyond the count authorized by the subscription tier.
6. The system of Claim 1, where the licensing controller enforces a per-location camera limit by rejecting new camera registrations when the authorized threshold is reached.
7. A method for autonomous deactivation of surveillance alerting, wherein the system suppresses SMS and Push notifications immediately upon detection of an expired subscription status, regardless of detection confidence.
8. The system of Claim 1, further comprising a 14-day autonomous grace period state that allows full system functionality prior to the first license activation.
9. A method for providing a multi-tier surveillance SaaS, comprising 6 tiers (Solo, Pro, Growth, Business, Enterprise, Global) where advanced AI features like "Cash Register Theft" are reserved for mid-to-high level tiers while "Concealment Detection" is provided at the base level.
10. The system of Claim 1, wherein the system provides a "Limited Access" management dashboard allowing review of historical events while simultaneously blocking the creation of new real-time detection events.
11. The use of a Base64-encoded JSON payload as an offline-validatable license key to gate high-performance computer vision features at the edge.
