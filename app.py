"""
Flask Application - Log Analytics with Six Agents
"""
from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import io
from pathlib import Path
from werkzeug.utils import secure_filename

import config
import utils
from agents.sentinel import validate_file, validate_local_folder
from agents.ledger import Ledger
from agents.nexus import Nexus
from agents.oracle import Oracle
from agents.cipher import Cipher
from agents.prism import Prism

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = config.MAX_UPLOAD_SIZE
app.config['UPLOAD_FOLDER'] = config.RAW_DIR

# Initialize agents
ledger = Ledger(config.DB_PATH)
nexus = Nexus(config.INDEX_DIR, ledger)
oracle = Oracle(nexus)
cipher = Cipher(ledger)
prism = Prism(ledger)


@app.route('/')
def index():
    """Home page - redirect to dashboard"""
    return render_template('dashboard.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """Upload logs page"""
    if request.method == 'GET':
        return render_template('upload.html')
    
    results = []
    
    # Handle file uploads
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided', 'results': []}), 400
        
        files = request.files.getlist('files')
        
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': 'No files selected', 'results': []}), 400
        
        for file in files:
            if file.filename == '' or file.filename is None:
                continue
            
            try:
                filename = secure_filename(file.filename)
                file_bytes = file.read()
                
                if len(file_bytes) == 0:
                    results.append({
                        'filename': filename,
                        'status': 'rejected',
                        'reason': 'Empty file'
                    })
                    continue
                
                # Validate with Sentinel
                validation = validate_file(filename, file_bytes)
                
                if not validation['valid']:
                    results.append({
                        'filename': filename,
                        'status': 'rejected',
                        'reason': ', '.join(validation['reasons'])
                    })
                    continue
                
                # Save raw file
                raw_path = os.path.join(config.RAW_DIR, filename)
                with open(raw_path, 'wb') as f:
                    f.write(file_bytes)
                
                # Record in Ledger
                file_id = ledger.record_file(
                    filename,
                    validation['size'],
                    validation['type'],
                    validation.get('cloud_type')
                )
                
                # Process file
                try:
                    events = process_file(filename, file_bytes, validation)
                    
                    if not events:
                        ledger.update_file_status(file_id, 'processed', event_count=0)
                        results.append({
                            'filename': filename,
                            'status': 'success',
                            'events': 0,
                            'cloud_type': validation.get('cloud_type', 'unknown'),
                            'message': 'No events extracted'
                        })
                        continue
                    
                    # Save processed events
                    processed_path = os.path.join(config.PROCESSED_DIR, f'{filename}.jsonl')
                    with open(processed_path, 'w', encoding='utf-8') as f:
                        for event in events:
                            f.write(utils.json.dumps(event) + '\n')
                    
                    # Store in Ledger
                    event_rows = [
                        (file_id, e['ts_event'], e['level'], e['service'],
                         e['user'], e['ip'], e['message'], e['json'])
                        for e in events
                    ]
                    ledger.add_events(event_rows)
                    ledger.update_file_status(file_id, 'processed', event_count=len(events))
                    
                    results.append({
                        'filename': filename,
                        'status': 'success',
                        'events': len(events),
                        'cloud_type': validation.get('cloud_type', 'unknown')
                    })
                except Exception as e:
                    error_msg = str(e)
                    ledger.update_file_status(file_id, 'error', error_msg)
                    results.append({
                        'filename': filename,
                        'status': 'error',
                        'reason': error_msg
                    })
            except Exception as e:
                results.append({
                    'filename': file.filename if file.filename else 'unknown',
                    'status': 'error',
                    'reason': str(e)
                })
    
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}', 'results': results}), 500
    
    return jsonify({'results': results, 'total': len(results)})


@app.route('/upload/local', methods=['POST'])
def upload_local():
    """Import from local folder"""
    folder_validation = validate_local_folder(config.INCOMING_DIR)
    
    if not folder_validation['valid']:
        return jsonify({'error': folder_validation['reason']}), 400
    
    results = []
    
    for file_info in folder_validation['files']:
        try:
            with open(file_info['path'], 'rb') as f:
                file_bytes = f.read()
            
            filename = file_info['name']
            
            # Validate
            validation = validate_file(filename, file_bytes)
            if not validation['valid']:
                results.append({
                    'filename': filename,
                    'status': 'rejected',
                    'reason': ', '.join(validation['reasons'])
                })
                continue
            
            # Record and process (same as upload)
            file_id = ledger.record_file(filename, validation['size'], validation['type'])
            events = process_file(filename, file_bytes, validation)
            
            processed_path = os.path.join(config.PROCESSED_DIR, f'{filename}.jsonl')
            with open(processed_path, 'w', encoding='utf-8') as f:
                for event in events:
                    f.write(utils.json.dumps(event) + '\n')
            
            event_rows = [
                (file_id, e['ts_event'], e['level'], e['service'],
                 e['user'], e['ip'], e['message'], e['json'])
                for e in events
            ]
            ledger.add_events(event_rows)
            ledger.update_file_status(file_id, 'processed', event_count=len(events))
            
            results.append({
                'filename': filename,
                'status': 'success',
                'events': len(events)
            })
        except Exception as e:
            results.append({
                'filename': filename,
                'status': 'error',
                'reason': str(e)
            })
    
    return jsonify({'results': results})


