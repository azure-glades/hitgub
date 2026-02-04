// Main application logic
class App {
    constructor() {
        this.currentRepo = null;
        this.currentIssue = null;
        this.initializeEventListeners();
        this.initializeModals();
        this.initializeTabs();
    }

    initializeEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = link.dataset.page;
                showPage(page);
            });
        });

        // Hero actions
        document.querySelector('[data-action="get-started"]')?.addEventListener('click', () => {
            if (auth.isAuthenticated()) {
                showPage('repositories');
            } else {
                openModal('login-modal');
            }
        });

        // Create repository
        document.getElementById('create-repo-btn')?.addEventListener('click', () => {
            if (auth.requireAuth() && auth.requireDeveloper()) {
                openModal('repo-modal');
            }
        });

        // Create repository (from my-repos page)
        document.getElementById('create-repo-btn-my')?.addEventListener('click', () => {
            if (auth.requireAuth() && auth.requireDeveloper()) {
                openModal('repo-modal');
            }
        });

        // Create user
        document.getElementById('create-user-btn')?.addEventListener('click', () => {
            if (auth.requireAuth() && auth.requireAdmin()) {
                openModal('user-modal');
            }
        });

        // Create issue
        document.getElementById('create-issue-btn')?.addEventListener('click', () => {
            if (auth.requireAuth()) {
                openModal('issue-modal');
            }
        });

        // Delete repository
        document.getElementById('delete-repo-btn')?.addEventListener('click', () => {
            if (confirm('Are you sure you want to delete this repository? This action cannot be undone.')) {
                this.handleDeleteRepo();
            }
        });

        // Back to repo button
        document.getElementById('back-to-repo')?.addEventListener('click', () => {
            if (this.currentRepo) {
                showRepoDetail(this.currentRepo.repo_id);
            } else {
                showPage('repositories');
            }
        });

        // Toggle issue status button
        document.getElementById('toggle-issue-status')?.addEventListener('click', async () => {
            await this.handleToggleIssueStatus();
        });
        document.getElementById('fork-repo-btn')?.addEventListener('click', () => {
        if (auth.requireAuth() && auth.requireDeveloper()) {
            openModal('fork-modal');
        }
    });

        // My Repos filter
        document.getElementById('my-repos-filter')?.addEventListener('change', (e) => {
            loadMyRepos(1, e.target.value);
        });

        // Create user form (admin page)
        document.getElementById('create-user-form-admin')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.handleCreateUserAdmin();
        });

        // Form submissions
        this.initializeForms();
    }

    initializeForms() {
        // Repository form
        document.getElementById('repo-form')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.handleCreateRepo();
        });

        // Issue form
        document.getElementById('issue-form')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.handleCreateIssue();
        });

        // User form
        document.getElementById('user-form')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.handleCreateUser();
        });

        // Comment form
        document.getElementById('comment-form')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.handleAddComment();
        });

        // Fork form
        document.getElementById('fork-form')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.handleForkRepo();
        });

        // Add member form
        document.getElementById('add-member-form')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.handleAddMember();
        });
    }

    initializeModals() {
        // Close modal on background click
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    closeModal(modal.id);
                }
            });
        });

        // Close modal on close button click
        document.querySelectorAll('.close-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const modal = e.target.closest('.modal');
                closeModal(modal.id);
            });
        });
    }

    initializeTabs() {
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const tab = btn.dataset.tab;
                this.switchTab(tab);
            });
        });
    }

    switchTab(activeTab) {
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === activeTab);
        });

        // Update tab panes
        document.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.toggle('active', pane.id === `tab-${activeTab}`);
        });

        // Lazy load access logs when the tab is opened
        if (activeTab === 'logs' && this.currentRepo) {
            loadRepoLogs(this.currentRepo.repo_id);
        }
    }

    async handleCreateRepo() {
        try {
            const repoName = document.getElementById('repo-name').value;
            
            if (!repoName.trim()) {
                showNotification('Repository name is required', 'error');
                return;
            }

            showLoading(true);
            
            const repoData = {
                reponame: repoName.trim(),
                maintainer_id: 0 // Will be overridden by backend with current user
            };

            const response = await RepoAPI.create(repoData);
            
            closeModal('repo-modal');
            document.getElementById('repo-form').reset();
            showNotification('Repository created successfully!', 'success');
            
            // Refresh repositories page
            if (document.querySelector('#page-repositories').classList.contains('active')) {
                await loadRepositories();
            }

        } catch (error) {
            handleAPIError(error, 'creating repository');
        } finally {
            showLoading(false);
        }
    }

    async handleCreateIssue() {
        try {
            const titleEl = document.getElementById('new-issue-title');
            const descriptionEl = document.getElementById('issue-description');
            
            const title = titleEl?.value || '';
            const description = descriptionEl?.value || '';

            if (!this.currentRepo) {
                showNotification('No repository selected', 'error');
                return;
            }

            showLoading(true);
            
            const issueData = {
                title: title,
                body: description
            };

            const response = await IssueAPI.create(this.currentRepo.repo_id, issueData);
            
            closeModal('issue-modal');
            document.getElementById('issue-form').reset();
            showNotification('Issue created successfully!', 'success');
            
            // Refresh issues list
            await loadRepoIssues(this.currentRepo.repo_id);

        } catch (error) {
            handleAPIError(error, 'creating issue');
        } finally {
            showLoading(false);
        }
    }

    async handleCreateUser() {
        try {
            const username = document.getElementById('user-username').value;
            const email = document.getElementById('user-email').value;
            const password = document.getElementById('user-password').value;
            
            if (!username.trim() || !email.trim() || !password.trim()) {
                showNotification('All fields are required', 'error');
                return;
            }

            showLoading(true);
            
            const userData = {
                username: username.trim(),
                email: email.trim(),
                password: password
            };

            const response = await UserAPI.create(userData);
            
            closeModal('user-modal');
            document.getElementById('user-form').reset();
            showNotification('User created successfully!', 'success');
            
            // Refresh users page if active
            if (document.querySelector('#page-users').classList.contains('active')) {
                await loadUsers();
            }

        } catch (error) {
            handleAPIError(error, 'creating user');
        } finally {
            showLoading(false);
        }
    }

    async handleAddComment() {
        try {
            const body = document.getElementById('comment-body').value;
            
            if (!body.trim()) {
                showNotification('Comment cannot be empty', 'error');
                return;
            }

            if (!this.currentRepo || !this.currentIssue) {
                showNotification('No issue selected', 'error');
                return;
            }

            showLoading(true);
            
            const commentData = {
                body: body.trim()
            };

            await IssueAPI.addComment(this.currentRepo.repo_id, this.currentIssue.issue_num, commentData);
            
            document.getElementById('comment-form').reset();
            showNotification('Comment added successfully!', 'success');
            
            // Refresh issue detail
            await showIssueDetail(this.currentRepo.repo_id, this.currentIssue.issue_num);

        } catch (error) {
            handleAPIError(error, 'adding comment');
        } finally {
            showLoading(false);
        }
    }

    async handleForkRepo() {
        try {
            const forkName = document.getElementById('fork-name').value;
            
            if (!forkName.trim()) {
                showNotification('Repository name is required', 'error');
                return;
            }

            if (!this.currentRepo) {
                showNotification('No repository selected', 'error');
                return;
            }

            showLoading(true);
            
            const forkData = {
                new_reponame: forkName.trim()
            };

            const response = await RepoAPI.fork(this.currentRepo.repo_id, forkData);
            
            closeModal('fork-modal');
            document.getElementById('fork-form').reset();
            showNotification('Repository forked successfully!', 'success');
            
            // Navigate to the new forked repository
            setTimeout(() => {
                showRepoDetail(response.repo_id);
            }, 1000);

        } catch (error) {
            handleAPIError(error, 'forking repository');
        } finally {
            showLoading(false);
        }
    }

    async handleAddMember() {
        try {
            const userId = document.getElementById('member-user').value;
            
            if (!userId) {
                showNotification('Please select a user', 'error');
                return;
            }

            if (!this.currentRepo) {
                showNotification('No repository selected', 'error');
                return;
            }

            console.log('Adding member:', {
                userId: parseInt(userId),
                repoId: this.currentRepo.repo_id,
                currentUser: auth.currentUser
            });

            showLoading(true);
            
            // Get developer role ID
            const roles = await RoleAPI.list();
            const developerRole = roles.find(r => r.rolename === 'developer');
            
            if (!developerRole) {
                showNotification('Developer role not found in system', 'error');
                return;
            }

            console.log('Using developer role:', developerRole);

            // Grant access
            await AccessAPI.grant(parseInt(userId), this.currentRepo.repo_id, developerRole.role_id);
            
            closeModal('add-member-modal');
            document.getElementById('add-member-form').reset();
            showNotification('Developer added successfully!', 'success');
            
            // Reload members list
            await loadRepoMembers(this.currentRepo.repo_id);

        } catch (error) {
            console.error('Error adding member:', error);
            handleAPIError(error, 'adding member to repository');
        } finally {
            showLoading(false);
        }
    }

    async handleToggleIssueStatus() {
        try {
            if (!this.currentRepo || !this.currentIssue) {
                showNotification('No issue selected', 'error');
                return;
            }

            showLoading(true);
            
            const newStatus = this.currentIssue.status === 'open' ? 'closed' : 'open';
            
            await IssueAPI.updateStatus(this.currentRepo.repo_id, this.currentIssue.issue_num, newStatus);
            
            showNotification(`Issue ${newStatus === 'closed' ? 'closed' : 'reopened'} successfully!`, 'success');
            
            // Reload issue detail to show updated status
            await showIssueDetail(this.currentRepo.repo_id, this.currentIssue.issue_num);

        } catch (error) {
            handleAPIError(error, 'updating issue status');
        } finally {
            showLoading(false);
        }
    }

    async handleDeleteRepo() {
        try {
            if (!this.currentRepo) {
                showNotification('No repository selected', 'error');
                return;
            }

            showLoading(true);
            
            await RepoAPI.delete(this.currentRepo.repo_id);
            
            showNotification('Repository deleted successfully!', 'success');
            
            // Navigate back to repositories page
            this.currentRepo = null;
            showPage('repositories');
            await loadRepositories();

        } catch (error) {
            handleAPIError(error, 'deleting repository');
        } finally {
            showLoading(false);
        }
    }

    async handleCreateUserAdmin() {
        try {
            const username = document.getElementById('admin-username').value;
            const email = document.getElementById('admin-email').value;
            const password = document.getElementById('admin-password').value;
            const tier = document.getElementById('admin-tier').value;

            if (!username.trim() || !email.trim() || !password.trim()) {
                showNotification('All fields are required', 'error');
                return;
            }

            showLoading(true);

            // Create the user
            const userData = {
                username: username.trim(),
                email: email.trim(),
                password: password.trim()
            };

            const response = await UserAPI.create(userData);

            // Update user tier if not developer (default)
            if (tier !== 'developer') {
                await UserAPI.updateTier(response.user_id, { tier });
            }

            document.getElementById('create-user-form-admin').reset();
            showNotification(`User '${username}' created successfully!`, 'success');

        } catch (error) {
            handleAPIError(error, 'creating user account');
        } finally {
            showLoading(false);
        }
    }
}

