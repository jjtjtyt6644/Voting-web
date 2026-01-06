let currentProposalId = null;
let members = [];
let proposals = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadMembers();
    loadProposals();
    setInterval(loadProposals, 5000); // Refresh proposals every 5 seconds
    setInterval(loadMembers, 10000); // Refresh members every 10 seconds
});

// Add member to assembly
async function addMember() {
    const nameInput = document.getElementById('memberName');
    const countryInput = document.getElementById('memberCountry');
    
    const name = nameInput.value.trim();
    const country = countryInput.value.trim();
    
    if (!name || !country) {
        alert('Please enter both name and country');
        return;
    }
    
    try {
        const response = await fetch('/api/members', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, country })
        });
        
        if (response.ok) {
            nameInput.value = '';
            countryInput.value = '';
            loadMembers();
            updateVoterSelect();
        } else {
            const data = await response.json();
            alert(data.error || 'Failed to add member');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error adding member');
    }
}

// Load members from server
async function loadMembers() {
    try {
        const response = await fetch('/api/members');
        members = await response.json();
        renderMembers();
    } catch (error) {
        console.error('Error loading members:', error);
    }
}

// Render members list
function renderMembers() {
    const list = document.getElementById('membersList');
    
    if (members.length === 0) {
        list.innerHTML = '<p class="empty">No members yet</p>';
        return;
    }
    
    list.innerHTML = members.map(member => `
        <div class="member-item">
            <div class="member-name">${escapeHtml(member.name)}</div>
            <div class="member-country">🌍 ${escapeHtml(member.country)}</div>
        </div>
    `).join('');
}

// Create proposal
async function createProposal() {
    const titleInput = document.getElementById('proposalTitle');
    const descInput = document.getElementById('proposalDesc');
    const proposerInput = document.getElementById('proposalProposer');
    
    const title = titleInput.value.trim();
    const description = descInput.value.trim();
    const proposed_by = proposerInput.value.trim();
    
    if (!title || !description || !proposed_by) {
        alert('Please fill in all fields');
        return;
    }
    
    try {
        const response = await fetch('/api/proposals', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, description, proposed_by })
        });
        
        if (response.ok) {
            titleInput.value = '';
            descInput.value = '';
            proposerInput.value = '';
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

// Load proposals from server
async function loadProposals() {
    try {
        const response = await fetch('/api/proposals');
        proposals = await response.json();
        renderProposals();
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
    
    list.innerHTML = proposals.map(proposal => `
        <div class="proposal-item">
            <div class="proposal-title">${escapeHtml(proposal.title)}</div>
            <div class="proposal-description">${escapeHtml(proposal.description)}</div>
            <div class="proposal-meta">
                <span>Proposed by: <strong>${escapeHtml(proposal.proposed_by)}</strong></span>
                <span>${formatDate(proposal.created_date)}</span>
            </div>
            <div class="proposal-buttons">
                <button class="vote-btn-proposal" onclick="openVotingModal(${proposal.id})">
                    Vote on This Proposal
                </button>
            </div>
        </div>
    `).join('');
}

// Open voting modal
async function openVotingModal(proposalId) {
    currentProposalId = proposalId;
    const proposal = proposals.find(p => p.id === proposalId);
    
    if (!proposal) return;
    
    document.getElementById('modalTitle').textContent = proposal.title;
    document.getElementById('modalDescription').textContent = proposal.description;
    
    updateVoterSelect();
    await updateResults();
    
    document.getElementById('votingModal').style.display = 'block';
}

// Close voting modal
function closeVotingModal() {
    document.getElementById('votingModal').style.display = 'none';
    currentProposalId = null;
}

// Update voter dropdown
function updateVoterSelect() {
    const select = document.getElementById('voterSelect');
    select.innerHTML = '<option value="">Select a member...</option>';
    
    members.forEach(member => {
        const option = document.createElement('option');
        option.value = member.id;
        option.textContent = `${member.name} (${member.country})`;
        select.appendChild(option);
    });
}

// Submit vote
async function submitVote(voteChoice) {
    if (!currentProposalId) return;
    
    const memberId = document.getElementById('voterSelect').value;
    
    if (!memberId) {
        alert('Please select a member to vote');
        return;
    }
    
    try {
        const response = await fetch(`/api/proposals/${currentProposalId}/vote`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ member_id: memberId, vote: voteChoice })
        });
        
        if (response.ok) {
            document.getElementById('voterSelect').value = '';
            await updateResults();
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
        document.getElementById('totalCount').textContent = results.total_members;
    } catch (error) {
        console.error('Error loading results:', error);
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
