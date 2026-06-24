import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

model_dir = os.path.join(base_dir, "models")
data_dir = os.path.join(base_dir, "data")
os.makedirs(data_dir, exist_ok=True)

csv_path = os.path.join(base_dir, "Astram event data_anonymized - Astram event data_anonymizedb40ac87.csv")
feedback_csv_path = os.path.join(base_dir, "feedback_data.csv")
feedback_xlsx_path = os.path.join(data_dir, "post_event_feedback.xlsx")
btp_xlsx_path = os.path.join(data_dir, "imported_btp_events.xlsx")
audit_xlsx_path = os.path.join(data_dir, "audit_log.xlsx")
registry_path = os.path.join(data_dir, "model_versions.json")
active_txt_path = os.path.join(model_dir, "active_version.txt")

playbooks_dir = os.path.join(base_dir, "playbooks")
os.makedirs(playbooks_dir, exist_ok=True)
