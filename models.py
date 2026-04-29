from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Alumni(db.Model):
    __tablename__ = 'alumni'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nim = db.Column(db.String(20), unique=True, nullable=False, index=True)
    nama_lulusan = db.Column(db.String(255), nullable=False)
    fakultas = db.Column(db.String(100), nullable=True)
    program_studi = db.Column(db.String(100), nullable=True)
    tahun_masuk = db.Column(db.String(10), nullable=True)
    tanggal_lulus = db.Column(db.String(50), nullable=True)
    
    # Status pelacakan
    status_pelacakan = db.Column(db.String(50), default='Belum Dilacak')
    confidence_score = db.Column(db.Integer, default=0)
    
    # 8 field hasil akhir profiling
    linkedin = db.Column(db.String(500), default='')
    email = db.Column(db.String(255), default='')
    no_hp = db.Column(db.String(50), default='')
    tempat_kerja = db.Column(db.String(255), default='')
    alamat_kerja = db.Column(db.Text, default='')
    posisi = db.Column(db.String(255), default='')
    kategori = db.Column(db.String(100), default='')
    sosmed_kantor = db.Column(db.String(500), default='')
    
    # Extended social media fields
    instagram = db.Column(db.String(500), default='')
    facebook = db.Column(db.String(500), default='')
    twitter_x = db.Column(db.String(500), default='')  # Twitter/X
    tiktok = db.Column(db.String(500), default='')
    website_personal = db.Column(db.String(500), default='')  # About.me, portfolio, blog
    
    # Relasi ke log pelacakan
    logs = db.relationship('LogPelacakan', backref='alumni', lazy=True, cascade='all, delete-orphan')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nim': self.nim,
            'nama_lulusan': self.nama_lulusan,
            'fakultas': self.fakultas or '-',
            'program_studi': self.program_studi or '-',
            'tahun_masuk': self.tahun_masuk or '-',
            'tanggal_lulus': self.tanggal_lulus or '-',
            'status_pelacakan': self.status_pelacakan,
            'confidence_score': self.confidence_score,
            'linkedin': self.linkedin or 'Belum diisi',
            'email': self.email or 'Belum diisi',
            'no_hp': self.no_hp or 'Belum diisi',
            'tempat_kerja': self.tempat_kerja or 'Belum diisi',
            'alamat_kerja': self.alamat_kerja or 'Belum diisi',
            'posisi': self.posisi or 'Belum diisi',
            'kategori': self.kategori or 'Belum diisi',
            'sosmed_kantor': self.sosmed_kantor or 'Belum diisi',
            'instagram': self.instagram or 'Belum diisi',
            'facebook': self.facebook or 'Belum diisi',
            'twitter_x': self.twitter_x or 'Belum diisi',
            'tiktok': self.tiktok or 'Belum diisi',
            'website_personal': self.website_personal or 'Belum diisi',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else '-',
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else '-'
        }


class LogPelacakan(db.Model):
    __tablename__ = 'log_pelacakan'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    alumni_id = db.Column(db.Integer, db.ForeignKey('alumni.id'), nullable=False, index=True)
    nim = db.Column(db.String(20), nullable=False, index=True)
    
    # Query yang digunakan
    query_dipakai = db.Column(db.Text, nullable=False)
    
    # Raw response dari Serper API
    raw_json_response = db.Column(db.Text, nullable=True)
    
    # Confidence score hasil scoring
    confidence_score = db.Column(db.Integer, default=0)
    
    # Status hasil
    status_hasil = db.Column(db.String(50), default='Pending')
    
    # Jejak bukti untuk review
    snippet_bukti = db.Column(db.Text, default='')
    url_sumber = db.Column(db.String(500), default='')
    title_sumber = db.Column(db.String(500), default='')
    
    # Timestamp
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'alumni_id': self.alumni_id,
            'nim': self.nim,
            'query_dipakai': self.query_dipakai,
            'confidence_score': self.confidence_score,
            'status_hasil': self.status_hasil,
            'snippet_bukti': self.snippet_bukti,
            'url_sumber': self.url_sumber,
            'title_sumber': self.title_sumber,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S') if self.timestamp else '-'
        }
