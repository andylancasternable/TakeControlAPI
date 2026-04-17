import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import scrolledtext
import csv
import json
import re
from datetime import datetime
from pathlib import Path

class CSVToJSONConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("TakeControlAPI - CSV to JSON Converter")
        self.root.geometry("900x700")
        self.root.configure(bg="#f0f0f0")
        
        self.api_token = "02.aB7waafgZ64HSV5dbUUfzdxtKHMELByZZ3sKDm9efPhnmVt9FkSaeYSFRqF9oKZojhUgEVgECBFBJHyCJMxE6DBdPbVKWWdrn5WfTFgjFEdNvfL4Rn173LV7hYutcV9byEM3oersLTM2bu5iPtuLrFAfdT8BS1eSAW1ANt5sU8jXmpXF82PaSyuedcB4VWAqGnjMUC18VLXuWoN24DgHjZmFtCwpdBVV42D1xELzExwE"
        self.selected_file = None
        self.valid_records = []
        self.error_records = []
        
        self.setup_ui()
    
    def setup_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=60)
        header_frame.pack(fill=tk.X)
        
        title_label = tk.Label(header_frame, text="CSV to JSON Converter", 
                               font=("Arial", 18, "bold"), fg="white", bg="#2c3e50")
        title_label.pack(pady=10)
        
        # File Selection Frame
        file_frame = tk.LabelFrame(self.root, text="File Selection", font=("Arial", 10, "bold"), 
                                   bg="#f0f0f0", padx=10, pady=10)
        file_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(file_frame, text="Browse CSV File", command=self.browse_file, 
                 bg="#3498db", fg="white", font=("Arial", 10), padx=10).pack(side=tk.LEFT, padx=5)
        
        self.file_label = tk.Label(file_frame, text="No file selected", font=("Arial", 9), 
                                    fg="#7f8c8d", bg="#f0f0f0")
        self.file_label.pack(side=tk.LEFT, padx=10)
        
        # API Token Frame
        token_frame = tk.LabelFrame(self.root, text="API Configuration", font=("Arial", 10, "bold"), 
                                    bg="#f0f0f0", padx=10, pady=10)
        token_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(token_frame, text="API Token:", font=("Arial", 9), bg="#f0f0f0").pack(side=tk.LEFT)
        
        self.token_label = tk.Label(token_frame, text=self.api_token[:20] + "...", 
                                    font=("Arial", 9), fg="#27ae60", bg="#f0f0f0")
        self.token_label.pack(side=tk.LEFT, padx=10)
        
        # Control Frame
        control_frame = tk.Frame(self.root, bg="#f0f0f0")
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(control_frame, text="Convert & Validate", command=self.process_csv, 
                 bg="#27ae60", fg="white", font=("Arial", 10, "bold"), padx=15, pady=8).pack(side=tk.LEFT, padx=5)
        
        tk.Button(control_frame, text="Clear Log", command=self.clear_log, 
                 bg="#e74c3c", fg="white", font=("Arial", 10), padx=15).pack(side=tk.LEFT, padx=5)
        
        # Log Output Frame
        log_frame = tk.LabelFrame(self.root, text="Processing Log", font=("Arial", 10, "bold"), 
                                  bg="#f0f0f0", padx=5, pady=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.log_output = scrolledtext.ScrolledText(log_frame, height=20, width=100, 
                                                     font=("Courier", 9), bg="#2c3e50", fg="#ecf0f1")
        self.log_output.pack(fill=tk.BOTH, expand=True)
        
        # Status Bar
        self.status_bar = tk.Label(self.root, text="Ready", font=("Arial", 9), 
                                   bg="#34495e", fg="#ecf0f1", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
    
    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if file_path:
            self.selected_file = file_path
            self.file_label.config(text=f"Selected: {Path(file_path).name}")
            self.log(f"✓ File selected: {file_path}")
    
    def validate_email(self, email):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def log(self, message):
        self.log_output.insert(tk.END, message + "\n")
        self.log_output.see(tk.END)
        self.root.update()
    
    def clear_log(self):
        self.log_output.delete(1.0, tk.END)
        self.valid_records = []
        self.error_records = []
    
    def process_csv(self):
        if not self.selected_file:
            messagebox.showerror("Error", "Please select a CSV file first!")
            return
        
        self.clear_log()
        self.log("=" * 80)
        self.log("Starting CSV to JSON Conversion")
        self.log("=" * 80)
        self.log("")
        
        try:
            with open(self.selected_file, 'r', encoding='utf-8') as f:
                csv_reader = csv.DictReader(f)
                
                if not csv_reader.fieldnames:
                    self.log("❌ ERROR: CSV file is empty!")
                    return
                
                required_fields = ['email', 'name', 'profile', 'language', 'timezone']
                self.log(f"Required fields: {', '.join(required_fields)}")
                self.log("")
                
                for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (header is 1)
                    self.log(f"Row {row_num}: Processing...")
                    
                    # Check for missing fields
                    missing_fields = [field for field in required_fields if not row.get(field, '').strip()]
                    
                    if missing_fields:
                        error_msg = f"  ❌ Missing fields: {', '.join(missing_fields)}"
                        self.log(error_msg)
                        self.error_records.append({'row': row_num, 'error': error_msg})
                        continue
                    
                    # Validate email
                    email = row['email'].strip()
                    if not self.validate_email(email):
                        error_msg = f"  ❌ Invalid email format: {email}"
                        self.log(error_msg)
                        self.error_records.append({'row': row_num, 'error': error_msg})
                        continue
                    
                    # Create JSON object
                    json_obj = {
                        'email': email,
                        'name': row['name'].strip(),
                        'profile': row['profile'].strip(),
                        'language': row['language'].strip(),
                        'timezone': row['timezone'].strip()
                    }
                    
                    self.valid_records.append(json_obj)
                    self.log(f"  ✓ Valid: {email}")
            
            self.log("")
            self.log("=" * 80)
            self.log("SUMMARY")
            self.log("=" * 80)
            self.log(f"Total rows processed: {len(self.valid_records) + len(self.error_records)}")
            self.log(f"✓ Valid records: {len(self.valid_records)}")
            self.log(f"❌ Error records: {len(self.error_records)}")
            self.log("")
            
            if self.valid_records:
                self.save_json()
            else:
                self.log("⚠ No valid records to save!")
        
        except Exception as e:
            self.log(f"❌ ERROR: {str(e)}")
        
        self.status_bar.config(text=f"Processed: {len(self.valid_records)} valid, {len(self.error_records)} errors")
    
    def save_json(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"technicians_{timestamp}.json"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.valid_records, f, indent=2, ensure_ascii=False)
            
            self.log(f"✓ JSON file saved: {output_file}")
            self.log(f"  Location: {Path(output_file).absolute()}")
            self.log(f"  Records in file: {len(self.valid_records)}")
            self.log("")
            self.log("Ready to POST to /tech endpoint with your API token!")
        
        except Exception as e:
            self.log(f"❌ ERROR saving file: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CSVToJSONConverter(root)
    root.mainloop()