// Page navigation
function showPage(pageName, skipHistory = false) {
    // Hide all pages
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });

    // Show target page
    const targetPage = document.getElementById(`page-${pageName}`);
    if (targetPage) {
        targetPage.classList.add('active');
        loadPageContent(pageName);
        
        // Update browser history
        if (!skipHistory) {
            const url = new URL(window.location);
            url.searchParams.set('page', pageName);
            window.history.pushState({ page: pageName }, '', url);
        }
    }
}

async function loadPageContent(pageName) {
    try {
        switch (pageName) {
            case 'repositories':
                await loadRepositories();
                break;
            case 'my-repos':
                if (auth.requireAuth()) {
                    await loadMyRepos(1, 'all');
                }
                break;
            case 'users':
                if (auth.isAdmin()) {
                    await loadUsers();
                } else {
                    showPage('home');
                    showNotification('Access denied', 'error');
                }
                break;
            case 'create-account':
                if (auth.isAdmin()) {
                    // Just reset the form when page loads
                    document.getElementById('create-user-form-admin')?.reset();
                } else {
                    showPage('home');
                    showNotification('Access denied', 'error');
                }
                break;
            case 'my-logs':
                if (auth.requireAuth()) {
                    await loadMyLogs();
                }
                break;
        }
    } catch (error) {
        console.error('Error loading page content:', error);
    }
}

