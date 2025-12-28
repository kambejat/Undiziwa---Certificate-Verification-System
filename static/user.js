const users = {{ users| tojson | safe }};
const currentUserRole = '{{ current_user_role }}';

let page = 1;
const pageSize = 10;
let filteredUsers = [...users];
let currentUser = null;

// DOM elements
const usersBody = document.getElementById('users-body');
const searchInput = document.getElementById('search-input');
const filterRole = document.getElementById('filter-role');
const filterStatus = document.getElementById('filter-status');
const prevPageBtn = document.getElementById('prev-page');
const nextPageBtn = document.getElementById('next-page');
const currentPageEl = document.getElementById('current-page');
const totalPagesEl = document.getElementById('total-pages');
const toastEl = document.getElementById('toast');
const toastMessage = document.getElementById('toast-message');
const modal = document.getElementById('modal');
const modalRole = document.getElementById('modal-role');
const modalStatus = document.getElementById('modal-status');
const modalCancel = document.getElementById('modal-cancel');
const modalSave = document.getElementById('modal-save');
const modalReset = document.getElementById('modal-reset');

function showToast(message, isError = false) {
    toastMessage.textContent = message;
    toastEl.className = isError ? 'fixed top-4 right-4 px-4 py-2 rounded shadow bg-red-600 text-white' :
        'fixed top-4 right-4 px-4 py-2 rounded shadow bg-green-600 text-white';
    toastEl.style.display = 'block';
    setTimeout(() => toastEl.style.display = 'none', 2500);
}

function renderTable() {
    usersBody.innerHTML = '';

    const start = (page - 1) * pageSize;
    const paginated = filteredUsers.slice(start, start + pageSize);
    paginated.forEach(user => {
        const tr = document.createElement('tr'); // <-- THIS WAS MISSING
        tr.className = 'hover:bg-blue-50';

        const userId = user.user_id ?? '';
        const username = user.username ?? '';
        const email = user.email ?? '';
        const role = user.role ?? '';
        const isActive = user.is_active ?? false;

        tr.innerHTML = `
              <td class="px-6 py-4">${userId}</td>
              <td class="px-6 py-4">${username}</td>
              <td class="px-6 py-4">${email}</td>
              <td class="px-6 py-4 uppercase">${role}</td>
              <td class="px-6 py-4">
                  <span class="px-3 py-1 rounded text-white text-sm ${isActive ? 'bg-green-600' : 'bg-red-600'}">
                      ${isActive ? 'Active' : 'Inactive'}
                  </span>
              </td>
              <td class="px-6 py-4">
                  ${['super_admin', 'gov_admin'].includes(currentUserRole) ?
                `<button class="bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700 manage-btn">Manage</button>` : ''}
              </td>
          `;

        // Attach Manage button listener
        const manageBtn = tr.querySelector('.manage-btn');
        if (manageBtn) {
            manageBtn.addEventListener('click', () => openModal(user));
        }

        usersBody.appendChild(tr);
    });
    currentPageEl.textContent = page;
    totalPagesEl.textContent = Math.ceil(filteredUsers.length / pageSize);

    prevPageBtn.disabled = page === 1;
    nextPageBtn.disabled = page === Math.ceil(filteredUsers.length / pageSize);
}

function filterUsers() {
    const searchTerm = searchInput.value.toLowerCase();
    const role = filterRole.value;
    const status = filterStatus.value;

    filteredUsers = users.filter(u => {
        const username = u.username || '';
        const email = u.email || '';

        const matchesSearch = username.toLowerCase().includes(searchTerm) || email.toLowerCase().includes(searchTerm);
        const matchesRole = role ? u.role === role : true;
        const matchesStatus = status ? Boolean(u.is_active) === (status === 'true') : true;

        return matchesSearch && matchesRole && matchesStatus;
    });
    page = 1;
    renderTable();
}

searchInput.addEventListener('input', filterUsers);
filterRole.addEventListener('change', filterUsers);
filterStatus.addEventListener('change', filterUsers);

prevPageBtn.addEventListener('click', () => { page--; renderTable(); });
nextPageBtn.addEventListener('click', () => { page++; renderTable(); });

// Modal functions
function openModal(user) {
    currentUser = user;
    modal.style.display = 'flex';
    modalRole.value = user.role;
    modalStatus.value = user.is_active.toString();
}

modalCancel.addEventListener('click', () => { modal.style.display = 'none'; });
modalSave.addEventListener('click', async () => {
    if (!currentUser) return;

    const response = await fetch(`/api/users/${currentUser.user_id}/permission`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            role: modalRole.value,
            is_active: modalStatus.value === 'true'
        })
    });

    if (response.ok) {
        const updated = await response.json();
        const index = users.findIndex(u => u.user_id === updated.user_id);
        users[index] = updated;
        filterUsers();
        modal.style.display = 'none';
        showToast('Permissions updated');
    } else {
        showToast('Failed to update user', true);
    }
});

modalReset.addEventListener('click', async () => {
    if (!currentUser) return;
    const confirmReset = confirm("Reset this user's password to a new random password?");
    if (!confirmReset) return;

    const response = await fetch(`/api/users/${currentUser.user_id}/reset-password`, { method: 'PATCH' });
    if (response.ok) {
        showToast('Password reset successfully');
    } else {
        showToast('Reset failed', true);
    }
});

const createModal = document.getElementById('create-modal');
const openCreateBtn = document.getElementById('open-create-modal');
const createCancel = document.getElementById('create-cancel');
const createSave = document.getElementById('create-save');

openCreateBtn.addEventListener('click', () => {
    createModal.style.display = 'flex';
});

createCancel.addEventListener('click', () => {
    createModal.style.display = 'none';
});

createSave.addEventListener('click', async () => {
    const payload = {
        username: document.getElementById('create-username').value.trim(),
        full_name: document.getElementById('create-fullname').value.trim(),
        email: document.getElementById('create-email').value.trim(),
        phone: document.getElementById('create-phone').value.trim(),
        password: document.getElementById('create-password').value,
        role: document.getElementById('create-role').value,
        is_active: document.getElementById('create-status').value === 'true'
    };


    /* Institution-scoped creation (SAFE) */
    const institutionSelect = document.getElementById('create-institution');
    if (institutionSelect && institutionSelect.value) {
        payload.institution_id = parseInt(institutionSelect.value);
    }

    // Validation
    if (!payload.username || !payload.email || !payload.password || !payload.role) {
        showToast('Please fill required fields', true);
        return;
    }

    console.log(payload)

    const response = await fetch('/api/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });

    if (response.ok) {
        const newUser = await response.json();
        users.unshift(newUser);
        filterUsers();
        createModal.style.display = 'none';
        showToast('User created successfully');
    } else {
        const err = await response.json().catch(() => ({}));
        showToast(err.message || 'Failed to create user', true);
    }
});

// Initial render
renderTable();