from flask import Flask, render_template, request, redirect, url_for, session
import csv
import os

app = Flask(__name__)
app.secret_key = 'rahasia_admin_kampus_123'

ADMIN_USERNAME = 'admin_kampus'
ADMIN_PASSWORD = 'password123'

MASTER_ALUMNI = []

def load_csv_data():
    file_path = 'Alumni_2000-2025.csv'
    if os.path.exists(file_path):
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for idx, row in enumerate(reader):
                MASTER_ALUMNI.append({
                    "id": idx + 1,
                    "nama": row.get('Nama Lulusan', '').strip(),
                    "nim": row.get('NIM', ''),
                    "prodi": row.get('Program Studi', ''),
                    "tahun_lulus": row.get('Tanggal Lulus', ''),
                    "sosmed": "LinkedIn: link.id/in, IG: @user, FB: user.fb, TikTok: @user",
                    "email": f"{row.get('NIM', 'user')}@student.mail.ac.id",
                    "no_hp": "0812-xxxx-xxxx",
                    "tempat_kerja": "PT. Contoh Perusahaan",
                    "alamat_kerja": "Jl. Contoh No. 1, Malang",
                    "posisi": "Staff Placeholder",
                    "kategori_pekerjaan": "Swasta",
                    "sosmed_kantor": "@akun_kantor"
                })

load_csv_data()

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USERNAME and request.form['password'] == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        error = 'Kredensial salah!'
    return render_template('login.html', error=error)

@app.route('/', methods=['GET'])
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    search_query = request.args.get('q', '').lower()
    results = []
    
    if search_query:
        results = [
            a for a in MASTER_ALUMNI 
            if search_query in a['nama'].lower() or search_query in a['nim']
        ]
        
    return render_template('index.html', alumni=results, query=search_query)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)