// Repository functions
async function loadRepositories(page = 1) {
    try {
        showLoading(true);
        const response = await RepoAPI.list(page);
        renderRepositories(response);
    } catch (error) {
        handleAPIError(error, 'loading repositories');
        document.getElementById('repo-list').innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Failed to load repositories. Please try again.</p>
            </div>
        `;
    } finally {
        showLoading(false);
    }
}

function renderRepositories(data) {
    const container = document.getElementById('repo-list');
    
    if (!data.items || data.items.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-folder-open"></i>
                <h3>No repositories found</h3>
                <p>Create your first repository to get started!</p>
            </div>
        `;
        return;
    }

    container.innerHTML = data.items.map(repo => `
        <div class="repo-card" onclick="showRepoDetail(${repo.repo_id})">
            <h3><i class="fas fa-folder"></i> ${repo.reponame}</h3>
            <div class="repo-meta">
                <span><i class="fas fa-user"></i> ${repo.maintainer_name}</span>
            </div>
        </div>
    `).join('');

    renderPagination('repo-pagination', data.meta, loadRepositories);
}

async function showRepoDetail(repoId) {
    try {
        showLoading(true);
        
        // Find repo data from current list or fetch it
        const repoData = await findRepoById(repoId);
        
        app.currentRepo = repoData;
        
        // Update repository header
        document.getElementById('repo-title').textContent = repoData.reponame;
        document.getElementById('repo-maintainer').textContent = `Maintained by ${repoData.maintainer_name || 'Unknown'}`;
        document.getElementById('clone-url').textContent = `git clone http://localhost:8080/${repoData.reponame}.git`;
        
        // Show/hide delete button based on permissions
        const deleteBtn = document.getElementById('delete-repo-btn');
        const isOwner = auth.currentUser && (auth.currentUser.user_id === repoData.maintainer_id || auth.isAdmin());
        if (isOwner) {
            deleteBtn.style.display = 'inline-flex';
        } else {
            deleteBtn.style.display = 'none';
        }

        // Show access log tab only for owners/admins
        const logsTab = document.getElementById('repo-logs-tab');
        const membersTab = document.getElementById('repo-members-tab');
        const logsPane = document.getElementById('tab-logs');
        if (logsTab) {
            logsTab.style.display = isOwner ? 'inline-flex' : 'none';
            if (!isOwner && logsPane?.classList.contains('active')) {
                app.switchTab('issues');
            }
        }
        
        // Show members tab for owners
        if (membersTab) {
            membersTab.style.display = isOwner ? 'inline-flex' : 'none';
        }
        
        // Show add member button for owners
        const addMemberBtn = document.getElementById('add-member-btn');
        if (addMemberBtn) {
            addMemberBtn.style.display = isOwner ? 'inline-flex' : 'none';
            addMemberBtn.addEventListener('click', () => openAddMemberModal());
        }
        
        showPage('repo-detail');
        
        // Attach fork button event listener (re-attach every time page is shown)
        const forkBtn = document.getElementById('fork-repo-btn');
        if (forkBtn) {
            forkBtn.onclick = () => {
                if (auth.requireAuth() && auth.requireDeveloper()) {
                    openModal('fork-modal');
                }
            };
        }
        
        await loadRepoIssues(repoId);
        await loadRepoFiles(repoId);
        if (isOwner) {
            await loadRepoLogs(repoId);
            await loadRepoMembers(repoId);
        }
        
    } catch (error) {
        handleAPIError(error, 'loading repository details');
    } finally {
        showLoading(false);
    }
}

