# VoteSecure - Online Voting Platform

A secure, transparent, and user-friendly online voting platform built with Flask and SQLite. VoteSecure enables organizations, institutions, and communities to conduct elections with complete integrity and ease of use.

## ✨ Features

- **Multi-Room Voting System**: Create separate voting rooms with passcodes for isolated elections
- **Secure Authentication**: User registration and login with encrypted passwords
- **Proposal Submission Phase**: Users submit and discuss proposals before voting
- **Voting Phase**: Cast votes on proposals with real-time results tracking
- **Tiebreaker Resolution**: Automatic tiebreaker voting when proposals are tied
- **Live Member Status**: See who's voting and who's finished in real-time
- **Room Code Display**: Copy room codes to clipboard for easy sharing
- **Modern UI**: Responsive design with smooth animations and intuitive navigation
- **Update Logs**: Track version history and feature updates

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Local Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/jjtjtyt6644/Voting-web.git
   cd Voting-web
   ```

2. **Create a virtual environment (optional but recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open in browser**
   - Navigate to `http://localhost:5000`
   - Register a new account or login

## 📖 How to Use

### For Organizers

1. **Start the Application**: Run `python app.py` and navigate to the homepage
2. **Login/Register**: Create an account or login with existing credentials
3. **Create a Room**: 
   - Click "Create Room" on the room selection page
   - Set a room name and passcode
   - Share the room code with participants
4. **Wait for Participants**: See members join the room in the lobby
5. **Start Voting**: All participants submit proposals, then vote on them
6. **View Results**: See final results and any tied proposals

### For Participants

1. **Login**: Enter your credentials
2. **Join a Room**: 
   - Enter the room passcode provided by the organizer
   - OR create a new room
3. **Submit Proposal** (if required):
   - Enter proposal title and description
   - Wait for all participants to submit
4. **Vote**: 
   - View all proposals
   - Vote YES, NO, or ABSTAIN on each proposal
5. **View Results**: See voting results once all members finish voting

### Proposal States

- **Passed**: YES votes > NO votes
- **Failed**: NO votes ≥ YES votes
- **Tied**: YES votes = NO votes (triggers tiebreaker)

### Tiebreaker Voting

When proposals are tied:
1. All members vote again on tied proposals only
2. The proposal with more YES votes in the tiebreaker passes
3. If still tied after tiebreaker, it's marked as TIED

## 🛠️ Technology Stack

- **Backend**: Flask (Python web framework)
- **Database**: SQLite3
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Authentication**: Session-based with password hashing
- **Deployment**: Gunicorn + Render

## 📁 Project Structure

```
Voting-web/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── un_voting.db               # SQLite database
├── templates/                 # HTML templates
│   ├── home.html             # Landing page
│   ├── login.html            # Login/Register page
│   ├── room.html             # Room selection/creation
│   ├── lobby.html            # Assembly lobby
│   ├── voting.html           # Voting phase
│   ├── tiebreaker.html       # Tiebreaker voting
│   ├── results.html          # Results display
│   ├── update_log.html       # Version history
│   └── index.html            # Index page
├── static/                    # Static files
│   ├── style.css             # Main stylesheet
│   ├── script.js             # Shared JavaScript
│   ├── voting.js             # Voting logic
│   └── background.png        # Background image
└── README.md                  # This file
```

## 🔧 API Endpoints

### Authentication
- `POST /login` - User login
- `POST /register` - User registration
- `GET /logout` - User logout

### Room Management
- `POST /api/room/create` - Create a new voting room
- `POST /api/room/join` - Join an existing room
- `GET /api/room/current` - Get current room info
- `GET /api/room/info/<room_code>` - Get specific room details
- `POST /api/room/leave` - Leave a room

### Voting
- `POST /api/proposal-submission` - Submit a proposal
- `GET /api/all-proposals-submitted` - Check submission status
- `GET /api/proposals` - Get all proposals in room
- `POST /api/vote` - Cast a vote
- `GET /api/check-all-voted` - Check voting completion status
- `GET /api/all-voting-results` - Get voting results

### Tiebreaker
- `POST /api/agree-to-tiebreak` - Agree to break tie
- `GET /api/check-tiebreak-agreement` - Check tiebreak agreement status
- `POST /api/tiebreak-vote` - Cast tiebreaker vote
- `GET /api/check-tiebreak-voted` - Check tiebreaker completion

### Admin
- `GET /api/users` - Get room members
- `GET /api/ready-status` - Get user ready status


## 📊 Database Schema

The application uses SQLite with the following main tables:

- **users**: Stores user accounts and credentials
- **proposals**: Stores submitted proposals
- **votes**: Stores individual votes on proposals
- **tiebreaker_votes**: Stores tiebreaker votes

## 🔐 Security Features

- Password hashing using SHA-256
- Session-based authentication
- Room passcode protection
- User validation on all API endpoints
- Room-scoped data isolation


## 📝 Version History

See [Update Logs] for detailed version history and feature updates.

### Latest Version: v2.1.1
- Fixed proposal counting for multi-room isolation
- Fixed voting member count display
- Fixed tiebreaker member count display
- Enhanced lobby UI with animations

## 🤝 Contributing

To contribute to this project:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is open source and available under the MIT License.

## 👨‍💻 Author

**Junyu** - Created 2026

---

**Made with for secure and transparent voting**
