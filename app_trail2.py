from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = 'SkyZag_2026'  # Change this to a secure secret key
USERS_FILE = 'users.xlsx'
ADMIN_FILE = 'admin.xlsx'  # Separate admin file for real-world logic

# Ensure the Excel files exist
for file in [USERS_FILE, ADMIN_FILE]:
    if not os.path.isfile(file):
        if file == USERS_FILE:
            df = pd.DataFrame(columns=['username', 'password', 'email', 'phone', 'blue_tokens', 'green_tokens', 'member'])
        else:
            df = pd.DataFrame(columns=['username', 'password'])
        df.to_excel(file, index=False)

def read_data(file):
    df = pd.read_excel(file)
    df = df.fillna('')
    df = df.astype(str)
    df = df.apply(lambda col: col.str.strip() if col.dtype == 'object' else col)
    return df

def write_data(df, file):
    df.to_excel(file, index=False)

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('index1.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip().lower()
        password = request.form['password'].strip().lower()
        
        # Check in admin file first
        df_admin = read_data(ADMIN_FILE)
        user_admin = df_admin[(df_admin['username'] == username) & (df_admin['password'] == password)]
        
        if user_admin.empty:
            # Check in users file
            df_users = read_data(USERS_FILE)
            user_users = df_users[(df_users['username'] == username) & (df_users['password'] == password)]
            
            if user_users.empty:
                return "Invalid username or password!"
            else:
                session['username'] = username
                session['member'] = user_users.iloc[0]['member']  # Set member status
                return redirect(url_for('dashboard'))
        else:
            session['username'] = username
            session['member'] = user_admin.iloc[0]['member']  # Set member status
            return redirect(url_for('dashboard'))
    
    return render_template('login.html')


@app.route('/createuser', methods=['GET', 'POST'])
def createuser():
    if request.method == 'POST':
        username = request.form['username'].strip().lower()
        password = request.form['password'].strip().lower()
        email = request.form['email'].strip()
        phone = request.form['phone'].strip()

        df = read_data(USERS_FILE)
        if username in df['username'].values:
            return "Username already exists!"

        new_user = pd.DataFrame({
            'username': [username],
            'password': [password],
            'email': [email],
            'phone': [phone],
            'blue_tokens': [0],
            'green_tokens': [0],
            'member': [0]  # Non-user by default
        })

        df = pd.concat([df, new_user], ignore_index=True)
        write_data(df, USERS_FILE)

        return redirect(url_for('login'))
    
    return render_template('createuser.html')

@app.route('/dashboard')
def dashboard():
    # Check if user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Ensure 'member' is in the session
    member_status = session.get('member', None)
    
    if member_status is None:
        # Handle the case where 'member' is not set
        return "Member status is not available. Please log in again."

    # Proceed with the rest of the function
    return render_template('blue_dashboard.html', member_status=member_status)


@app.route('/admin_dashboard')
def admin_dashboard():
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    return render_template('admin_dashboard.html')

@app.route('/export_requested')
def export_requested():
    if 'username' not in session or session['role'] != 'admin':
        return "Unauthorized access!"
    
    df = read_data(USERS_FILE)
    requested_users = df[df['member'] == '0']  # Non-members (requested users)
    
    if not requested_users.empty:
        requested_users.to_excel('requested.xlsx', index=False)
    
    return "Requested users have been exported."

@app.route('/move_users', methods=['POST'])
def move_users():
    if 'username' not in session or session['role'] != 'admin':
        return "Unauthorized access!"
    
    requested_df = pd.read_excel('requested.xlsx')

    if requested_df.empty:
        return "No users to move."

    users_df = read_data(USERS_FILE)

    requested_df['member'] = 2  # Move requested users to green members
    users_df = pd.concat([users_df, requested_df], ignore_index=True)
    write_data(users_df, USERS_FILE)

    os.remove('requested.xlsx')
    return "Users have been moved to the main file."

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