async function findRepoById(repoId) {
    // Always fetch full repo details from API to get maintainer_id
    try {
        const response = await API.get(`/repos?page=1&size=100`);
        const repo = response.items.find(r => r.repo_id === repoId);
        if (repo) {
            return {
                repo_id: repo.repo_id,
                reponame: repo.reponame,
                maintainer_name: repo.maintainer_name,
                maintainer_id: repo.maintainer_id
            };
        }
    } catch (error) {
        console.error('Failed to fetch repo data:', error);
    }
    
    // If not found, we'll create a basic object
    return {
        repo_id: repoId,
        reponame: `Repository ${repoId}`,
        maintainer_name: 'Unknown',
        maintainer_id: null
    };
}

// Issue functions
async function loadRepoIssues(repoId, page = 1) {
    try {
        const response = await IssueAPI.list(repoId, page);
        renderIssues(response, repoId);
    } catch (error) {
        handleAPIError(error, 'loading issues');
        document.getElementById('issue-list').innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Failed to load issues. Please try again.</p>
            </div>
        `;
    }
}

function renderIssues(data, repoId) {
    const container = document.getElementById('issue-list');
    
    if (!data.items || data.items.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-bug"></i>
                <h3>No issues found</h3>
                <p>Create your first issue to start tracking bugs and features!</p>
            </div>
        `;
        return;
    }

    container.innerHTML = data.items.map(issue => `
        <div class="issue-card" onclick="showIssueDetail(${repoId}, ${issue.issue_num})">
            <h3><i class="fas fa-${issue.status === 'open' ? 'circle' : 'check-circle'}"></i> ${issue.title || 'Untitled Issue'}</h3>
            <div class="issue-meta">
                <span class="issue-number">#${issue.issue_num}</span>
                <span class="issue-status ${issue.status}">${issue.status}</span>
                <span><i class="fas fa-user"></i> ${issue.author}</span>
                <span><i class="fas fa-clock"></i> ${formatRelativeTime(issue.created_at)}</span>
            </div>
        </div>
    `).join('');

    renderPagination('issue-pagination', data.meta, (page) => loadRepoIssues(repoId, page));
}

