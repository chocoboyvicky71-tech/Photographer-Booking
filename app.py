from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid
import os
import json  # Added to handle saving to a file

app = Flask(__name__)
app.secret_key = os.urandom(24) 

# ==========================================
# PHASE 1: LOCAL FILE DATABASE
# This replaces DynamoDB for local testing.
# Data is saved to 'local_database.json'
# ==========================================
DB_FILE = 'local_database.json'

def load_data():
    """Reads the database file. If it doesn't exist, creates an empty structure."""
    if not os.path.exists(DB_FILE):
        return {"users": {}, "bookings": {}}
    with open(DB_FILE, 'r') as file:
        return json.load(file)

def save_data(data):
    """Saves the dictionary back to the JSON file."""
    with open(DB_FILE, 'w') as file:
        json.dump(data, file, indent=4)

# ==========================================
# ROUTES
# ==========================================

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('home'))
    return render_template('index.html')

@app.route('/home')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('home.html', fullname=session.get('fullname'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Load data from the local file
        db = load_data()
        user = db['users'].get(username)

        if user and check_password_hash(user['password'], password):
            session['username'] = username
            session['fullname'] = user['fullname']
            flash('Login successful!', 'success')
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'username' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        fullname = request.form.get('fullname')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Load current data
        db = load_data()

        # Check if username exists
        if username in db['users']:
            flash('Username already exists!', 'error')
            return redirect(url_for('signup'))

        # Add new user to the dictionary
        db['users'][username] = {
            'username': username,
            'password': generate_password_hash(password),
            'fullname': fullname,
            'email': email,
            'created_at': datetime.now().isoformat()
        }
        
        # Save the updated dictionary back to the file
        save_data(db)
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if 'username' not in session:
        flash('Please login to make a booking.', 'error')
        return redirect(url_for('login', next=request.url))

    event_type = request.args.get('event', 'General')

    if request.method == 'POST':
        try:
            booking_date = request.form.get('date')
            booking_time = request.form.get('time')
            details = request.form.get('details')
            
            booking_id = str(uuid.uuid4())

            # Load current data
            db = load_data()

            # Add new booking
            db['bookings'][booking_id] = {
                'booking_id': booking_id,
                'username': session['username'],
                'event_type': event_type,
                'date': booking_date,
                'time': booking_time,
                'details': details,
                'status': 'Confirmed',
                'created_at': datetime.now().isoformat()
            }

            # Save the updated dictionary back to the file
            save_data(db)

            session['last_booking_id'] = booking_id
            return redirect(url_for('success'))

        except Exception as e:
            print(f"Error in booking form: {str(e)}")
            flash(f'An error occurred: {str(e)}', 'error')
            return redirect(url_for('booking', event=event_type))

    return render_template('booking.html', event_type=event_type)

@app.route('/success', methods=['GET', 'POST'])
def success():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('success.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/photographers')
def photographers():
    return render_template('photographers.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)