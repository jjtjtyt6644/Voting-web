from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import hashlib
from functools import wraps

app = Flask(__name__)
app.secret_key = '4e1_voting_secret_key_2026'
DATABASE = 'un_voting.db'
ready_users = set()  # Track which users are ready
logged_in_users = set()  # Track currently logged-in users
proposal_submissions = {}  # Track proposal submissions by user_id
submission_votes = {}  # Format: {proposer_user_id: {'yes': X, 'no': Y, 'abstain': Z}}
users_finished_voting = set()  # Track users who have finished voting
tiebreaker_votes = {}  # Format: {proposer_user_id: {'yes': X, 'no': Y}}
users_finished_tiebreaker = set()  # Track users who have finished tie breaking
users_agreed_to_tiebreak = set()  # Track users who agreed to break tie
users_arrived_tiebreak = set()  # Track users who have loaded the tiebreaker page

# Room management
voting_rooms = {}  # Format: {room_code: {'name': str, 'passcode': str, 'created_by': user_id, 'users': set(), 'created_date': timestamp}}
user_rooms = {}  # Format: {user_id: room_code}

# Security decorator to require authentication
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# Security decorator for API endpoints
def api_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with app.app_context():
        db = get_db()
        db.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                position TEXT NOT NULL,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS proposals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                proposed_by TEXT NOT NULL,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            );
            
            CREATE TABLE IF NOT EXISTS votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proposal_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                vote TEXT NOT NULL,
                voted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(proposal_id) REFERENCES proposals(id),
                FOREIGN KEY(user_id) REFERENCES users(id),
                UNIQUE(proposal_id, user_id)
            );
        ''')
        db.commit()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/lobby')
@login_required
def lobby_page():
    # Reset voting state when entering lobby
    global ready_users, proposal_submissions, submission_votes, users_finished_voting
    # Don't clear ready_users if we're just refreshing
    # But clear voting state from previous round
    proposal_submissions.clear()
    submission_votes.clear()
    users_finished_voting.clear()
    # Determine user's current room (if any)
    user_id = session.get('user_id')
    room_code = None
    room_name = None
    if user_id in user_rooms:
        room_code = user_rooms.get(user_id)
        room = voting_rooms.get(room_code)
        if room:
            room_name = room.get('name')

    return render_template('lobby.html', user_name=session.get('user_name'), user_position=session.get('user_position'), user_id=session.get('user_id'), room_code=room_code, room_name=room_name)

@app.route('/room')
@login_required
def room_page():
    return render_template('room.html', user_name=session.get('user_name'), user_position=session.get('user_position'), user_id=session.get('user_id'))

@app.route('/voting')
@login_required
def voting_page():
    return render_template('voting.html', user_name=session.get('user_name'), user_position=session.get('user_position'), user_id=session.get('user_id'))

@app.route('/tiebreaker')
@login_required
def tiebreaker_page():
    return render_template('tiebreaker.html', user_name=session.get('user_name'), user_position=session.get('user_position'), user_id=session.get('user_id'))

@app.route('/results')
@login_required
def results_page():
    return render_template('results.html')

@app.route('/update')
def update_log_page():
    return render_template('update_log.html')

@app.route('/')
def home_page():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        data = request.json
        name = data.get('name')
        password = data.get('password')
        
        if not name or not password:
            return jsonify({'error': 'Name and password required'}), 400
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE name = ?', (name,)).fetchone()
        
        if user and user['password'] == hash_password(password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_position'] = user['position']
            # Add user to logged_in_users set
            logged_in_users.add(user['id'])
            return jsonify({'success': True, 'message': 'Logged in successfully'}), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('name')
    password = data.get('password')
    position = data.get('position')
    
    if not name or not password or not position:
        return jsonify({'error': 'All fields required'}), 400
    
    if len(password) < 4:
        return jsonify({'error': 'Password must be at least 4 characters'}), 400
    
    try:
        db = get_db()
        cursor = db.execute(
            'INSERT INTO users (name, password, position) VALUES (?, ?, ?)',
            (name, hash_password(password), position)
        )
        db.commit()
        
        user_id = cursor.lastrowid
        session['user_id'] = user_id
        session['user_name'] = name
        session['user_position'] = position
        # Add user to logged_in_users set
        logged_in_users.add(user_id)
        
        return jsonify({'success': True, 'message': 'Registered successfully'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username already exists'}), 400

# Room Management Routes
@app.route('/api/room/create', methods=['POST'])
@api_login_required
def create_room():
    import random
    import string
    from datetime import datetime
    
    data = request.json
    room_name = data.get('room_name', f"Room {random.randint(1000, 9999)}")
    passcode = data.get('passcode', '')
    
    user_id = session['user_id']
    
    # Generate unique room code
    room_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    # Create room
    voting_rooms[room_code] = {
        'name': room_name,
        'passcode': passcode,
        'created_by': user_id,
        'users': {user_id},
        'created_date': datetime.now().isoformat()
    }
    
    # Add user to room
    user_rooms[user_id] = room_code
    
    return jsonify({
        'success': True,
        'room_code': room_code,
        'room_name': room_name,
        'message': f'Room created successfully'
    }), 201

@app.route('/api/room/join', methods=['POST'])
@api_login_required
def join_room():
    data = request.json
    room_code = data.get('room_code', '').upper()
    passcode = data.get('passcode', '')
    
    user_id = session['user_id']
    
    # Check if room exists
    if room_code not in voting_rooms:
        return jsonify({'error': 'Room not found'}), 404
    
    room = voting_rooms[room_code]
    
    # Check passcode if room has one
    if room['passcode'] and room['passcode'] != passcode:
        return jsonify({'error': 'Invalid passcode'}), 401
    
    # Add user to room
    room['users'].add(user_id)
    user_rooms[user_id] = room_code
    
    return jsonify({
        'success': True,
        'room_code': room_code,
        'room_name': room['name'],
        'message': f'Joined room successfully'
    }), 200

@app.route('/api/room/current', methods=['GET'])
@api_login_required
def get_current_room():
    user_id = session['user_id']
    
    if user_id not in user_rooms:
        return jsonify({'error': 'User not in any room'}), 404
    
    room_code = user_rooms[user_id]
    room = voting_rooms[room_code]
    
    return jsonify({
        'room_code': room_code,
        'room_name': room['name'],
        'users_count': len(room['users']),
        'created_by': room['created_by'],
        'created_date': room['created_date']
    }), 200

@app.route('/api/room/info/<room_code>', methods=['GET'])
@api_login_required
def get_room_info(room_code):
    room_code = room_code.upper()
    
    if room_code not in voting_rooms:
        return jsonify({'error': 'Room not found'}), 404
    
    room = voting_rooms[room_code]
    
    return jsonify({
        'room_code': room_code,
        'room_name': room['name'],
        'users_count': len(room['users']),
        'has_passcode': bool(room['passcode']),
        'created_date': room['created_date']
    }), 200

@app.route('/api/room/leave', methods=['POST'])
@api_login_required
def leave_room():
    user_id = session['user_id']
    
    if user_id not in user_rooms:
        return jsonify({'error': 'User not in any room'}), 404
    
    room_code = user_rooms[user_id]
    room = voting_rooms[room_code]
    
    # Remove user from room
    room['users'].discard(user_id)
    del user_rooms[user_id]
    
    # Delete room if empty
    if not room['users']:
        del voting_rooms[room_code]
    
    return jsonify({'success': True, 'message': 'Left room successfully'}), 200

@app.route('/api/users', methods=['GET'])
@api_login_required
def get_users():
    user_id = session['user_id']
    
    # Check if user is in a room
    if user_id not in user_rooms:
        return jsonify({'error': 'User not in any room'}), 400
    
    room_code = user_rooms[user_id]
    room = voting_rooms.get(room_code)
    
    if not room:
        return jsonify({'error': 'Room not found'}), 404
    
    db = get_db()
    users = db.execute('SELECT id, name, position FROM users ORDER BY created_date').fetchall()
    
    # Only return users that are in the same room and currently logged in
    room_users = [
        {
            'id': dict(u)['id'],
            'name': dict(u)['name'],
            'position': dict(u)['position'],
            'ready': dict(u)['id'] in ready_users
        }
        for u in users
        if dict(u)['id'] in room['users'] and dict(u)['id'] in logged_in_users
    ]
    
    return jsonify(room_users)

@app.route('/api/users/<int:user_id>/ready', methods=['POST'])
@api_login_required
def mark_user_ready(user_id):
    if session['user_id'] != user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Add to global ready_users set
    ready_users.add(user_id)
    
    return jsonify({'success': True}), 200

@app.route('/api/ready-status', methods=['GET'])
@api_login_required
def get_ready_status():
    user_id = session['user_id']
    
    # Check if user is in a room
    if user_id not in user_rooms:
        return jsonify({'error': 'User not in any room'}), 400
    
    room_code = user_rooms[user_id]
    room = voting_rooms.get(room_code)
    
    if not room:
        return jsonify({'error': 'Room not found'}), 404
    
    # Count only users in the same room and logged in
    total_users = len(room['users'] & logged_in_users)
    ready_count = len(ready_users & room['users'] & logged_in_users)
    all_ready = ready_count == total_users and total_users > 0
    
    return jsonify({'ready': ready_count, 'total': total_users, 'all_ready': all_ready})

@app.route('/api/random-proposer', methods=['GET'])
@api_login_required
def get_random_proposer():
    import random
    db = get_db()
    users = db.execute('SELECT id, name FROM users').fetchall()
    
    if not users:
        return jsonify({'error': 'No users available'}), 404
    
    selected = random.choice(users)
    return jsonify({'user_id': selected['id'], 'user_name': selected['name']})

@app.route('/api/proposal-submission', methods=['POST'])
@api_login_required
def submit_proposal_data():
    data = request.json
    title = data.get('title')
    description = data.get('description')
    
    if not title or not description:
        return jsonify({'error': 'Title and description required'}), 400
    
    user_id = session['user_id']
    user_name = session['user_name']
    
    # Store proposal submission
    proposal_submissions[user_id] = {
        'title': title,
        'description': description,
        'user_name': user_name,
        'user_id': user_id
    }
    
    return jsonify({'success': True}), 201

@app.route('/api/all-proposals-submitted', methods=['GET'])
@api_login_required
def check_all_proposals():
    user_id = session['user_id']
    
    # Get current user's room
    if user_id not in user_rooms:
        return jsonify({'error': 'User not in any room'}), 400
    
    room_code = user_rooms[user_id]
    room = voting_rooms.get(room_code)
    
    if not room:
        return jsonify({'error': 'Room not found'}), 404
    
    # Count only users in the same room
    total_users = len(room['users'] & logged_in_users)
    submitted = len(proposal_submissions)
    
    return jsonify({'submitted': submitted, 'total': total_users, 'all_submitted': submitted == total_users})

@app.route('/api/proposals-to-vote', methods=['GET'])
@api_login_required
def get_proposals_to_vote():
    current_user_id = session.get('user_id')
    
    # Convert proposal_submissions to list, excluding own proposal, with randomized order
    proposals_list = [p for user_id, p in proposal_submissions.items() if user_id != current_user_id]
    
    import random
    random.shuffle(proposals_list)
    
    return jsonify(proposals_list)

@app.route('/logout')
def logout():
    user_id = session.get('user_id')
    # Clear user from all tracking sets for safe state management
    if user_id in logged_in_users:
        logged_in_users.discard(user_id)
    if user_id in ready_users:
        ready_users.discard(user_id)
    if user_id in users_finished_voting:
        users_finished_voting.discard(user_id)
    if user_id in users_finished_tiebreaker:
        users_finished_tiebreaker.discard(user_id)
    if user_id in users_agreed_to_tiebreak:
        users_agreed_to_tiebreak.discard(user_id)
    if user_id in users_arrived_tiebreak:
        users_arrived_tiebreak.discard(user_id)
    # Remove user from any room they are in
    try:
        if user_id in user_rooms:
            room_code = user_rooms.get(user_id)
            room = voting_rooms.get(room_code)
            if room:
                room['users'].discard(user_id)
                # delete room if empty
                if not room['users']:
                    del voting_rooms[room_code]
            del user_rooms[user_id]
    except Exception:
        pass
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/api/proposals', methods=['GET'])
@api_login_required
def get_proposals():
    db = get_db()
    proposals = db.execute('SELECT * FROM proposals ORDER BY created_date DESC').fetchall()
    return jsonify([dict(p) for p in proposals])

@app.route('/api/proposals', methods=['POST'])
@api_login_required
def create_proposal():
    data = request.json
    title = data.get('title')
    description = data.get('description')
    
    if not title or not description:
        return jsonify({'error': 'Title and description required'}), 400
    
    proposed_by = session.get('user_name')
    
    db = get_db()
    cursor = db.execute(
        'INSERT INTO proposals (title, description, proposed_by) VALUES (?, ?, ?)',
        (title, description, proposed_by)
    )
    db.commit()
    return jsonify({
        'id': cursor.lastrowid,
        'title': title,
        'description': description,
        'proposed_by': proposed_by
    }), 201

@app.route('/api/proposals/<int:proposal_id>/vote', methods=['POST'])
@api_login_required
def vote(proposal_id):
    data = request.json
    vote_choice = data.get('vote')
    password = data.get('password')
    
    # Verify password
    user_id = session.get('user_id')
    db = get_db()
    user = db.execute('SELECT password FROM users WHERE id = ?', (user_id,)).fetchone()
    
    if not user or user['password'] != hash_password(password):
        return jsonify({'error': 'Invalid password'}), 401
    
    if vote_choice not in ['yes', 'no', 'abstain']:
        return jsonify({'error': 'Invalid vote choice'}), 400
    
    try:
        db.execute(
            'INSERT INTO votes (proposal_id, user_id, vote) VALUES (?, ?, ?)',
            (proposal_id, user_id, vote_choice)
        )
        db.commit()
        return jsonify({'success': True}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'You have already voted on this proposal'}), 400

@app.route('/api/proposals/<int:proposal_id>/results', methods=['GET'])
@api_login_required
def get_results(proposal_id):
    db = get_db()
    
    votes = db.execute('''
        SELECT vote, COUNT(*) as count FROM votes 
        WHERE proposal_id = ? 
        GROUP BY vote
    ''', (proposal_id,)).fetchall()
    
    results = {'yes': 0, 'no': 0, 'abstain': 0, 'total_users': 0}
    for vote_record in votes:
        results[vote_record['vote']] = vote_record['count']
    
    total = db.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    results['total_users'] = total
    
    voted = db.execute('SELECT COUNT(*) FROM votes WHERE proposal_id = ?', (proposal_id,)).fetchone()[0]
    results['total_voted'] = voted
    
    return jsonify(results)

@app.route('/api/vote-on-submission/<int:proposer_user_id>', methods=['POST'])
@api_login_required
def vote_on_submission(proposer_user_id):
    data = request.json
    vote_choice = data.get('vote')
    password = data.get('password')
    user_id = session.get('user_id')
    
    # Verify password
    db = get_db()
    user = db.execute('SELECT password FROM users WHERE id = ?', (user_id,)).fetchone()
    
    if not user or user['password'] != hash_password(password):
        return jsonify({'error': 'Invalid password'}), 401
    
    if vote_choice not in ['yes', 'no', 'abstain']:
        return jsonify({'error': 'Invalid vote choice'}), 400
    
    # Initialize vote entry if needed
    if proposer_user_id not in submission_votes:
        submission_votes[proposer_user_id] = {'yes': 0, 'no': 0, 'abstain': 0, 'voters': set()}
    
    # Check if user already voted on this submission
    if user_id in submission_votes[proposer_user_id]['voters']:
        return jsonify({'error': 'You have already voted on this proposal'}), 400
    
    # Record the vote
    submission_votes[proposer_user_id][vote_choice] += 1
    submission_votes[proposer_user_id]['voters'].add(user_id)
    
    return jsonify({'success': True}), 201

@app.route('/api/submission-results/<int:proposer_user_id>', methods=['GET'])
@api_login_required
def get_submission_results(proposer_user_id):
    # Return vote counts for this submission
    if proposer_user_id in submission_votes:
        votes = submission_votes[proposer_user_id]
        return jsonify({
            'yes': votes['yes'],
            'no': votes['no'],
            'abstain': votes['abstain']
        })
    else:
        return jsonify({'yes': 0, 'no': 0, 'abstain': 0})

@app.route('/api/all-voting-results', methods=['GET'])
@api_login_required
def get_all_voting_results():
    """Return all proposals with their aggregated vote results"""
    results = []
    
    for proposer_user_id, proposal_data in proposal_submissions.items():
        votes = submission_votes.get(proposer_user_id, {'yes': 0, 'no': 0, 'abstain': 0})
        
        yes_count = votes['yes']
        no_count = votes['no']
        abstain_count = votes['abstain']
        total = yes_count + no_count + abstain_count
        
        # Calculate percentages
        yes_percent = round((yes_count / total) * 100) if total > 0 else 0
        no_percent = round((no_count / total) * 100) if total > 0 else 0
        abstain_percent = round((abstain_count / total) * 100) if total > 0 else 0
        
        # Determine pass/fail status
        passed = yes_count > no_count
        status = 'passed' if passed else ('failed' if no_count > yes_count else 'tied')
        
        results.append({
            'proposer_id': proposer_user_id,
            'title': proposal_data['title'],
            'description': proposal_data['description'],
            'proposed_by': proposal_data['user_name'],
            'yes': yes_count,
            'no': no_count,
            'abstain': abstain_count,
            'total_votes': total,
            'yes_percent': yes_percent,
            'no_percent': no_percent,
            'abstain_percent': abstain_percent,
            'status': status
        })
    
    # Sort by yes votes (most votes first)
    results.sort(key=lambda x: x['yes'], reverse=True)
    
    return jsonify(results)

@app.route('/api/mark-voting-complete', methods=['POST'])
@api_login_required
def mark_voting_complete():
    """Mark current user as finished voting"""
    user_id = session.get('user_id')
    users_finished_voting.add(user_id)
    return jsonify({'success': True}), 200

@app.route('/api/check-all-voted', methods=['GET'])
@api_login_required
def check_all_voted():
    """Check if all users have finished voting"""
    user_id = session['user_id']
    if user_id not in user_rooms:
        return jsonify({'error': 'User not in any room'}), 400
    
    room_code = user_rooms[user_id]
    room = voting_rooms.get(room_code)
    if not room:
        return jsonify({'error': 'Room not found'}), 404
    
    # Count only room members who are logged in
    total_users = len(room['users'] & logged_in_users)
    finished_users = len(users_finished_voting & room['users'])
    
    all_voted = finished_users == total_users and total_users > 0
    
    return jsonify({
        'all_voted': all_voted,
        'finished': finished_users,
        'total': total_users
    })

@app.route('/api/start-tiebreaker', methods=['POST'])
@api_login_required
def start_tiebreaker():
    """Initialize tiebreaker voting"""
    global tiebreaker_votes, users_finished_tiebreaker
    tiebreaker_votes.clear()
    users_finished_tiebreaker.clear()
    return jsonify({'success': True}), 200

@app.route('/api/reset-tiebreak-agreement', methods=['POST'])
@api_login_required
def reset_tiebreak_agreement():
    """Reset tiebreak agreement after all users loaded tiebreaker page"""
    global users_agreed_to_tiebreak
    users_agreed_to_tiebreak.clear()
    return jsonify({'success': True}), 200

@app.route('/api/agree-to-tiebreak', methods=['POST'])
@api_login_required
def agree_to_tiebreak():
    """User agrees to break tie"""
    user_id = session.get('user_id')
    users_agreed_to_tiebreak.add(user_id)
    return jsonify({'success': True}), 200

@app.route('/api/check-tiebreak-agreement', methods=['GET'])
@api_login_required
def check_tiebreak_agreement():
    """Check if all users agreed to break tie"""
    db = get_db()
    total_users = db.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    agreed_users = len(users_agreed_to_tiebreak)
    
    all_agreed = agreed_users == total_users and total_users > 0
    
    return jsonify({
        'all_agreed': all_agreed,
        'agreed': agreed_users,
        'total': total_users
    })

@app.route('/api/arrived-tiebreaker', methods=['POST'])
@api_login_required
def arrived_tiebreaker():
    """Mark that a user has loaded the tiebreaker page"""
    user_id = session.get('user_id')
    users_arrived_tiebreak.add(user_id)
    db = get_db()
    total_users = db.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    arrived = len(users_arrived_tiebreak)
    all_arrived = arrived == total_users and total_users > 0
    # If all arrived, initialize tiebreaker state and clear agreements
    if all_arrived:
        tiebreaker_votes.clear()
        users_finished_tiebreaker.clear()
        users_agreed_to_tiebreak.clear()
    return jsonify({'arrived': arrived, 'total': total_users, 'all_arrived': all_arrived}), 200

@app.route('/api/check-arrived', methods=['GET'])
@api_login_required
def check_arrived():
    """Check arrival counts for tiebreaker page"""
    db = get_db()
    total_users = db.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    arrived = len(users_arrived_tiebreak)
    all_arrived = arrived == total_users and total_users > 0
    # If all arrived, ensure tiebreaker is initialized
    if all_arrived:
        tiebreaker_votes.clear()
        users_finished_tiebreaker.clear()
        users_agreed_to_tiebreak.clear()
    return jsonify({'arrived': arrived, 'total': total_users, 'all_arrived': all_arrived}), 200

@app.route('/api/get-tied-proposals', methods=['GET'])
@api_login_required
def get_tied_proposals():
    """Get proposals that are tied"""
    db = get_db()
    total_users = db.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    
    tied_proposals = []
    
    for proposer_user_id, votes_data in submission_votes.items():
        yes_count = votes_data.get('yes', 0)
        no_count = votes_data.get('no', 0)
        abstain_count = votes_data.get('abstain', 0)
        
        # Determine if tied (yes and no are equal, abstain doesn't count towards pass/fail)
        if yes_count == no_count and yes_count > 0:
            proposal = proposal_submissions.get(proposer_user_id)
            if proposal:
                tied_proposals.append({
                    'user_id': proposer_user_id,
                    'title': proposal['title'],
                    'description': proposal['description'],
                    'proposed_by': proposal['user_name']
                })
    
    return jsonify({'tied_proposals': tied_proposals})

@app.route('/api/tiebreaker-vote/<int:proposer_user_id>', methods=['POST'])
@api_login_required
def record_tiebreaker_vote(proposer_user_id):
    """Record a tie breaker vote on a proposal"""
    data = request.json
    vote_choice = data.get('vote')
    password = data.get('password')
    
    if not vote_choice or vote_choice not in ['yes', 'no', 'abstain']:
        return jsonify({'error': 'Invalid vote'}), 400
    
    if not password:
        return jsonify({'error': 'Password required'}), 400
    
    # Verify password
    user_id = session.get('user_id')
    user_name = session.get('user_name')
    db = get_db()
    user = db.execute('SELECT password FROM users WHERE id = ?', (user_id,)).fetchone()
    
    if not user or user['password'] != hash_password(password):
        return jsonify({'error': 'Invalid password'}), 401
    
    # Initialize if not exists
    if proposer_user_id not in tiebreaker_votes:
        tiebreaker_votes[proposer_user_id] = {'yes': 0, 'no': 0, 'abstain': 0}
    
    # Record the vote
    tiebreaker_votes[proposer_user_id][vote_choice] += 1
    
    return jsonify({'success': True}), 201

@app.route('/api/mark-tiebreaker-complete', methods=['POST'])
@api_login_required
def mark_tiebreaker_complete():
    """Mark user as finished with tie breaking"""
    user_id = session.get('user_id')
    users_finished_tiebreaker.add(user_id)
    return jsonify({'success': True}), 200

@app.route('/api/check-all-tiebreaker-complete', methods=['GET'])
@api_login_required
def check_all_tiebreaker_complete():
    """Check if all users have finished tie breaking"""
    db = get_db()
    total_users = db.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    finished_users = len(users_finished_tiebreaker)
    
    all_complete = finished_users == total_users and total_users > 0
    
    return jsonify({
        'all_complete': all_complete,
        'finished': finished_users,
        'total': total_users
    })

@app.route('/api/final-voting-results', methods=['GET'])
@api_login_required
def get_final_voting_results():
    """Get final results after tie breaking"""
    db = get_db()
    total_users = db.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    
    results = []
    
    for proposer_user_id, proposal in proposal_submissions.items():
        # Use tiebreaker votes if available, otherwise use regular votes
        votes_data = tiebreaker_votes.get(proposer_user_id) or submission_votes.get(proposer_user_id, {})
        
        yes_count = votes_data.get('yes', 0)
        no_count = votes_data.get('no', 0)
        abstain_count = votes_data.get('abstain', 0)
        total_votes = yes_count + no_count + abstain_count
        
        # Calculate percentages (excluding abstain from pass/fail determination)
        yes_percent = round((yes_count / total_votes * 100) if total_votes > 0 else 0)
        no_percent = round((no_count / total_votes * 100) if total_votes > 0 else 0)
        abstain_percent = round((abstain_count / total_votes * 100) if total_votes > 0 else 0)
        
        # Determine status (yes > no = passed, no > yes = failed, yes == no = tied)
        if yes_count > no_count:
            status = 'passed'
        elif no_count > yes_count:
            status = 'failed'
        else:
            status = 'tied'
        
        results.append({
            'user_id': proposer_user_id,
            'title': proposal['title'],
            'description': proposal['description'],
            'proposed_by': proposal['user_name'],
            'yes': yes_count,
            'no': no_count,
            'abstain': abstain_count,
            'yes_percent': yes_percent,
            'no_percent': no_percent,
            'abstain_percent': abstain_percent,
            'status': status
        })
    
    # Sort by yes votes descending
    results.sort(key=lambda x: x['yes'], reverse=True)
    
    return jsonify(results)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
