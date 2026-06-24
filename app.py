import os
import platform
from collections import namedtuple

_UnameResult = namedtuple('uname_result', ['system', 'node', 'release', 'version', 'machine'])
platform.win32_ver = lambda release='', version='', csd='', ptype='': ('10', '10.0.19045', '', 'Multiprocessor Free')
platform.uname = lambda: _UnameResult('Windows', 'DESKTOP', '10', '10.0.19045', 'AMD64')

from flask import Flask, jsonify, send_file
import sys
from core.config import playbooks_dir, data_dir, model_dir, base_dir

sys.path.append(os.path.join(base_dir, "scratch"))
sys.path.append(os.path.join(base_dir, "services"))

from core.model_loader import load_all_models
from core.error_handlers import register_error_handlers

from routes.predict_routes import predict_bp
from routes.audit_routes import audit_bp
from routes.diversion_routes import diversion_bp
from routes.optimize_routes import optimize_bp
from routes.incident_routes import incident_bp
from routes.system_routes import system_bp
from routes.dashboard_routes import dashboard_bp
from routes.feedback_routes import feedback_bp
from routes.retrain_routes import retrain_bp
from routes.btp_routes import btp_bp
from routes.playbook_routes import playbook_bp
from routes.conflict_routes import conflict_bp

app = Flask(__name__)

register_error_handlers(app)

app.register_blueprint(predict_bp)
app.register_blueprint(audit_bp)
app.register_blueprint(diversion_bp)
app.register_blueprint(optimize_bp)
app.register_blueprint(incident_bp)
app.register_blueprint(system_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(feedback_bp)
app.register_blueprint(retrain_bp)
app.register_blueprint(btp_bp)
app.register_blueprint(playbook_bp)
app.register_blueprint(conflict_bp)

@app.route('/')
def index_page():
    return send_file(os.path.join(base_dir, 'index.html'))

@app.route('/inspect_crops')
def inspect_crops():
    return send_file(os.path.join(base_dir, 'inspect_crops.html'))

@app.route('/static/icons/<path:filename>')
def static_icons(filename):
    icons_dir = os.path.join(base_dir, 'static', 'icons')
    return send_file(os.path.join(icons_dir, filename))

if __name__ == '__main__':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.makedirs(playbooks_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(model_dir, exist_ok=True)
    
    print("Loading intelligence components...")
    load_all_models()
    
    port = int(os.environ.get("PORT", 7860))
    print(f'[OK] Models loaded | Data ready | TRAFIQ360 at http://0.0.0.0:{port}')
    app.run(host='0.0.0.0', port=port, debug=False)
