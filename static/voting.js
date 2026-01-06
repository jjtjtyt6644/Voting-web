let currentProposalId = null;
let proposals = [];
let userVotedProposals = new Set();
let currentUserId = null;
let hasSubmittedProposal = false;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadProposals();
    checkIfNeedsProposal();
    setInterval(loadProposals, 5000);
});

// Load proposals from server
async function loadProposals() {
    try {
        const response = await fetch('/api/proposals');
        if (response.status === 401) {
            window.location.href = '/login';
            return;
        }
        proposals = await response.json();
        renderProposals();
        updateStats();
    } catch (error) {
        console.error('Error loading proposals:', error);
    }
}

// Render proposals list
function renderProposals() {
    const list = document.getElementById('proposalsList');
    
    if (proposals.length === 0) {
        list.innerHTML = '<p class="empty">No proposals yet</p>';
        return;
    }
    
    list.innerHTML = proposals.map(proposal => {
        const alreadyVoted = userVotedProposals.has(proposal.id);
        return `
            <div class="proposal-item">
                <div class="proposal-title">${escapeHtml(proposal.title)}</div>
                <div class="proposal-description">${escapeHtml(proposal.description)}</div>
                <div class="proposal-meta">
                    <span>Proposed by: <strong>${escapeHtml(proposal.proposed_by)}</strong></span>
                    <span>${formatDate(proposal.created_date)}</span>
                </div>
                <div class="proposal-buttons">
                    <button class="vote-btn-proposal" onclick="openVotingModal(${proposal.id})" ${alreadyVoted ? 'disabled' : ''}>
                        ${alreadyVoted ? '✓ Already Voted' : 'Vote on This Proposal'}
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// Create proposal
async function createProposal() {
    const titleInput = document.getElementById('proposalTitle');
    const descInput = document.getElementById('proposalDesc');
    
    const title = titleInput.value.trim();
    const description = descInput.value.trim();
    
    if (!title || !description) {
        alert('Please fill in all fields');
        return;
    }
    
    try {
        const response = await fetch('/api/proposals', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, description })
        });
        
        if (response.ok) {
            titleInput.value = '';
            descInput.value = '';
            loadProposals();
        } else {
            const data = await response.json();
            alert(data.error || 'Failed to create proposal');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error creating proposal');
    }
}

// Open voting modal
async function openVotingModal(proposalId) {
    currentProposalId = proposalId;
    const proposal = proposals.find(p => p.id === proposalId);
    
    if (!proposal) return;
    
    document.getElementById('modalTitle').textContent = proposal.title;
    document.getElementById('modalDescription').textContent = proposal.description;
    document.getElementById('passwordInput').value = '';
    
    await updateResults();
    
    document.getElementById('votingModal').style.display = 'block';
}

// Close voting modal
function closeVotingModal() {
    document.getElementById('votingModal').style.display = 'none';
    currentProposalId = null;
    document.getElementById('passwordInput').value = '';
}

// Submit vote
async function submitVote(voteChoice) {
    if (!currentProposalId) return;
    
    const password = document.getElementById('passwordInput').value;
    
    if (!password) {
        alert('Please enter your password to vote');
        return;
    }
    
    try {
        const response = await fetch(`/api/proposals/${currentProposalId}/vote`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ vote: voteChoice, password })
        });
        
        if (response.ok) {
            userVotedProposals.add(currentProposalId);
            document.getElementById('passwordInput').value = '';
            closeVotingModal();
            loadProposals();
            alert(`Vote recorded: ${voteChoice.toUpperCase()}`);
        } else {
            const data = await response.json();
            alert(data.error || 'Failed to record vote');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error recording vote');
    }
}

// Update voting results
async function updateResults() {
    if (!currentProposalId) return;
    
    try {
        const response = await fetch(`/api/proposals/${currentProposalId}/results`);
        const results = await response.json();
        
        document.getElementById('yesCount').textContent = results.yes;
        document.getElementById('noCount').textContent = results.no;
        document.getElementById('abstainCount').textContent = results.abstain;
        document.getElementById('votedCount').textContent = results.total_voted;
        document.getElementById('totalCount').textContent = results.total_users;
    } catch (error) {
        console.error('Error loading results:', error);
    }
}

// Update stats
function updateStats() {
    document.getElementById('totalProposals').textContent = proposals.length;
    document.getElementById('yourVotes').textContent = userVotedProposals.size;
}

// Navigate to results
function goToResults() {
    window.location.href = '/results';
}

// Check if user needs to submit proposal
async function checkIfNeedsProposal() {
    // Simulate random selection - in production, could be assigned by server
    const shouldSubmit = Math.random() < 0.3; // 30% chance for demo
    
    if (shouldSubmit) {
        try {
            const response = await fetch('/api/random-proposer');
            const data = await response.json();
            
            // Get current user ID from session/page
            const userNameEl = document.querySelector('.user-name');
            if (userNameEl && data.user_name === userNameEl.textContent) {
                openProposalModal();
            }
        } catch (error) {
            console.error('Error:', error);
        }
    }
}

// Open proposal submission modal
function openProposalModal() {
    const text = document.getElementById('proposalModalText');
    text.textContent = 'You have been randomly selected to submit a proposal. Please describe your proposal below and click submit. All members will see it immediately.';
    document.getElementById('proposalModal').style.display = 'block';
}

// Close proposal modal
function closeProposalModal() {
    document.getElementById('proposalModal').style.display = 'none';
}

// Submit proposal from modal
async function submitProposalFromModal() {
    const title = document.getElementById('proposalTitleInput').value.trim();
    const description = document.getElementById('proposalDescInput').value.trim();
    
    if (!title || !description) {
        alert('Please fill in all fields');
        return;
    }
    
    try {
        const response = await fetch('/api/proposals', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, description })
        });
        
        if (response.ok) {
            closeProposalModal();
            document.getElementById('proposalTitleInput').value = '';
            document.getElementById('proposalDescInput').value = '';
            hasSubmittedProposal = true;
            loadProposals();
            alert('✓ Your proposal has been submitted and is now visible to all members!');
        } else {
            const data = await response.json();
            alert(data.error || 'Failed to submit proposal');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error submitting proposal');
    }
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('votingModal');
    if (event.target === modal) {
        closeVotingModal();
    }
}

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    if (seconds < 60) return 'just now';
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
}
