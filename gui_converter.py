import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter import scrolledtext
import csv
import json
import re
from datetime import datetime
from pathlib import Path
import threading
try:
    import requests
except ImportError:
    requests = None


# ---------------------------------------------------------------------------
# Operation type configuration
# ---------------------------------------------------------------------------
OPERATION_CONFIG = {
    "Technician": {
        "endpoint": "/tech",
        "required_fields": ["email", "name", "profile", "language", "timezone"],
        "email_fields": ["email"],
        "description": "Create new technician accounts",
    },
    "Support Ticket": {
        "endpoint": "/ticket",
        "required_fields": ["customer_name", "customer_email", "problem_description"],
        "email_fields": ["customer_email"],
        "description": "Create support tickets",
    },
    "Device Installer": {
        "endpoint": "/device/installer",
        "required_fields": [
            "device_name", "device_type", "group_id",
            "customer_name", "customer_email",
            "max_installs", "link_expiration_date",
        ],
        "email_fields": ["customer_email"],
        "int_fields": ["device_type", "group_id", "max_installs"],
        "description": "Create device installers",
    },
    "Session": {
        "endpoint": "/session",
        "required_fields": [
            "department_id", "technician_username", "language",
            "customer_name", "customer_email",
        ],
        "email_fields": ["customer_email"],
        "description": "Create support sessions",
    },
}