async function loadRepoFiles(repoId) {
    try {
        const response = await RepoAPI.getFiles(repoId);
        renderRepoFiles(response);
    } catch (error) {
        // Don't show error for empty repos
        document.getElementById('repo-files').innerHTML = `
            <div class="empty-state">
                <i class="fas fa-folder-open"></i>
                <p>No files in repository yet</p>
            </div>
        `;
    }
}

function renderRepoFiles(data) {
    const container = document.getElementById('repo-files');
    
    if (!data.files || data.files.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-folder-open"></i>
                <p>No files in repository yet</p>
            </div>
        `;
        return;
    }

    // Group files by directory
    const directories = new Set();
    const files = [];
    
    data.files.forEach(file => {
        if (file.type === 'tree') {
            directories.add(file.path);
        } else {
            files.push(file);
        }
    });

    let html = '';
    
    // Show directories first
    if (directories.size > 0) {
        html += '<div class="file-group"><h4>📁 Directories</h4><ul class="file-list-items">';
        directories.forEach(dir => {
            html += `<li><i class="fas fa-folder"></i> ${dir}</li>`;
        });
        html += '</ul></div>';
    }
    
    // Show files
    if (files.length > 0) {
        html += '<div class="file-group"><h4>📄 Files</h4><ul class="file-list-items">';
        files.forEach(file => {
            const icon = getFileIcon(file.path);
            html += `<li><i class="${icon}"></i> ${file.path}</li>`;
        });
        html += '</ul></div>';
    }

    container.innerHTML = html;
}

// Access Log functions
async function loadRepoLogs(repoId, page = 1) {
    try {
        const response = await AccessLogAPI.listRepoLogs(repoId, page);
        renderRepoLogs(response, repoId);
    } catch (error) {
        handleAPIError(error, 'loading access logs');
        const container = document.getElementById('repo-logs-list');
        if (container) {
            container.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Failed to load logs. Please try again.</p>
                </div>
            `;
        }
    }
}

async function loadRepoMembers(repoId) {
    try {
        const response = await AccessAPI.getMembers(repoId);
        renderRepoMembers(response);
    } catch (error) {
        handleAPIError(error, 'loading repository members');
        const container = document.getElementById('repo-members-list');
        if (container) {
            container.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Failed to load members. Please try again.</p>
                </div>
            `;
        }
    }
}

function renderRepoMembers(data) {
    const container = document.getElementById('repo-members-list');
    if (!container) return;

    if (!data.members || data.members.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-users"></i>
                <h3>No members yet</h3>
                <p>Add developers to allow them to push code to this repository.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = data.members.map(member => `
        <div class="member-card">
            <div class="member-info">
                <strong>${member.username}</strong>
                <span class="member-role">${member.role}</span>
            </div>
            <button class="btn btn-small btn-danger" onclick="removeMember(${data.repo_id}, ${member.user_id}, '${member.username}')">
                <i class="fas fa-trash"></i> Remove
            </button>
        </div>
    `).join('');
}

function renderRepoLogs(data, repoId) {
    const container = document.getElementById('repo-logs-list');
    if (!container) return;

    if (!data.items || data.items.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-list"></i>
                <h3>No access logs yet</h3>
                <p>Actions like clone, push, fork, delete will appear here.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = data.items.map(log => `
        <div class="log-card">
            <div class="log-main">
                <strong>${log.action.toUpperCase()}</strong>
                <span class="log-user"><i class="fas fa-user"></i> ${log.username}</span>
                <span class="log-time"><i class="fas fa-clock"></i> ${formatRelativeTime(log.created_at)}</span>
            </div>
            <div class="log-meta">Log #${log.log_no} in ${log.reponame}</div>
        </div>
    `).join('');

    renderPagination('repo-logs-pagination', data.meta, (p) => loadRepoLogs(repoId, p));
}

async function loadMyLogs(page = 1) {
    try {
        showLoading(true);
        const response = await AccessLogAPI.listMyLogs(page);
        renderMyLogs(response);
    } catch (error) {
        handleAPIError(error, 'loading my logs');
        const container = document.getElementById('my-logs-list');
        if (container) {
            container.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Failed to load your logs. Please try again.</p>
                </div>
            `;
        }
    } finally {
        showLoading(false);
    }
}