@app.route('/status')
def status():
    """Processing status page"""
    files = ledger.list_files()
    index_meta = ledger.get_latest_index_meta()
    
    return render_template('status.html', files=files, index_meta=index_meta)


@app.route('/view-file/<filename>')
def view_file(filename):
    """View raw log file content"""
    import os
    raw_path = os.path.join(config.RAW_DIR, filename)
    processed_path = os.path.join(config.PROCESSED_DIR, filename)
    file_path = None
    if os.path.exists(raw_path):
        file_path = raw_path
    elif os.path.exists(processed_path):
        file_path = processed_path
    if file_path:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return render_template('view_file.html', filename=filename, content=content)
        except Exception as e:
            return jsonify({'error': f'Failed to read file: {str(e)}'}), 500
    return jsonify({'error': 'File not found'}), 404



@app.route('/index/build', methods=['POST'])
def build_index():
    """Build/refresh index with Nexus"""
    try:
        result = nexus.build_index(config.PROCESSED_DIR)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'reason': str(e)}), 500


@app.route('/search')
def search_page():
    """Search & explore page"""
    return render_template('search.html')


@app.route('/api/search', methods=['POST'])
def api_search():
    """Search API with Oracle"""
    data = request.get_json() or {}
    query = data.get('query', '')
    
    if not query:
        return jsonify({'success': False, 'reason': 'No query provided'}), 400
    
    filters = {}
    if data.get('level'):
        filters['level'] = data['level']
    if data.get('service'):
        filters['service'] = data['service']
    if data.get('time_from'):
        filters['time_from'] = data['time_from']
    if data.get('time_to'):
        filters['time_to'] = data['time_to']
    
    top_n = data.get('top_n', config.SEARCH_RESULT_LIMIT)
    
    result = oracle.search(query, top_n=top_n, filters=filters if filters else None)
    return jsonify(result)


@app.route('/insights')
def insights_page():
    """Insights & recommendations page"""
    return render_template('insights.html')


@app.route('/api/insights')
def api_insights():
    """Insights API with Cipher"""
    try:
        insights = cipher.compute_insights()
        return jsonify(insights)
    except Exception as e:
        return jsonify({'success': False, 'reason': str(e)}), 500


@app.route('/dashboard')
def dashboard():
    """Dashboard page"""
    return render_template('dashboard.html')


@app.route('/api/dashboard')
def api_dashboard():
    """Dashboard data API with Prism"""
    try:
        data = prism.get_dashboard_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/api/files')
def api_files():
    """Get list of all tracked files"""
    try:
        files = ledger.list_files()
        return jsonify({'files': files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/index/status')
def api_index_status():
    """Get index build status"""
    try:
        index_meta = ledger.get_latest_index_meta()
        exists = index_meta is not None
        last_build = index_meta.get('build_time') if index_meta else None
        return jsonify({
            'exists': exists,
            'last_build': last_build,
            'doc_count': index_meta.get('doc_count', 0) if index_meta else 0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/agents')
def api_agents():
    """Agent activity API"""
    try:
        activity = prism.get_agent_activity()
        return jsonify(activity)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def process_file(filename, file_bytes, validation):
    """Process uploaded file based on type"""
    file_type = validation['type']
    
    # Handle ZIP files
    if file_type == 'zip':
        extracted = utils.extract_zip(file_bytes)
        all_events = []
        for extracted_file in extracted:
            sub_validation = validate_file(extracted_file['filename'], extracted_file['content'])
            if sub_validation['valid']:
                sub_events = process_file(
                    extracted_file['filename'],
                    extracted_file['content'],
                    sub_validation
                )
                all_events.extend(sub_events)
        return all_events
    
    # Parse based on type
    if file_type == 'json':
        events = utils.parse_json_logs(file_bytes, filename)
    elif file_type == 'csv':
        events = utils.parse_csv_logs(file_bytes, filename)
    else:  # txt, log
        events = utils.parse_plain_logs(file_bytes, filename)
    
    # Filter noise
    events = utils.filter_noise(events, config.NOISE_PATTERNS)
    
    # Apply sampling if needed
    if config.ENABLE_SAMPLING and len(events) > config.SAMPLING_THRESHOLD:
        import random
        events = random.sample(events, config.SAMPLING_THRESHOLD)
    
    return events


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.APP_PORT, debug=True)
