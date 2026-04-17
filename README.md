# Take Control Plus – API Batch Processor

A Python GUI application for batch-processing Take Control Plus API operations via CSV uploads.

---

## Features

- 🔐 **Session Management** – Create a new Take Control Plus session before running operations
- 📋 **4 Operation Types** – Technician, Support Ticket, Device Installer, Session
- 📁 **CSV File Browser** – Load any CSV matching the selected operation
- ✅ **Smart Validation** – Per-field checks with email format validation and integer type checks
- 🚀 **API Integration** – POST records directly to the Take Control Plus REST API
- 📊 **Real-time Logging** – Coloured output for success, errors, and API responses
- 📈 **Status Bar** – Live total / valid / error counters

---

## Quick Start

```bash
git clone https://github.com/andylancasternable/TakeControlAPI.git
cd TakeControlAPI
pip install -r requirements.txt
python gui_converter.py
```

---

## Usage

### 1. Create a New Session
Click **Create New Session** and fill in:
- Department ID
- Technician Username
- Language (default: `en`)
- Customer Name & Email
- Customer Number (optional)

### 2. Select an Operation Type
Choose one of:
| Operation | Endpoint | Required Fields |
|-----------|----------|-----------------|
| Technician | `POST /tech` | email, name, profile, language, timezone |
| Support Ticket | `POST /ticket` | customer_name, customer_email, problem_description |
| Device Installer | `POST /device/installer` | device_name, device_type, group_id, customer_name, customer_email, max_installs, link_expiration_date |
| Session | `POST /session` | department_id, technician_username, language, customer_name, customer_email |

### 3. Load a CSV File
Click **Browse CSV File** and select a file with the appropriate columns.

### 4. Run an Action
| Button | Action |
|--------|--------|
| **Convert & Validate** | Parses and validates the CSV; shows errors in the log |
| **Post to API** | POSTs previously validated records to the API |
| **Convert & Post** | Does both steps in sequence |

---

## CSV Format Examples

### sample_technician.csv
```csv
email,name,profile,language,timezone
jane.doe@example.com,Jane Doe,admin,en,America/New_York
john.smith@example.com,John Smith,technician,en,America/Chicago
```

### sample_ticket.csv
```csv
customer_name,customer_email,problem_description
John Doe,john.doe@example.com,Unable to access network drives
Sandy Smith,sandy@company.com,Printer not responding
```

### sample_installer.csv
```csv
device_name,device_type,group_id,customer_name,customer_email,max_installs,link_expiration_date
Marketing Laptop,2,12619,Jane Smith,jane.smith@example.com,1,2024-12-31 23:59:59
```

### sample_session.csv
```csv
department_id,technician_username,language,customer_name,customer_email,customer_number
id_1234,user123,en,Sandy Smith,sandy@company.com,d4f%d$3
```

---

## API Configuration

| Setting | Value |
|---------|-------|
| Base URL | `https://api.us0.swi-rc.com/rest` |
| Auth Header | `INTEGRATION-KEY: <token>` |
| Content-Type | `application/json` |
| Accept | `application/json` |

### Response Format
```json
{
  "result": "SUCCESS",
  "details": { ... },
  "errorDetails": null
}
```

---

## Dependencies

```
requests
pandas
```

Install with:
```bash
pip install -r requirements.txt
```

---

## License

MIT