function renderMyLogs(data) {
    const container = document.getElementById('my-logs-list');
    if (!container) return;

    if (!data.items || data.items.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-list"></i>
                <h3>No access logs yet</h3>
                <p>Your clone/push/fork actions will appear here.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = data.items.map(log => `
        <div class="log-card">
            <div class="log-main">
                <strong>${log.action.toUpperCase()}</strong>
                <span class="log-repo"><i class="fas fa-folder"></i> ${log.reponame}</span>
                <span class="log-time"><i class="fas fa-clock"></i> ${formatRelativeTime(log.created_at)}</span>
            </div>
            <div class="log-meta">Log #${log.log_no}</div>
        </div>
    `).join('');

    renderPagination('my-logs-pagination', data.meta, loadMyLogs);
}

function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const iconMap = {
        'js': 'fab fa-js-square',
        'py': 'fab fa-python',
        'java': 'fab fa-java',
        'json': 'fas fa-code',
        'md': 'fas fa-file-alt',
        'txt': 'fas fa-file-alt',
        'html': 'fab fa-html5',
        'css': 'fab fa-css3',
        'yml': 'fas fa-code',
        'yaml': 'fas fa-code',
        'xml': 'fas fa-code',
        'sql': 'fas fa-database'
    };
    return iconMap[ext] || 'fas fa-file';
}

async function showIssueDetail(repoId, issueNum) {
    try {
        showLoading(true);
        
        const response = await IssueAPI.get(repoId, issueNum);
        
        app.currentIssue = { issue_num: issueNum };
        
        renderIssueDetail(response);
        showPage('issue-detail');
        
    } catch (error) {
        handleAPIError(error, 'loading issue details');
    } finally {
        showLoading(false);
    }
}

function renderIssueDetail(issue) {
    document.getElementById('issue-title').textContent = issue.title || 'Untitled Issue';
    document.getElementById('issue-number').textContent = issue.issue_num;
    document.getElementById('issue-status').textContent = issue.status;
    document.getElementById('issue-status').className = `issue-status ${issue.status}`;
    document.getElementById('issue-author').textContent = issue.author;
    document.getElementById('issue-date').textContent = formatDate(issue.created_at);
    document.getElementById('issue-body').textContent = issue.body;

    // Store current issue status
    app.currentIssue.status = issue.status;
    app.currentIssue.author_id = issue.author_id;

    // Show close/reopen button if user is author or admin/developer
    const toggleBtn = document.getElementById('toggle-issue-status');
    const toggleText = document.getElementById('toggle-status-text');
    const currentUser = auth.currentUser;
    
    if (currentUser && (currentUser.user_id === issue.author_id || auth.isDeveloper())) {
        toggleBtn.style.display = 'inline-flex';
        if (issue.status === 'open') {
            toggleText.textContent = 'Close Issue';
            toggleBtn.querySelector('i').className = 'fas fa-times-circle';
        } else {
            toggleText.textContent = 'Reopen Issue';
            toggleBtn.querySelector('i').className = 'fas fa-redo';
        }
    } else {
        toggleBtn.style.display = 'none';
    }

    // Render comments
    const commentsContainer = document.getElementById('comments-list');
    
    if (!issue.comments || issue.comments.length === 0) {
        commentsContainer.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-comments"></i>
                <p>No comments yet. Be the first to comment!</p>
            </div>
        `;
    } else {
        commentsContainer.innerHTML = issue.comments.map(comment => `
            <div class="comment">
                <div class="comment-header">
                    <span><i class="fas fa-user"></i> ${comment.user}</span>
                    <span><i class="fas fa-clock"></i> ${formatDate(comment.timestamp)}</span>
                </div>
                <div class="comment-body">${comment.body}</div>
            </div>
        `).join('');
    }
}

// User functions
async function loadUsers(page = 1) {
    try {
        showLoading(true);
        const response = await UserAPI.list(page);
        renderUsers(response);
    } catch (error) {
        handleAPIError(error, 'loading users');
        document.getElementById('user-list').innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Failed to load users. Please try again.</p>
            </div>
        `;
    } finally {
        showLoading(false);
    }
}

