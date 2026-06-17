# 🛡️ DAST Security Report

**Tool:** OWASP ZAP v2.17.0
**Target Site:** `http://127.0.0.1:5000`
**Generated:** Wed, 17 Jun 2026 02:44:30

---

## 📊 Summary of Alerts

| Risk Level           | Alerts |
| :------------------- | :----: |
| 🔴 **High**          |   0    |
| 🟠 **Medium**        |   3    |
| 🟡 **Low**           |   3    |
| 🔵 **Informational** |   7    |
| 🟢 False Positives   |   0    |

---

## 📈 Site Insights

| Metric                                | Value |
| :------------------------------------ | :---: |
| Total endpoints                       |  14   |
| Responses 2xx                         |  78%  |
| Responses 4xx                         |  21%  |
| Endpoints — `GET`                     |  85%  |
| Endpoints — `POST`                    |  14%  |
| Content type `text/html`              |  71%  |
| Content type `application/javascript` |  14%  |
| Content type `text/css`               |  14%  |
| ZAP errors logged                     |   3   |
| ZAP warnings logged                   |  10   |

---

## 🟠 Medium Risk Findings

### 1. CSP: `style-src unsafe-inline` — _Systemic_

- **CWE:** [693](https://cwe.mitre.org/data/definitions/693.html) · **Plugin:** [10055](https://www.zaproxy.org/docs/alerts/10055/)
- **Issue:** Your CSP `style-src` includes `'unsafe-inline'`, weakening XSS protection.
- **Affected:** `/`, `/help.html`, `/login.html`, `/signup.html`
- **Fix:** Remove `'unsafe-inline'` from `style-src`; use hashes or nonces for inline styles.

### 2. Content Security Policy (CSP) Header Not Set — _2 instances_

- **CWE:** [693](https://cwe.mitre.org/data/definitions/693.html) · **Plugin:** [10038](https://www.zaproxy.org/docs/alerts/10038/)
- **Issue:** No CSP header on some responses.
- **Affected:** `/robots.txt`, `/login.html` (POST)
- **Fix:** Ensure the CSP header is applied to **all** responses, including static files and POST handlers.

### 3. Missing Anti-clickjacking Header — _5 instances_

- **CWE:** [1021](https://cwe.mitre.org/data/definitions/1021.html) · **Plugin:** [10020](https://www.zaproxy.org/docs/alerts/10020/)
- **Issue:** No `X-Frame-Options` or CSP `frame-ancestors`.
- **Affected:** `/help.html`, `/login.html`, `/privacy.html`, `/signup.html`
- **Fix:** Set `X-Frame-Options: DENY` or add `frame-ancestors 'none'` to CSP.

---

## 🟡 Low Risk Findings

### 1. CSP: Notices — _2 instances_

- **Plugin:** [10055](https://www.zaproxy.org/docs/alerts/10055/)
- **Issue:** `report-uri` directive is deprecated.
- **Fix:** Migrate to the `report-to` directive.

### 2. Server Leaks Version Info via `Server` Header — _Systemic_

- **CWE:** [497](https://cwe.mitre.org/data/definitions/497.html) · **Plugin:** [10036](https://www.zaproxy.org/docs/alerts/10036/)
- **Evidence:** `Werkzeug/3.1.8 Python/3.11.4`
- **Fix:** Suppress/override the `Server` header (use a production WSGI server like gunicorn behind a reverse proxy).

### 3. X-Content-Type-Options Header Missing — _Systemic_

- **CWE:** [693](https://cwe.mitre.org/data/definitions/693.html) · **Plugin:** [10021](https://www.zaproxy.org/docs/alerts/10021/)
- **Fix:** Set `X-Content-Type-Options: nosniff` on all responses.

---

## 🔵 Informational Findings

| Finding                                                                     | Instances |                       Plugin                        |
| :-------------------------------------------------------------------------- | :-------: | :-------------------------------------------------: |
| Authentication Request Identified                                           |     1     | [10111](https://www.zaproxy.org/docs/alerts/10111/) |
| CSP: Header & Meta (evaluated separately)                                   |     2     | [10055](https://www.zaproxy.org/docs/alerts/10055/) |
| GET for POST (`/signup.html` accepts GET)                                   |     1     | [10058](https://www.zaproxy.org/docs/alerts/10058/) |
| Information Disclosure — Suspicious Comments (in `bootstrap.bundle.min.js`) |     1     | [10027](https://www.zaproxy.org/docs/alerts/10027/) |
| Session Management Response Identified                                      |     2     | [10112](https://www.zaproxy.org/docs/alerts/10112/) |
| User Agent Fuzzer                                                           | Systemic  | [10104](https://www.zaproxy.org/docs/alerts/10104/) |
| User Controllable HTML Attribute (Potential XSS)                            |     1     | [10031](https://www.zaproxy.org/docs/alerts/10031/) |

> **Note:** Most informational items require no action. The **GET for POST** finding is worth fixing — restrict `/signup.html` to `POST` only.

---

## ✅ Recommended Action Plan

1. **Apply security headers globally** (CSP, `X-Frame-Options`, `X-Content-Type-Options`, hide `Server`) — use a Flask `@app.after_request` hook.
2. **Tighten CSP** — remove `'unsafe-inline'`, switch `report-uri` → `report-to`.
3. **Restrict HTTP methods** — only allow `POST` where expected.
4. **Re-run the scan** to confirm fixes.
