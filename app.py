from flask import Flask, render_template, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import re
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')

# ── Database configuration ──
database_url = os.environ.get('DATABASE_URL', 'sqlite:///database.db')

# Render provides postgres:// but SQLAlchemy requires postgresql://
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ── Models (database tables) ──

class Appointment(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(120), nullable=False)
    phone      = db.Column(db.String(20),  nullable=False)
    services   = db.Column(db.Text,        nullable=False)
    party_size = db.Column(db.Integer,     nullable=False, default=1)
    estimated_total = db.Column(db.String(20),   nullable=True)
    date       = db.Column(db.String(20),  nullable=False)
    time       = db.Column(db.String(20),  nullable=False)
    technician = db.Column(db.String(100), nullable=True)
    details    = db.Column(db.Text,        nullable=True)
    created_at = db.Column(db.DateTime,    default=datetime.utcnow)

    def __repr__(self):
        return f'<Appointment {self.name} on {self.date} at {self.time}>'


class ContactMessage(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(120), nullable=False)
    phone      = db.Column(db.String(20),  nullable=True)
    message    = db.Column(db.Text,        nullable=False)
    created_at = db.Column(db.DateTime,    default=datetime.utcnow)

    def __repr__(self):
        return f'<Message from {self.name}>'

# ── Services data ── 
# Edit this list to update pricing of services on website
# TO-DO: Add more services from other menu
services = [
    {
        'category': 'Manicure Services',
        'services': [
            { 'name': 'Basic Manicure',                 'price': '25',  'price_note': '' },
            { 'name': 'Luxury Manicure',                'price': '40',  'price_note': '' },
            { 'name': 'Gel Polish Manicure',            'price': '35',  'price_note': '' },
            { 'name': 'Gel French Manicure',            'price': '40',  'price_note': '' },
        ]
    },
    {
        'category': 'Pedicure Services',
        'services': [
            { 'name': 'Basic Pedicure',                 'price': '35',  'price_note': '' },
            { 'name': 'Signature Pedicure',             'price': '45',  'price_note': '' },
            { 'name': 'Deluxe Pedicure',                'price': '50',  'price_note': '' },
            { 'name': 'Luxury Pedicure',                'price': '60',  'price_note': '' },
        ]
    },
    {
        'category': 'Manicure & Pedicure Combos',
        'services': [
            { 'name': 'Basic Manicure-Pedicure',        'price': '55',  'price_note': '' },
            { 'name': 'Signature Manicure-Pedicure',    'price': '70',  'price_note': '' },
            { 'name': 'Deluxe Manicure-Pedicure',       'price': '80',  'price_note': '' },
        ]
    },
    {
        'category': 'Dipping Services',
        'services': [
            { 'name': 'Dipping Color',                  'price': '45',  'price_note': '+' },
            { 'name': 'Dipping Color Add Tip',          'price': '55',  'price_note': '+' },
            { 'name': 'Dipping French',                 'price': '50',  'price_note': '+' },
            { 'name': 'Dipping French Add Tip',         'price': '55',  'price_note': '+' },
        ]
    },
    {
        'category': 'Nail Enhancement — Acrylic',
        'services': [
            { 'name': 'Full Set with Gel Color',        'price': '55',  'price_note': '+' },
            { 'name': 'Fill Set with French Tip',       'price': '60',  'price_note': '+' },
            { 'name': 'Fill-In No Polish',              'price': '35',  'price_note': '+' },
            { 'name': 'Fill-In with French Tip',        'price': '50',  'price_note': '+' },
            { 'name': 'Fill-In with Gel Color',         'price': '45',  'price_note': '+' },
        ]
    },
    {
        'category': 'Nail Enhancement — Pink & White / Poly Gel',
        'services': [
            { 'name': 'Pink & White Full Set',          'price': '60',  'price_note': '+' },
            { 'name': 'Pink & White Fill-In',           'price': '55',  'price_note': '+' },
            { 'name': 'Poly Gel Full Set',              'price': '55',  'price_note': '+' },
            { 'name': 'Poly Gel Fill-In with Color',    'price': '45',  'price_note': '+' },
            { 'name': 'Poly Gel Fill-In with French Tip', 'price': '50', 'price_note': '+' },
        ]
    },
    {
        'category': 'Nail Enhancement — Ombre & Builder Gel',
        'services': [
            { 'name': 'Ombre Full Set',                 'price': '70',  'price_note': '+' },
            { 'name': 'Ombre Fill-In',                  'price': '70',  'price_note': '+' },
            { 'name': 'Builder Gel Full Set',           'price': '60',  'price_note': '+' },
            { 'name': 'Builder Gel Fill-In',            'price': '55',  'price_note': '+' },
        ]
    },
    {
        'category': 'Polish Change',
        'services': [
            { 'name': 'Regular Polish Change',          'price': '15',  'price_note': '' },
            { 'name': 'Gel Color Change',               'price': '25',  'price_note': '' },
            { 'name': 'Gel French Tip Change',          'price': '30',  'price_note': '' },
        ]
    },
    {
        'category': 'Add-On Services',
        'services': [
            { 'name': 'Cat Eyes',                       'price': '10',  'price_note': '' },
            { 'name': 'Chrome',                         'price': '15',  'price_note': '+' },
            { 'name': 'Design',                         'price': '10',  'price_note': '+' },
            { 'name': 'Soak-Off Without Service',       'price': '25',  'price_note': '+' },
        ]
    },
    {
        'category': 'Kid Services (Ages 10 & Under)',
        'services': [
            { 'name': 'Kids Regular Manicure',          'price': '15',  'price_note': '' },
            { 'name': 'Kids Gel Manicure',              'price': '25',  'price_note': '' },
            { 'name': 'Kids Polish Hands & Toes',       'price': '15',  'price_note': '' },
        ]
    },
    {
        'category': 'Waxing Services',
        'services': [
            { 'name': 'Eyebrows',                       'price': '15',  'price_note': '' },
            { 'name': 'Lip',                            'price': '8',   'price_note': '' },
            { 'name': 'Chin',                           'price': '10',  'price_note': '' },
            { 'name': 'Full Face',                      'price': '35',  'price_note': '' },
        ]
    },
]