function renderUsers(data) {
    const container = document.getElementById('user-list');
    
    if (!data.items || data.items.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-users"></i>
                <h3>No users found</h3>
                <p>Create your first user to get started!</p>
            </div>
        `;
        return;
    }

    container.innerHTML = data.items.map(user => `
        <div class="user-card">
            <div class="user-info">
                <h3><i class="fas fa-user"></i> ${user.username}</h3>
                <div class="user-meta">
                    <span><i class="fas fa-envelope"></i> ${user.email}</span>
                    <span class="user-tier ${user.tier}"><i class="fas fa-tag"></i> ${user.tier}</span>
                </div>
            </div>
            <div class="user-actions">
                <select onchange="updateUserTier(${user.user_id}, this.value)" ${user.user_id === 1 ? 'disabled' : ''}>
                    <option value="tester" ${user.tier === 'tester' ? 'selected' : ''}>Tester</option>
                    <option value="developer" ${user.tier === 'developer' ? 'selected' : ''}>Developer</option>
                    <option value="admin" ${user.tier === 'admin' ? 'selected' : ''}>Admin</option>
                </select>
            </div>
        </div>
    `).join('');

    renderPagination('user-pagination', data.meta, loadUsers);
}

async function updateUserTier(userId, newTier) {
    try {
        showLoading(true);
        await UserAPI.updateTier(userId, { tier: newTier });
        showNotification('User tier updated successfully!', 'success');
        await loadUsers(); // Refresh the list
    } catch (error) {
        handleAPIError(error, 'updating user tier');
    } finally {
        showLoading(false);
    }
}

// Utility functions
function renderPagination(containerId, meta, loadFunction) {
    const container = document.getElementById(containerId);
    
    if (!meta || meta.total_pages <= 1) {
        container.innerHTML = '';
        return;
    }

    const { page, total_pages } = meta;
    let pagination = '';

    // Previous button
    if (page > 1) {
        pagination += `<button class="page-btn" onclick="${loadFunction.name}(${page - 1})">Previous</button>`;
    }

    // Page numbers
    const startPage = Math.max(1, page - 2);
    const endPage = Math.min(total_pages, page + 2);

    if (startPage > 1) {
        pagination += `<button class="page-btn" onclick="${loadFunction.name}(1)">1</button>`;
        if (startPage > 2) pagination += '<span class="page-ellipsis">...</span>';
    }

    for (let i = startPage; i <= endPage; i++) {
        const activeClass = i === page ? 'active' : '';
        pagination += `<button class="page-btn ${activeClass}" onclick="${loadFunction.name}(${i})">${i}</button>`;
    }

    if (endPage < total_pages) {
        if (endPage < total_pages - 1) pagination += '<span class="page-ellipsis">...</span>';
        pagination += `<button class="page-btn" onclick="${loadFunction.name}(${total_pages})">${total_pages}</button>`;
    }

    // Next button
    if (page < total_pages) {
        pagination += `<button class="page-btn" onclick="${loadFunction.name}(${page + 1})">Next</button>`;
    }

    container.innerHTML = pagination;
}

// Modal functions
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.classList.add('active');
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.classList.remove('active');
}

// Add member modal
async function openAddMemberModal() {
    try {
        if (!app.currentRepo) {
            showNotification('No repository selected', 'error');
            return;
        }
        
        // Fetch available users for this repo
        const response = await API.get(`/repos/${app.currentRepo.repo_id}/available-users`);
        const userSelect = document.getElementById('member-user');
        
        // Populate user list
        userSelect.innerHTML = '<option value="">-- Choose a user --</option>';
        response.users.forEach(user => {
            const option = document.createElement('option');
            option.value = user.user_id;
            option.textContent = `${user.username} (${user.email})`;
            userSelect.appendChild(option);
        });
        
        if (response.users.length === 0) {
            userSelect.innerHTML = '<option value="">-- No users available --</option>';
            showNotification('All users are already members or owner of this repository', 'info');
        }
        
        openModal('add-member-modal');
    } catch (error) {
        handleAPIError(error, 'loading available users');
    }
}

async function removeMember(repoId, userId, username) {
    if (!confirm(`Remove ${username} as developer from this repository?`)) {
        return;
    }
    
    try {
        showLoading(true);
        await AccessAPI.revoke(userId, repoId);
        showNotification(`${username} has been removed from the repository`, 'success');
        await loadRepoMembers(repoId);
    } catch (error) {
        handleAPIError(error, 'removing member');
    } finally {
        showLoading(false);
    }
}

// Copy clone URL
function copyCloneUrl() {
    const url = document.getElementById('clone-url').textContent;
    navigator.clipboard.writeText(url).then(() => {
        showNotification('Clone URL copied to clipboard!', 'success');
    }).catch(() => {
        showNotification('Failed to copy URL', 'error');
    });
}

// Load My Repositories
async function loadMyRepos(page = 1, filter = 'all') {
    try {
        showLoading(true);
        
        if (!auth.isAuthenticated()) {
            showNotification('Please log in first', 'error');
            showPage('home');
            return;
        }

        // Get user's repos with their roles
        const response = await API.get('/user/my-repos');
        const repos = response.repos || [];
        
        // Filter repos based on the filter parameter
        let filteredRepos = repos;
        if (filter === 'owner') {
            filteredRepos = repos.filter(repo => repo.role === 'owner');
        } else if (filter === 'developer') {
            filteredRepos = repos.filter(repo => repo.role === 'developer');
        }
        // 'all' - show all repos (owned and developer)
        else {
            filteredRepos = repos.filter(repo => repo.role === 'owner' || repo.role === 'developer');
        }

        renderMyRepos(filteredRepos, filter);
    } catch (error) {
        handleAPIError(error, 'loading your repositories');
        document.getElementById('my-repos-list').innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Failed to load repositories. Please try again.</p>
            </div>
        `;
    } finally {
        showLoading(false);
    }
}

