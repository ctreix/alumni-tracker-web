import os
import json
import pandas as pd
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_session import Session
from dotenv import load_dotenv
from functools import wraps

# Import models
from models import db, Alumni, LogPelacakan

# Import search engine and scorer
from search_engine import SerperSearchEngine
from scorer import AlumniScorer

# Load environment variables from .env file (for local development)
# On Render/production, env vars are set in the dashboard
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"[OK] Loaded .env from {env_path}")
else:
    print("[INFO] No .env file found, using system environment variables")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'tracer_study_secret_key_2024')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "alumni_new.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
Session(app)

# Admin credentials from environment
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'password123')

CSV_FILE = 'Alumni_2000-2025.csv'

# Initialize search engine and scorer
search_engine = None
scorer = None

def init_services():
    """Initialize search engine and scorer with API key"""
    global search_engine, scorer
    try:
        # Debug: Print all environment variables (mask sensitive values)
        api_key = os.environ.get('SERPER_API_KEY')
        print(f"[DEBUG] SERPER_API_KEY present: {bool(api_key)}")
        print(f"[DEBUG] SERPER_API_KEY length: {len(api_key) if api_key else 0}")
        
        if api_key:
            search_engine = SerperSearchEngine(api_key=api_key)
            scorer = AlumniScorer()
            print("[OK] Search engine and scorer initialized")
        else:
            print("[WARNING] SERPER_API_KEY not set. Search functionality disabled.")
            print(f"[DEBUG] Available env vars: {[k for k in os.environ.keys() if not k.startswith('_')][:10]}")
    except Exception as e:
        print(f"[ERROR] Failed to initialize services: {e}")


def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def init_db():
    """Initialize database and import CSV data"""
    with app.app_context():
        db.create_all()
        
        # Check if alumni table has data
        count = Alumni.query.count()
        if count > 0:
            print(f"[OK] Database already initialized with {count} alumni records")
            return
        
        # Import from CSV
        if os.path.exists(CSV_FILE):
            print(f"[INFO] Importing data from {CSV_FILE}...")
            try:
                df = pd.read_csv(CSV_FILE, low_memory=False)
                imported = 0
                skipped = 0
                seen_nims = set()
                
                for _, row in df.iterrows():
                    nim = str(row.get('NIM', '')).strip()
                    
                    # Skip if NIM is empty or already seen
                    if not nim or nim in seen_nims:
                        skipped += 1
                        continue
                    
                    seen_nims.add(nim)
                    
                    alumni = Alumni(
                        nim=nim,
                        nama_lulusan=str(row.get('Nama Lulusan', '')).strip(),
                        fakultas=str(row.get('Fakultas', '')).strip() if pd.notna(row.get('Fakultas')) else None,
                        program_studi=str(row.get('Program Studi', '')).strip() if pd.notna(row.get('Program Studi')) else None,
                        tahun_masuk=str(row.get('Tahun Masuk', '')).strip() if pd.notna(row.get('Tahun Masuk')) else None,
                        tanggal_lulus=str(row.get('Tanggal Lulus', '')).strip() if pd.notna(row.get('Tanggal Lulus')) else None,
                        status_pelacakan='Belum Dilacak',
                        confidence_score=0
                    )
                    db.session.add(alumni)
                    imported += 1
                    
                    # Commit in batches
                    if imported % 1000 == 0:
                        db.session.commit()
                        print(f"[INFO] Imported {imported} records...")
                
                db.session.commit()
                print(f"[OK] Successfully imported {imported} alumni records (skipped {skipped} duplicates)")
            except Exception as e:
                db.session.rollback()
                print(f"[ERROR] Failed to import CSV: {e}")
        else:
            print(f"[WARNING] CSV file {CSV_FILE} not found")


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        error = 'Username atau password salah!'
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    """Main dashboard with search and filter"""
    search_query = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Build query
    query = Alumni.query
    
    if search_query:
        search_pattern = f'%{search_query}%'
        query = query.filter(
            db.or_(
                Alumni.nama_lulusan.ilike(search_pattern),
                Alumni.nim.ilike(search_pattern)
            )
        )
    
    if status_filter:
        query = query.filter(Alumni.status_pelacakan == status_filter)
    
    # Paginate results
    pagination = query.order_by(Alumni.nama_lulusan).paginate(
        page=page, per_page=per_page, error_out=False
    )
    alumni_list = pagination.items
    
    # Get status counts for filter dropdown
    status_counts = db.session.query(
        Alumni.status_pelacakan,
        db.func.count(Alumni.id)
    ).group_by(Alumni.status_pelacakan).all()
    
    return render_template('index.html', 
                         alumni=alumni_list,
                         pagination=pagination,
                         query=search_query,
                         status_filter=status_filter,
                         status_counts=status_counts,
                         search_engine_available=search_engine is not None)