# Flat list of service names for the booking form dropdown
service_names = [item['name'] for section in services for item in section['services']]

# ── Gallery data ── 
# Update this with pictures for viewing in the gallery
# TO-DO: Replace placeholders with real imagery
gallery = [
    {
        'filename': '/static/images/gallery/sunny1.jpg',
        'caption': 'Classic French Manicure',
        'category': 'Manicure'
    },
    {
        'filename': '/static/images/gallery/sunny2.jpg',
        'caption': 'Gel Color Set',
        'category': 'Gel'
    },
    {
        'filename': '/static/images/gallery/sunny3.jpg',
        'caption': 'Spa Pedicure',
        'category': 'Pedicure'
    },
    {
        'filename': '/static/images/gallery/sunny4.jpg',
        'caption': 'Acrylic Full Set',
        'category': 'Acrylic'
    },
    {
        'filename': '/static/images/gallery/sunny5.jpg',
        'caption': 'Nail Art Design',
        'category': 'Nail Art'
    },
    {
        'filename': '/static/images/gallery/sunny6.jpg',
        'caption': 'Pink Ombre Gel',
        'category': 'Gel'
    },
    {
        'filename': '/static/images/gallery/sunny7.jpg',
        'caption': 'Summer Pedicure',
        'category': 'Pedicure'
    },
    {
        'filename': '/static/images/gallery/sunny8.jpg',
        'caption': 'Chrome Powder Nails',
        'category': 'Nail Art'
    },
    {
        'filename': '/static/images/gallery/sunny9.jpg',
        'caption': 'Acrylic with Glitter',
        'category': 'Acrylic'
    },
]

# ── Helpers ──

def normalize_phone(raw):
    digits = re.sub(r'\D', '', raw)
    if len(digits) == 10:
        return f'({digits[:3]}) {digits[3:6]}-{digits[6:]}'
    elif len(digits) == 11 and digits[0] == '1':
        return f'({digits[1:4]}) {digits[4:7]}-{digits[7:]}'
    else:
        return raw.strip()
    
# ── Routes ──

@app.route('/')
def home():
    #return 'Welcome to Pretty Nail Spa!'
    return render_template('index.html', salon_name='Pretty Nail Spa')

@app.route('/services')
def services_page():
    return render_template('services.html', services=services)

@app.route('/gallery')
def gallery_page():
    return render_template('gallery.html', gallery=gallery)

@app.route('/about-us')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        msg = ContactMessage(
            name    = request.form['customer_name'],
            email   = request.form['email'],
            phone   = normalize_phone(request.form['phone']),
            message = request.form['message']
        )
        db.session.add(msg)
        db.session.commit()
        flash(f"Thank you {msg.name}! We'll be in touch soon.")
        return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if request.method == 'POST':
        selected_services = request.form.getlist('services')

        if not selected_services:
            flash('Please select at least one service.')
            return redirect(url_for('booking'))
        
        phone = normalize_phone(request.form['phone'])

        appt = Appointment(
            name            = request.form['customer_name'],
            email           = request.form['email'],
            phone           = phone,
            services        = ', '.join(selected_services),
            party_size      = int(request.form['party_size']),
            estimated_total = request.form.get('estimated_total', ''),
            date            = request.form['date'],
            time            = request.form['time'],
            technician      = request.form['technician'],
            details         = request.form['details']
        )
        db.session.add(appt)
        db.session.commit()

        party_note = f' for {appt.party_size} guests' if appt.party_size > 1 else ''
        flash(f"Thank you {appt.name}! Your appointment{party_note} on {appt.date} at {appt.time} has been submitted. We will reach out to confirm your appointment. Estimated total: {appt.estimated_total}.")
        return redirect(url_for('booking'))

    return render_template('booking.html', services=services)

# Create tables on startup
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)