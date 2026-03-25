"""
ISO 27001 Annex A.8 - Audit Web Application
=============================================
Flask web app for uploading system configs,
evaluating against ISO 27001 rules, and generating reports.
"""

import os
import json
import uuid
from datetime import datetime
from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, send_file, jsonify
)
from audit_engine import AuditEngine
from report_generator import ReportGenerator

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
REPORT_DIR = os.path.join(BASE_DIR, 'reports')

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

# Initialize engine and report generator
engine = AuditEngine()
report_gen = ReportGenerator(REPORT_DIR)

# In-memory store for audit results (simple dict)
audit_store = {}


@app.route('/')
def index():
    """Dashboard / upload page."""
    # Get past audits sorted by timestamp
    past_audits = sorted(
        audit_store.values(),
        key=lambda x: x['summary']['timestamp'],
        reverse=True
    )
    return render_template('index.html', past_audits=past_audits)


@app.route('/upload', methods=['POST'])
def upload():
    """Handle config file upload and run audit."""
    if 'config_file' not in request.files:
        flash('No file selected.', 'error')
        return redirect(url_for('index'))

    file = request.files['config_file']
    if file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('index'))

    if not file.filename.endswith('.json'):
        flash('Please upload a JSON file.', 'error')
        return redirect(url_for('index'))

    try:
        # Read and parse JSON
        config_data = json.loads(file.read().decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        flash(f'Invalid JSON file: {str(e)}', 'error')
        return redirect(url_for('index'))

    # Generate audit ID
    audit_id = datetime.now().strftime('%Y%m%d_%H%M%S') + '_' + uuid.uuid4().hex[:6]

    # Save uploaded file
    upload_path = os.path.join(UPLOAD_DIR, f'{audit_id}.json')
    with open(upload_path, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2)

    # Run evaluation
    try:
        results = engine.evaluate(config_data)
    except Exception as e:
        flash(f'Audit evaluation error: {str(e)}', 'error')
        return redirect(url_for('index'))

    # Store results
    results['audit_id'] = audit_id
    results['filename'] = file.filename
    audit_store[audit_id] = results

    # Pre-generate HTML report
    try:
        report_gen.generate_html_report(results, audit_id)
    except Exception:
        pass  # Report generation is optional

    return redirect(url_for('results', audit_id=audit_id))


@app.route('/results/<audit_id>')
def results(audit_id):
    """Display audit results."""
    if audit_id not in audit_store:
        flash('Audit not found.', 'error')
        return redirect(url_for('index'))

    data = audit_store[audit_id]
    return render_template('results.html', data=data, audit_id=audit_id)


@app.route('/download/<audit_id>/<fmt>')
def download(audit_id, fmt):
    """Download report in HTML or PDF format."""
    if audit_id not in audit_store:
        flash('Audit not found.', 'error')
        return redirect(url_for('index'))

    data = audit_store[audit_id]

    if fmt == 'html':
        filepath = os.path.join(REPORT_DIR, f'audit_report_{audit_id}.html')
        if not os.path.exists(filepath):
            filepath = report_gen.generate_html_report(data, audit_id)
        return send_file(filepath, as_attachment=True,
                         download_name=f'ISO27001_Audit_{audit_id}.html')

    elif fmt == 'pdf':
        filepath = os.path.join(REPORT_DIR, f'audit_report_{audit_id}.pdf')
        if not os.path.exists(filepath):
            filepath = report_gen.generate_pdf_report(data, audit_id)
        if filepath and os.path.exists(filepath):
            return send_file(filepath, as_attachment=True,
                             download_name=f'ISO27001_Audit_{audit_id}.pdf')
        else:
            flash('PDF generation failed. Please ensure weasyprint is installed.', 'error')
            return redirect(url_for('results', audit_id=audit_id))

    flash('Invalid format.', 'error')
    return redirect(url_for('results', audit_id=audit_id))


@app.route('/api/audit/<audit_id>')
def api_audit(audit_id):
    """API endpoint to get audit results as JSON."""
    if audit_id not in audit_store:
        return jsonify({'error': 'Audit not found'}), 404
    return jsonify(audit_store[audit_id])


@app.route('/delete/<audit_id>', methods=['POST'])
def delete_audit(audit_id):
    """Delete an audit and its files."""
    if audit_id in audit_store:
        del audit_store[audit_id]

    # Clean up files
    for ext in ['json', 'html', 'pdf']:
        path = os.path.join(
            UPLOAD_DIR if ext == 'json' else REPORT_DIR,
            f'{"" if ext == "json" else "audit_report_"}{audit_id}.{ext}'
        )
        if os.path.exists(path):
            os.remove(path)

    flash('Audit deleted.', 'info')
    return redirect(url_for('index'))


if __name__ == '__main__':
    print("=" * 56)
    print("  ISO 27001 Annex A.8 Audit App")
    print("  http://localhost:5000")
    print("=" * 56)
    app.run(debug=True, host='0.0.0.0', port=5000)