@app.route('/track/<int:alumni_id>', methods=['POST'])
@login_required
def track_alumni(alumni_id):
    """Execute API search and scoring for an alumni"""
    if not search_engine or not scorer:
        flash('Search engine not configured. Please set SERPER_API_KEY.', 'error')
        return redirect(url_for('index'))
    
    alumni = Alumni.query.get_or_404(alumni_id)
    
    try:
        # Execute search
        search_results = search_engine.search_alumni(
            nama=alumni.nama_lulusan,
            prodi=alumni.program_studi or ''
        )
        
        # Calculate confidence score
        scoring_result = scorer.calculate_confidence(
            nama=alumni.nama_lulusan,
            prodi=alumni.program_studi or '',
            serper_results=search_results['search_results']
        )
        
        # Update alumni data
        alumni.confidence_score = scoring_result['confidence_score']
        alumni.status_pelacakan = scoring_result['status']
        alumni.updated_at = datetime.utcnow()
        
        # Extract and update profile data - collect from ALL results to maximize data capture
        # Even if confidence score is medium, we can still extract useful info from multiple sources
        if scoring_result['all_scored_results']:
            # Use the new method to extract from ALL search results, not just the best one
            profile_data = scorer.extract_data_from_all_results(scoring_result['all_scored_results'])
            
            # Update all social media and contact fields
            if profile_data.get('linkedin'):
                alumni.linkedin = profile_data['linkedin']
            if profile_data.get('instagram'):
                alumni.instagram = profile_data['instagram']
            if profile_data.get('facebook'):
                alumni.facebook = profile_data['facebook']
            if profile_data.get('twitter_x'):
                alumni.twitter_x = profile_data['twitter_x']
            if profile_data.get('tiktok'):
                alumni.tiktok = profile_data['tiktok']
            if profile_data.get('website_personal'):
                alumni.website_personal = profile_data['website_personal']
            if profile_data.get('email'):
                alumni.email = profile_data['email']
            if profile_data.get('no_hp'):
                alumni.no_hp = profile_data['no_hp']
            if profile_data.get('tempat_kerja'):
                alumni.tempat_kerja = profile_data['tempat_kerja']
            if profile_data.get('alamat_kerja'):
                alumni.alamat_kerja = profile_data['alamat_kerja']
            if profile_data.get('posisi'):
                alumni.posisi = profile_data['posisi']
            if profile_data.get('kategori'):
                alumni.kategori = profile_data['kategori']
            if profile_data.get('sosmed_kantor'):
                alumni.sosmed_kantor = profile_data['sosmed_kantor']
        
        # Create log entry
        matched = scoring_result.get('matched_result', {})
        log = LogPelacakan(
            alumni_id=alumni.id,
            nim=alumni.nim,
            query_dipakai=json.dumps(search_results['queries_used']),
            raw_json_response=json.dumps(search_results),
            confidence_score=scoring_result['confidence_score'],
            status_hasil=scoring_result['status'],
            snippet_bukti=matched.get('snippet', ''),
            url_sumber=matched.get('link', ''),
            title_sumber=matched.get('title', '')
        )
        db.session.add(log)
        db.session.commit()
        
        # Build success message with extracted data summary
        extracted_fields = []
        if profile_data.get('linkedin'): extracted_fields.append('LinkedIn')
        if profile_data.get('tempat_kerja'): extracted_fields.append('Perusahaan')
        if profile_data.get('posisi'): extracted_fields.append('Posisi')
        if profile_data.get('email'): extracted_fields.append('Email')
        if profile_data.get('no_hp'): extracted_fields.append('No.HP')
        
        extra_info = f" | Data: {', '.join(extracted_fields)}" if extracted_fields else ""
        flash(f'Pelacakan selesai! Skor: {scoring_result["confidence_score"]} - {scoring_result["status"]}{extra_info}', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error saat pelacakan: {str(e)}', 'error')
    
    # Redirect back to the same page
    return redirect(request.referrer or url_for('index'))


@app.route('/review/<int:alumni_id>')
@login_required
def review_alumni(alumni_id):
    """Review panel for alumni with score 50-79"""
    alumni = Alumni.query.get_or_404(alumni_id)
    
    # Get latest log for this alumni
    latest_log = LogPelacakan.query.filter_by(alumni_id=alumni_id).order_by(
        LogPelacakan.timestamp.desc()
    ).first()
    
    # Get all scored results from the raw response
    all_results = []
    if latest_log and latest_log.raw_json_response:
        try:
            raw_data = json.loads(latest_log.raw_json_response)
            # Re-run scoring to get detailed breakdown
            for result_group in raw_data.get('search_results', []):
                for result in result_group.get('extracted_results', []):
                    score, analysis = scorer._score_single_result(
                        alumni.nama_lulusan,
                        alumni.program_studi or '',
                        result
                    ) if scorer else (0, {})
                    all_results.append({
                        'title': result.get('title', ''),
                        'snippet': result.get('snippet', ''),
                        'link': result.get('link', ''),
                        'score': score,
                        'analysis': analysis
                    })
            all_results.sort(key=lambda x: x['score'], reverse=True)
        except:
            pass
    
    return render_template('review.html',
                         alumni=alumni,
                         log=latest_log,
                         all_results=all_results[:10])


@app.route('/verify/<int:alumni_id>', methods=['POST'])
@login_required
def verify_alumni(alumni_id):
    """Manual verification by admin with all social media fields"""
    alumni = Alumni.query.get_or_404(alumni_id)
    
    action = request.form.get('action')
    
    # Get all social media and profile fields from form
    fields = {
        'linkedin': request.form.get('linkedin', '').strip(),
        'instagram': request.form.get('instagram', '').strip(),
        'facebook': request.form.get('facebook', '').strip(),
        'twitter_x': request.form.get('twitter_x', '').strip(),
        'tiktok': request.form.get('tiktok', '').strip(),
        'website_personal': request.form.get('website_personal', '').strip(),
        'email': request.form.get('email', '').strip(),
        'no_hp': request.form.get('no_hp', '').strip(),
        'tempat_kerja': request.form.get('tempat_kerja', '').strip(),
        'alamat_kerja': request.form.get('alamat_kerja', '').strip(),
        'posisi': request.form.get('posisi', '').strip(),
        'kategori': request.form.get('kategori', '').strip(),
        'sosmed_kantor': request.form.get('sosmed_kantor', '').strip(),
    }
    catatan = request.form.get('catatan', '').strip()
    
    if action == 'approve':
        alumni.status_pelacakan = 'Terverifikasi Manual'
        alumni.confidence_score = max(alumni.confidence_score, 85)
        flash('Data alumni telah diverifikasi dan disetujui.', 'success')
    elif action == 'reject':
        alumni.status_pelacakan = 'Tidak Ditemukan'
        alumni.confidence_score = 0
        flash('Data alumni ditandai sebagai tidak ditemukan.', 'warning')
    
    # Update all profile data from manual input
    for field, value in fields.items():
        if value:
            setattr(alumni, field, value)
    
    # Add verification log
    log = LogPelacakan(
        alumni_id=alumni.id,
        nim=alumni.nim,
        query_dipakai='VERIFIKASI_MANUAL',
        confidence_score=alumni.confidence_score,
        status_hasil=alumni.status_pelacakan,
        snippet_bukti=catatan
    )
    db.session.add(log)
    db.session.commit()
    
    return redirect(url_for('index'))


@app.route('/reset/<int:alumni_id>', methods=['POST'])
@login_required
def reset_alumni(alumni_id):
    """Reset all tracked data for an alumni to allow re-tracking"""
    alumni = Alumni.query.get_or_404(alumni_id)
    
    try:
        # Reset all profile fields
        alumni.linkedin = ''
        alumni.instagram = ''
        alumni.facebook = ''
        alumni.twitter_x = ''
        alumni.tiktok = ''
        alumni.website_personal = ''
        alumni.email = ''
        alumni.no_hp = ''
        alumni.tempat_kerja = ''
        alumni.alamat_kerja = ''
        alumni.posisi = ''
        alumni.kategori = ''
        alumni.sosmed_kantor = ''
        alumni.confidence_score = 0
        alumni.status_pelacakan = 'Belum Dilacak'
        alumni.updated_at = datetime.utcnow()
        
        # Delete all tracking logs for this alumni
        LogPelacakan.query.filter_by(alumni_id=alumni_id).delete()
        
        db.session.commit()
        flash(f'Data tracking untuk {alumni.nama_lulusan} telah direset. Siap untuk dilacak ulang.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error saat reset: {str(e)}', 'error')
    
    return redirect(request.referrer or url_for('index'))


@app.route('/api/stats')
@login_required
def api_stats():
    """API endpoint for dashboard statistics"""
    total = Alumni.query.count()
    tracked = Alumni.query.filter(Alumni.status_pelacakan != 'Belum Dilacak').count()
    strong = Alumni.query.filter(Alumni.status_pelacakan == 'Teridentifikasi Kuat').count()
    verify = Alumni.query.filter(Alumni.status_pelacakan == 'Perlu Verifikasi').count()
    
    return jsonify({
        'total_alumni': total,
        'tracked': tracked,
        'strong_matches': strong,
        'needs_verification': verify,
        'tracking_rate': round(tracked / total * 100, 2) if total > 0 else 0
    })


@app.route('/health')
def health_check():
    """Health check endpoint - also verifies environment variables"""
    api_key_present = bool(os.environ.get('SERPER_API_KEY'))
    secret_key_present = bool(os.environ.get('FLASK_SECRET_KEY'))
    
    return jsonify({
        'status': 'ok',
        'database': 'connected',
        'serper_api_key': 'configured' if api_key_present else 'missing',
        'flask_secret_key': 'configured' if secret_key_present else 'missing',
        'search_engine_initialized': search_engine is not None,
        'message': 'All systems operational' if api_key_present else 'SERPER_API_KEY not configured'
    })


if __name__ == '__main__':
    init_services()
    init_db()
    app.run(debug=True)