function renderMyRepos(repos, filter = 'all') {
    const container = document.getElementById('my-repos-list');
    
    if (!repos || repos.length === 0) {
        let filterText = '';
        if (filter === 'owner') {
            filterText = ' you own';
        } else if (filter === 'developer') {
            filterText = ' you\'re a developer on';
        } else {
            filterText = ' you have access to';
        }
        
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-folder-open"></i>
                <h3>No repositories${filterText}</h3>
                <p>Create or ask to be added to a repository to get started!</p>
            </div>
        `;
        return;
    }

    container.innerHTML = repos.map(repo => {
        return `
            <div class="repo-card" onclick="showRepoDetail(${repo.repo_id})">
                <div style="display: flex; justify-content: space-between; align-items: start; width: 100%;">
                    <div style="flex: 1;">
                        <h3><i class="fas fa-folder"></i> ${repo.reponame}</h3>
                        <div class="repo-meta">
                            <span><i class="fas fa-user"></i> ${repo.maintainer_name}</span>
                            <span class="repo-role">${repo.role.charAt(0).toUpperCase() + repo.role.slice(1)}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}
// Handle browser back/forward buttons
window.addEventListener('popstate', (event) => {
    if (event.state && event.state.page) {
        showPage(event.state.page, true);
    } else {
        // If no state, check URL params
        const urlParams = new URLSearchParams(window.location.search);
        const page = urlParams.get('page') || 'home';
        showPage(page, true);
    }
});

// Set initial state on page load
window.addEventListener('load', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const page = urlParams.get('page');
    if (page && page !== 'home') {
        showPage(page, true);
    } else {
        // Set initial state
        const url = new URL(window.location);
        url.searchParams.set('page', 'home');
        window.history.replaceState({ page: 'home' }, '', url);
    }
});

// Initialize app
const app = new App();

// Initialize page when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    showPage('home');
});