BASE_URL = "https://api.us0.swi-rc.com/rest"
API_TOKEN = (
    "02.aB7waafgZ64HSV5dbUUfzdxtKHMELByZZ3sKDm9efPhnmVt9FkSaeYSFRqF9oKZojhUgEVgECBFBJ"
    "HyCJMxE6DBdPbVKWWdrn5WfTFgjFEdNvfL4Rn173LV7hYutcV9byEM3oersLTM2bu5iPtuLrFAfdT8BS"
    "1eSAW1ANt5sU8jXmpXF82PaSyuedcB4VWAqGnjMUC18VLXuWoN24DgHjZmFtCwpdBVV42D1xELzExwE"
)


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------
class TakeControlBatchProcessor:
    def __init__(self, root):
        self.root = root
        self.root.title("Take Control Plus – API Batch Processor")
        self.root.geometry("980x760")
        self.root.configure(bg="#f0f0f0")
        self.root.minsize(800, 600)

        self.api_token = API_TOKEN
        self.base_url = BASE_URL
        self.session_id = None

        self.selected_file = None
        self.valid_records = []
        self.error_records = []
        self.operation_var = tk.StringVar(value="Technician")

        self._setup_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _setup_ui(self):
        # ---- Header ----
        header = tk.Frame(self.root, bg="#2c3e50", height=60)
        header.pack(fill=tk.X)
        tk.Label(
            header,
            text="Take Control Plus – API Batch Processor",
            font=("Arial", 16, "bold"),
            fg="white",
            bg="#2c3e50",
        ).pack(pady=12)

        # ---- Session Frame ----
        session_frame = tk.LabelFrame(
            self.root, text="Session Management",
            font=("Arial", 10, "bold"), bg="#f0f0f0", padx=10, pady=8,
        )
        session_frame.pack(fill=tk.X, padx=10, pady=(10, 4))

        tk.Button(
            session_frame, text="Create New Session",
            command=self._open_session_dialog,
            bg="#8e44ad", fg="white", font=("Arial", 10, "bold"), padx=12, pady=6,
        ).pack(side=tk.LEFT, padx=5)

        tk.Label(session_frame, text="Active Session ID:", font=("Arial", 9), bg="#f0f0f0").pack(
            side=tk.LEFT, padx=(20, 4)
        )
        self.session_label = tk.Label(
            session_frame, text="None", font=("Arial", 9, "italic"),
            fg="#7f8c8d", bg="#f0f0f0",
        )
        self.session_label.pack(side=tk.LEFT)

        # ---- Operation Type Frame ----
        op_frame = tk.LabelFrame(
            self.root, text="Operation Type",
            font=("Arial", 10, "bold"), bg="#f0f0f0", padx=10, pady=8,
        )
        op_frame.pack(fill=tk.X, padx=10, pady=4)

        for op in OPERATION_CONFIG:
            rb = tk.Radiobutton(
                op_frame, text=op, variable=self.operation_var, value=op,
                command=self._on_operation_change,
                font=("Arial", 10), bg="#f0f0f0", activebackground="#f0f0f0",
            )
            rb.pack(side=tk.LEFT, padx=12)

        self.op_desc_label = tk.Label(
            op_frame, text=OPERATION_CONFIG["Technician"]["description"],
            font=("Arial", 9, "italic"), fg="#2980b9", bg="#f0f0f0",
        )
        self.op_desc_label.pack(side=tk.LEFT, padx=20)

        # ---- File Selection Frame ----
        file_frame = tk.LabelFrame(
            self.root, text="CSV File",
            font=("Arial", 10, "bold"), bg="#f0f0f0", padx=10, pady=8,
        )
        file_frame.pack(fill=tk.X, padx=10, pady=4)

        tk.Button(
            file_frame, text="Browse CSV File", command=self._browse_file,
            bg="#3498db", fg="white", font=("Arial", 10), padx=10, pady=4,
        ).pack(side=tk.LEFT, padx=5)

        self.file_label = tk.Label(
            file_frame, text="No file selected",
            font=("Arial", 9), fg="#7f8c8d", bg="#f0f0f0",
        )
        self.file_label.pack(side=tk.LEFT, padx=10)

        self.fields_label = tk.Label(
            file_frame,
            text=f"Required: {', '.join(OPERATION_CONFIG['Technician']['required_fields'])}",
            font=("Arial", 8), fg="#95a5a6", bg="#f0f0f0",
        )
        self.fields_label.pack(side=tk.RIGHT, padx=5)

        # ---- Action Buttons ----
        action_frame = tk.Frame(self.root, bg="#f0f0f0")
        action_frame.pack(fill=tk.X, padx=10, pady=6)

        tk.Button(
            action_frame, text="Convert & Validate",
            command=self._convert_validate,
            bg="#27ae60", fg="white", font=("Arial", 10, "bold"), padx=14, pady=7,
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            action_frame, text="Post to API",
            command=self._post_to_api,
            bg="#e67e22", fg="white", font=("Arial", 10, "bold"), padx=14, pady=7,
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            action_frame, text="Convert & Post",
            command=self._convert_and_post,
            bg="#c0392b", fg="white", font=("Arial", 10, "bold"), padx=14, pady=7,
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            action_frame, text="Clear Log",
            command=self._clear_log,
            bg="#7f8c8d", fg="white", font=("Arial", 10), padx=14, pady=7,
        ).pack(side=tk.RIGHT, padx=5)

        # ---- Log Output ----
        log_frame = tk.LabelFrame(
            self.root, text="Processing Log",
            font=("Arial", 10, "bold"), bg="#f0f0f0", padx=5, pady=5,
        )
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        self.log_output = scrolledtext.ScrolledText(
            log_frame, height=18, font=("Courier", 9),
            bg="#1e2a35", fg="#ecf0f1", insertbackground="white",
        )
        self.log_output.pack(fill=tk.BOTH, expand=True)

        # colour tags
        self.log_output.tag_config("ok", foreground="#2ecc71")
        self.log_output.tag_config("err", foreground="#e74c3c")
        self.log_output.tag_config("warn", foreground="#f39c12")
        self.log_output.tag_config("info", foreground="#3498db")
        self.log_output.tag_config("head", foreground="#ecf0f1", font=("Courier", 9, "bold"))

        # ---- Status Bar ----
        self.status_bar = tk.Label(
            self.root, text="Ready  |  Total: 0  Valid: 0  Errors: 0",
            font=("Arial", 9), bg="#34495e", fg="#ecf0f1",
            relief=tk.SUNKEN, anchor=tk.W, padx=6,
        )
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------
    def _on_operation_change(self):
        op = self.operation_var.get()
        cfg = OPERATION_CONFIG[op]
        self.op_desc_label.config(text=cfg["description"])
        self.fields_label.config(text=f"Required: {', '.join(cfg['required_fields'])}")
        self.valid_records = []
        self.error_records = []

    def _browse_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if path:
            self.selected_file = path
            self.file_label.config(text=f"Selected: {Path(path).name}")
            self._log(f"File selected: {path}", "ok")

    # ------------------------------------------------------------------
    # Session dialog
    # ------------------------------------------------------------------
    def _open_session_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Create New Session")
        dialog.geometry("480x400")
        dialog.configure(bg="#f0f0f0")
        dialog.grab_set()
        dialog.resizable(False, False)

        tk.Label(
            dialog, text="Create New Session",
            font=("Arial", 13, "bold"), bg="#2c3e50", fg="white",
        ).pack(fill=tk.X, pady=0)

        form_frame = tk.Frame(dialog, bg="#f0f0f0", padx=20, pady=10)
        form_frame.pack(fill=tk.BOTH, expand=True)

        fields = [
            ("Department ID *", "department_id"),
            ("Technician Username *", "technician_username"),
            ("Language *", "language"),
            ("Customer Name *", "customer_name"),
            ("Customer Email *", "customer_email"),
            ("Customer Number", "customer_number"),
        ]
        defaults = {
            "language": "en",
        }

        entries = {}
        for i, (label, key) in enumerate(fields):
            tk.Label(form_frame, text=label, font=("Arial", 9), bg="#f0f0f0", anchor="w").grid(
                row=i, column=0, sticky="w", pady=4
            )
            e = tk.Entry(form_frame, width=34, font=("Arial", 9))
            e.grid(row=i, column=1, sticky="ew", padx=(10, 0), pady=4)
            if key in defaults:
                e.insert(0, defaults[key])
            entries[key] = e

        form_frame.columnconfigure(1, weight=1)

        btn_frame = tk.Frame(dialog, bg="#f0f0f0", padx=20, pady=10)
        btn_frame.pack(fill=tk.X)

        def _submit():
            payload = {k: e.get().strip() for k, e in entries.items()}
            required_session = ["department_id", "technician_username", "language",
                                 "customer_name", "customer_email"]
            missing = [f for f in required_session if not payload.get(f)]
            if missing:
                messagebox.showerror(
                    "Missing Fields",
                    f"Please fill in: {', '.join(missing)}",
                    parent=dialog,
                )
                return
            if not self._validate_email(payload["customer_email"]):
                messagebox.showerror(
                    "Invalid Email",
                    f"Invalid email address: {payload['customer_email']}",
                    parent=dialog,
                )
                return
            # Remove empty optional fields
            payload = {k: v for k, v in payload.items() if v}
            dialog.destroy()
            self._do_create_session(payload)

        tk.Button(
            btn_frame, text="Create Session",
            command=_submit,
            bg="#8e44ad", fg="white", font=("Arial", 10, "bold"), padx=12, pady=5,
        ).pack(side=tk.LEFT)

        tk.Button(
            btn_frame, text="Cancel",
            command=dialog.destroy,
            bg="#7f8c8d", fg="white", font=("Arial", 10), padx=12, pady=5,
        ).pack(side=tk.LEFT, padx=10)

    def _do_create_session(self, payload):
        self._log("=" * 70, "head")
        self._log("Creating New Session...", "head")
        self._log("=" * 70, "head")
        self._log(f"Payload: {json.dumps(payload, indent=2)}", "info")

        if requests is None:
            self._log("❌ 'requests' library not installed. Run: pip install requests", "err")
            return

        url = f"{self.base_url}/session"
        headers = {
            "INTEGRATION-KEY": self.api_token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=15)
            self._log(f"HTTP Status: {resp.status_code}", "info")
            try:
                data = resp.json()
                self._log(f"Response: {json.dumps(data, indent=2)}", "info")
                if data.get("result") == "SUCCESS":
                    details = data.get("details") or {}
                    sid = details.get("session_id") or details.get("id") or "created"
                    self.session_id = str(sid)
                    self.session_label.config(text=self.session_id, fg="#27ae60")
                    self._log(f"✓ Session created successfully. ID: {self.session_id}", "ok")
                else:
                    err = data.get("errorDetails") or data.get("error") or "Unknown error"
                    self._log(f"❌ Session creation failed: {err}", "err")
            except ValueError:
                self._log(f"Response body: {resp.text[:500]}", "warn")
        except requests.exceptions.ConnectionError:
            self._log("❌ Connection error – check network and base URL.", "err")
        except requests.exceptions.Timeout:
            self._log("❌ Request timed out.", "err")
        except Exception as exc:
            self._log(f"❌ Unexpected error: {exc}", "err")

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _validate_email(email):
        pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def _build_record(self, row, op):
        cfg = OPERATION_CONFIG[op]
        required = cfg["required_fields"]
        email_fields = cfg.get("email_fields", [])
        int_fields = cfg.get("int_fields", [])

        errors = []
        missing = [f for f in required if not row.get(f, "").strip()]
        if missing:
            errors.append(f"Missing fields: {', '.join(missing)}")

        for ef in email_fields:
            val = row.get(ef, "").strip()
            if val and not self._validate_email(val):
                errors.append(f"Invalid email for '{ef}': {val}")

        if errors:
            return None, errors

        record = {}
        for field in required:
            val = row[field].strip()
            if field in int_fields:
                try:
                    val = int(val)
                except ValueError:
                    errors.append(f"Field '{field}' must be an integer, got: {val}")
                    return None, errors
            record[field] = val

        # include optional fields if present
        for k, v in row.items():
            if k not in record and v and v.strip():
                record[k] = v.strip()

        return record, []

    def _process_csv(self, op):
        cfg = OPERATION_CONFIG[op]
        self.valid_records = []
        self.error_records = []

        self._log("=" * 70, "head")
        self._log(f"Processing CSV for operation: {op}", "head")
        self._log(f"Endpoint: {self.base_url}{cfg['endpoint']}", "info")
        self._log(f"Required fields: {', '.join(cfg['required_fields'])}", "info")
        self._log("=" * 70, "head")
        self._log("")

        try:
            with open(self.selected_file, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    self._log("❌ CSV file is empty or has no header row.", "err")
                    return

                for row_num, row in enumerate(reader, start=2):
                    record, errors = self._build_record(row, op)
                    if errors:
                        for e in errors:
                            self._log(f"  Row {row_num} ❌ {e}", "err")
                        self.error_records.append({"row": row_num, "errors": errors})
                    else:
                        id_val = (
                            record.get("email")
                            or record.get("customer_email")
                            or record.get("device_name")
                            or f"row-{row_num}"
                        )
                        self._log(f"  Row {row_num} ✓ Valid: {id_val}", "ok")
                        self.valid_records.append(record)

        except FileNotFoundError:
            self._log(f"❌ File not found: {self.selected_file}", "err")
            return
        except Exception as exc:
            self._log(f"❌ Error reading CSV: {exc}", "err")
            return

        total = len(self.valid_records) + len(self.error_records)
        self._log("")
        self._log("─" * 70, "head")
        self._log(f"SUMMARY  –  Total: {total}  |  Valid: {len(self.valid_records)}  |  Errors: {len(self.error_records)}", "head")
        self._log("─" * 70, "head")
        self._update_status()

    # ------------------------------------------------------------------
    # API posting
    # ------------------------------------------------------------------
    def _post_records(self, op):
        if not self.valid_records:
            self._log("⚠ No valid records to post. Run 'Convert & Validate' first.", "warn")
            return

        if requests is None:
            self._log("❌ 'requests' library not installed. Run: pip install requests", "err")
            return

        cfg = OPERATION_CONFIG[op]
        url = f"{self.base_url}{cfg['endpoint']}"
        headers = {
            "INTEGRATION-KEY": self.api_token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        self._log("")
        self._log("=" * 70, "head")
        self._log(f"Posting {len(self.valid_records)} record(s) to {url}", "head")
        self._log("=" * 70, "head")

        success_count = 0
        fail_count = 0

        for i, record in enumerate(self.valid_records, start=1):
            self._log(f"\n  [{i}/{len(self.valid_records)}] Posting: {json.dumps(record)}", "info")
            try:
                resp = requests.post(url, json=record, headers=headers, timeout=15)
                self._log(f"  HTTP {resp.status_code}", "info")
                try:
                    data = resp.json()
                    if data.get("result") == "SUCCESS":
                        self._log(f"  ✓ SUCCESS", "ok")
                        details = data.get("details")
                        if details:
                            self._log(f"    Details: {json.dumps(details)}", "ok")
                        success_count += 1
                    else:
                        err = data.get("errorDetails") or data.get("error") or "Unknown error"
                        self._log(f"  ❌ FAILED: {err}", "err")
                        fail_count += 1
                except ValueError:
                    self._log(f"  Response (non-JSON): {resp.text[:300]}", "warn")
                    if resp.ok:
                        success_count += 1
                    else:
                        fail_count += 1
            except requests.exceptions.ConnectionError:
                self._log("  ❌ Connection error.", "err")
                fail_count += 1
            except requests.exceptions.Timeout:
                self._log("  ❌ Request timed out.", "err")
                fail_count += 1
            except Exception as exc:
                self._log(f"  ❌ Error: {exc}", "err")
                fail_count += 1

        self._log("")
        self._log("─" * 70, "head")
        self._log(
            f"POST COMPLETE  –  Success: {success_count}  |  Failed: {fail_count}",
            "ok" if fail_count == 0 else "warn",
        )
        self._log("─" * 70, "head")
        self._update_status()

    # ------------------------------------------------------------------
    # Button commands
    # ------------------------------------------------------------------
    def _convert_validate(self):
        if not self.selected_file:
            messagebox.showerror("No File", "Please select a CSV file first.")
            return
        self._clear_log(keep_file=True)
        self._process_csv(self.operation_var.get())

    def _post_to_api(self):
        self._post_records(self.operation_var.get())

    def _convert_and_post(self):
        if not self.selected_file:
            messagebox.showerror("No File", "Please select a CSV file first.")
            return
        self._clear_log(keep_file=True)
        op = self.operation_var.get()
        self._process_csv(op)
        self._post_records(op)

    # ------------------------------------------------------------------
    # Log helpers
    # ------------------------------------------------------------------
    def _log(self, message, tag=None):
        if tag:
            self.log_output.insert(tk.END, message + "\n", tag)
        else:
            self.log_output.insert(tk.END, message + "\n")
        self.log_output.see(tk.END)
        self.root.update_idletasks()

    def _clear_log(self, keep_file=False):
        self.log_output.delete(1.0, tk.END)
        self.valid_records = []
        self.error_records = []
        if not keep_file:
            self.selected_file = None
            self.file_label.config(text="No file selected")
        self._update_status()

    def _update_status(self):
        total = len(self.valid_records) + len(self.error_records)
        self.status_bar.config(
            text=(
                f"Ready  |  Total: {total}  "
                f"Valid: {len(self.valid_records)}  "
                f"Errors: {len(self.error_records)}"
            )
        )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = TakeControlBatchProcessor(root)
    root.mainloop()