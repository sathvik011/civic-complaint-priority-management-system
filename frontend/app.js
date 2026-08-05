// ===============================
// API & Utility Functions
// ===================================
const API_BASE_URL = "http://127.0.0.1:5000/api";

function getLoggedInUser() {
    return JSON.parse(sessionStorage.getItem('loggedInUser'));
}

function isLoggedIn() {
    return !!sessionStorage.getItem('loggedInUser');
}

function setLoggedInUser(user) {
    sessionStorage.setItem('loggedInUser', JSON.stringify(user));
}

function clearLoggedInUser() {
    sessionStorage.removeItem('loggedInUser');
    window.location.href = 'index.html';
}

// ===============================
// Main Logic
// ===================================
document.addEventListener('DOMContentLoaded', () => {

    // ===============================
    // Admin Login
    // ===================================
    const adminLoginForm = document.getElementById("adminLoginForm");
    if (adminLoginForm) {
        adminLoginForm.addEventListener("submit", async e => {
            e.preventDefault();

            const username = document.getElementById("admin-user").value.trim();
            const password = document.getElementById("admin-pass").value.trim();

            try {
                const response = await fetch(`${API_BASE_URL}/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });

                const result = await response.json();
                if (response.ok) {
                    setLoggedInUser(result);
                    window.location.href = "admin-dashboard.html";
                } else {
                    alert(result.error);
                }
            } catch (error) {
                console.error("Login failed:", error);
                alert("Login failed. Check server connection.");
            }
        });
    }

    // ===============================
    // Citizen Signup
    // ===================================
    const signupForm = document.getElementById('signupForm');
    if (signupForm) {
        signupForm.addEventListener('submit', async e => {
            e.preventDefault();
            const name = document.getElementById('signup-name').value;
            const email = document.getElementById('signup-email').value;
            const password = document.getElementById('signup-password').value;

            try {
                const response = await fetch(`${API_BASE_URL}/signup`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, email, password })
                });

                const result = await response.json();
                if (response.ok) {
                    alert('Signup successful! Please log in.');
                    window.location.href = 'citizen-login.html';
                } else {
                    alert(result.error);
                }
            } catch (error) {
                console.error("Signup failed:", error);
                alert("Signup failed. Check server connection.");
            }
        });
    }

    // ===============================
    // Citizen Login
    // ===================================
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async e => {
            e.preventDefault();
            const email = document.getElementById('citizen-email').value;
            const password = document.getElementById('citizen-password').value;

            try {
                const response = await fetch(`${API_BASE_URL}/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });

                const result = await response.json();
                if (response.ok) {
                    setLoggedInUser(result);
                    window.location.href = 'citizen-dashboard.html';
                } else {
                    alert(result.error);
                }
            } catch (error) {
                console.error("Login failed:", error);
                alert("Login failed. Check server connection.");
            }
        });
    }

    // ===============================
    // New Complaint Submission
    // ===================================
    const complaintForm = document.getElementById('complaintForm');
    if (complaintForm) {
        complaintForm.addEventListener('submit', submitComplaint);
    }

    async function submitComplaint(event) {
        event.preventDefault();

        const user = getLoggedInUser();
        if (!user) {
            alert("You must be logged in to submit a complaint.");
            window.location.href = "citizen-login.html";
            return;
        }

        const title = document.getElementById("complaint-title").value.trim();
        const description = document.getElementById("complaint-desc").value.trim();
        const location = document.getElementById("complaint-location").value.trim();

        const coords = JSON.parse(sessionStorage.getItem('complaintCoords') || 'null');
        sessionStorage.removeItem('complaintCoords');

        if (!title || !description || !location) {
            alert("Please fill in all fields.");
            return;
        }

        try {
            // Collect images if the upload helper is available (defined in new-complaint.html)
            let images = [];
            if (typeof window.getSelectedImagesBase64 === 'function') {
                images = await window.getSelectedImagesBase64();
            }

            // Collect videos if the upload helper is available
            let videos = [];
            if (typeof window.getSelectedVideosBase64 === 'function') {
                videos = await window.getSelectedVideosBase64();
            }

            const requestBody = {
                title,
                description,
                location,
                user_id: user.user_id,
                images, // array of base64 data URLs (may be empty)
                videos, // array of base64 data URLs (may be empty)
            };

            if (coords) {
                requestBody.lat = coords.lat;
                requestBody.lon = coords.lng;
            }

            const response = await fetch(`${API_BASE_URL}/complaints`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(requestBody)
            });

            const result = await response.json();
            if (response.ok) {
                const complaint = result.complaint;
                alert(`Complaint submitted! Assigned to ${complaint.department} with priority ${complaint.priority}.`);
                window.location.href = "citizen-dashboard.html";
            } else {
                alert("Submission failed: " + result.error);
            }
        } catch (err) {
            console.error("Error during complaint submission:", err);
            alert("Server error. Check console.");
        }
    }

    // ===============================
    // Render Citizen Dashboard
    // ===================================
    const citizenTableBody = document.querySelector('#complaintsTable tbody');
    if (citizenTableBody) {
        renderCitizenComplaints();

        document.getElementById('sortOption').addEventListener('change', renderCitizenComplaints);
        document.getElementById('filterStatus').addEventListener('change', renderCitizenComplaints);
        document.getElementById('searchBox').addEventListener('input', renderCitizenComplaints);
    }

    async function renderCitizenComplaints() {
        const user = getLoggedInUser();
        if (!user) return;

        try {
            const response = await fetch(`${API_BASE_URL}/complaints/user/${user.user_id}`);
            let complaints = await response.json();

            const filterVal = document.getElementById('filterStatus').value;
            if (filterVal !== "all") {
                complaints = complaints.filter(c => c.status === filterVal);
            }

            const searchVal = document.getElementById('searchBox').value.toLowerCase();
            if (searchVal) {
                complaints = complaints.filter(c =>
                    c.title.toLowerCase().includes(searchVal) ||
                    c.description.toLowerCase().includes(searchVal) ||
                    c.location.toLowerCase().includes(searchVal) ||
                    c.department.toLowerCase().includes(searchVal)
                );
            }

            const sortVal = document.getElementById('sortOption').value;
            complaints.sort((a, b) => {
                if (sortVal === "date") return new Date(b.registered) - new Date(a.registered);
                return (a[sortVal] || '').localeCompare(b[sortVal] || '');
            });

            citizenTableBody.innerHTML = "";
            complaints.forEach(c => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${c.title}</td>
                    <td style="max-width:200px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="${c.description || ''}">${c.description || '—'}</td>
                    <td>${c.location}</td>
                    <td>${c.department}</td>
                    <td>${c.status}</td>
                    <td>${c.registered.split('T')[0]}</td>
                    <td><button onclick="deleteComplaint('${c.id}')">Delete</button></td>
                `;
                citizenTableBody.appendChild(row);
            });
        } catch (error) {
            console.error("Error fetching complaints:", error);
        }
    }

    // ===============================
    // Admin Dashboard
    // ===================================
    const adminTableBody = document.getElementById('adminComplaintsBody');
    if (adminTableBody) {
        renderAdminComplaints();
        document.getElementById('adminSort').addEventListener('change', () => {
            renderAdminComplaints(document.getElementById('adminSort').value);
        });
    }

    async function renderAdminComplaints(sortBy = 'date') {
        const user = getLoggedInUser();
        if (!user) return;

        try {
            const response = await fetch(`${API_BASE_URL}/complaints`);
            let complaints = await response.json();

            const welcomeEl = document.getElementById("welcomeAdmin");
            if (welcomeEl) {
                if (user.role === "superadmin") {
                    welcomeEl.textContent = "Welcome Super Admin — You can manage all complaints.";
                } else {
                    complaints = complaints.filter(c => c.department === user.department);
                    welcomeEl.textContent = `Welcome ${user.department} Admin — You can manage only your department's complaints.`;
                }
            }

            // Sort
            if (sortBy === 'priority') {
                const priorityOrder = { '1': 1, '2': 2, '3': 3 };
                complaints.sort((a, b) =>
                    (priorityOrder[a.priority] || 4) - (priorityOrder[b.priority] || 4)
                );
            } else {
                complaints.sort((a, b) => {
                    if (sortBy === "date") return new Date(b.registered) - new Date(a.registered);
                    if (!a[sortBy]) return 1;
                    if (!b[sortBy]) return -1;
                    return a[sortBy].localeCompare(b[sortBy]);
                });
            }

            adminTableBody.innerHTML = "";
            complaints.forEach(c => {
                // Build photos cell
                const hasImages = Array.isArray(c.images) && c.images.length > 0;
                const photosCell = hasImages
                    ? `<button class="btn-imgs" onclick='viewComplaintImages(${JSON.stringify(c.images)})'>📷 ${c.images.length} photo${c.images.length > 1 ? 's' : ''}</button>`
                    : `<span style="color:#bbb;font-size:0.85em;">—</span>`;

                // Build videos cell
                const hasVideos = Array.isArray(c.videos) && c.videos.length > 0;
                const videosCell = hasVideos
                    ? `<button class="btn-imgs" onclick='viewComplaintVideos(${JSON.stringify(c.videos)})'>🎥 ${c.videos.length} video${c.videos.length > 1 ? 's' : ''}</button>`
                    : `<span style="color:#bbb;font-size:0.85em;">—</span>`;

                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>${c.id}</td>
                    <td>${c.title}</td>
                    <td style="max-width:200px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="${c.description || ''}">${c.description || '—'}</td>
                    <td>${c.location}</td>
                    <td>${c.department}</td>
                    <td>${c.citizen_email || '—'}</td>
                    <td>${c.priority || '—'}</td>
                    <td>${c.registered.split('T')[0]}</td>
                    <td>${c.resolved ? c.resolved.split('T')[0] : '—'}</td>
                    <td>
                        <select onchange="updateComplaintStatus('${c.id}', this.value)">
                            <option value="Registered" ${c.status === "Registered" ? "selected" : ""}>Registered</option>
                            <option value="In Progress" ${c.status === "In Progress" ? "selected" : ""}>In Progress</option>
                            <option value="Resolved" ${c.status === "Resolved" ? "selected" : ""}>Resolved</option>
                        </select>
                    </td>
                    <td>${photosCell}</td>
                    <td>${videosCell}</td>
                    <td><button onclick="deleteComplaint('${c.id}')">Delete</button></td>
                `;
                adminTableBody.appendChild(row);
            });
        } catch (error) {
            console.error("Error fetching complaints:", error);
        }
    }

    // ===============================
    // Delete & Update
    // ===================================
    window.deleteComplaint = async function (id) {
        if (!confirm("Are you sure you want to delete this complaint?")) return;
        try {
            const response = await fetch(`${API_BASE_URL}/complaints/${id}`, { method: 'DELETE' });
            if (response.ok) {
                alert("Complaint deleted.");
                location.reload();
            } else {
                const result = await response.json();
                alert(result.error);
            }
        } catch (error) {
            console.error("Error deleting complaint:", error);
            alert("Error deleting complaint. Check server connection.");
        }
    };

    window.updateComplaintStatus = async function (id, status) {
        try {
            const response = await fetch(`${API_BASE_URL}/complaints/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status })
            });

            if (response.ok) {
                location.reload();
            } else {
                const result = await response.json();
                alert(result.error);
            }
        } catch (error) {
            console.error("Error updating complaint:", error);
            alert("Error updating complaint. Check server connection.");
        }
    };

    // Logout — only attach to nav links that are genuinely logout buttons
    // (links pointing to index.html that are labelled "Logout")
    document.querySelectorAll('a[href="index.html"]').forEach(link => {
        if (link.textContent.trim() === 'Logout') {
            link.addEventListener('click', e => {
                e.preventDefault();
                clearLoggedInUser();
            });
        }
    });
});

// ===============================
// Image Lightbox Viewer (global — called from inline onclick)
// ===================================
window.viewComplaintImages = function (images) {
    const existing = document.getElementById('imgModal');
    if (existing) existing.remove();

    let current = 0;

    const modal = document.createElement('div');
    modal.id = 'imgModal';
    modal.style.cssText = `
        position:fixed;inset:0;z-index:9999;
        background:rgba(0,0,0,0.88);
        display:flex;flex-direction:column;align-items:center;justify-content:center;
        padding:20px;
    `;

    modal.innerHTML = `
        <div style="position:relative;max-width:860px;width:100%;background:#1a1a1a;border-radius:14px;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,0.6);">
            <div style="display:flex;justify-content:space-between;align-items:center;padding:14px 20px;border-bottom:1px solid #333;">
                <span style="color:#ccc;font-size:0.9em;font-family:sans-serif;">
                    📷 Complaint Photos — <span id="imgCounter">1 / ${images.length}</span>
                </span>
                <button onclick="document.getElementById('imgModal').remove()"
                    style="background:none;border:none;color:#aaa;font-size:1.4em;cursor:pointer;line-height:1;">✕</button>
            </div>
            <div style="position:relative;min-height:420px;display:flex;align-items:center;justify-content:center;background:#111;">
                <img id="modalImg" src="${images[0]}" style="max-width:100%;max-height:65vh;object-fit:contain;display:block;" />
                ${images.length > 1 ? `
                <button id="prevBtn" onclick="changeModalImage(-1)" style="
                    position:absolute;left:12px;
                    background:rgba(255,255,255,0.12);border:none;color:#fff;
                    font-size:1.6em;padding:10px 14px;border-radius:50%;cursor:pointer;">‹</button>
                <button id="nextBtn" onclick="changeModalImage(1)" style="
                    position:absolute;right:12px;
                    background:rgba(255,255,255,0.12);border:none;color:#fff;
                    font-size:1.6em;padding:10px 14px;border-radius:50%;cursor:pointer;">›</button>` : ''}
            </div>
            <div id="thumbStrip" style="display:flex;gap:8px;padding:12px 16px;overflow-x:auto;background:#161616;"></div>
        </div>
    `;

    document.body.appendChild(modal);

    const strip = modal.querySelector('#thumbStrip');
    images.forEach((src, i) => {
        const thumb = document.createElement('img');
        thumb.src = src;
        thumb.style.cssText = `width:64px;height:64px;object-fit:cover;border-radius:6px;cursor:pointer;border:2px solid ${i === 0 ? '#4a90e2' : 'transparent'};flex-shrink:0;transition:border-color 0.2s;`;
        thumb.onclick = () => goToImage(i);
        strip.appendChild(thumb);
    });

    function goToImage(i) {
        current = i;
        modal.querySelector('#modalImg').src = images[i];
        modal.querySelector('#imgCounter').textContent = `${i + 1} / ${images.length}`;
        strip.querySelectorAll('img').forEach((t, j) => t.style.borderColor = j === i ? '#4a90e2' : 'transparent');
    }

    window.changeModalImage = function (dir) {
        goToImage((current + dir + images.length) % images.length);
    };

    // Close on backdrop click
    modal.addEventListener('click', e => { if (e.target === modal) modal.remove(); });

    // Keyboard navigation
    const onKey = e => {
        if (e.key === 'ArrowRight') window.changeModalImage(1);
        if (e.key === 'ArrowLeft') window.changeModalImage(-1);
        if (e.key === 'Escape') { modal.remove(); document.removeEventListener('keydown', onKey); }
    };
    document.addEventListener('keydown', onKey);
};

// ===============================
// Video Modal Viewer (global — called from inline onclick)
// ===================================
window.viewComplaintVideos = function (videos) {
    const existing = document.getElementById('videoModal');
    if (existing) existing.remove();

    let current = 0;

    const modal = document.createElement('div');
    modal.id = 'videoModal';
    modal.style.cssText = `
        position:fixed;inset:0;z-index:9999;
        background:rgba(0,0,0,0.92);
        display:flex;flex-direction:column;align-items:center;justify-content:center;
        padding:20px;
    `;

    modal.innerHTML = `
        <div style="position:relative;max-width:860px;width:100%;background:#1a1a1a;border-radius:14px;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,0.7);">
            <div style="display:flex;justify-content:space-between;align-items:center;padding:14px 20px;border-bottom:1px solid #333;">
                <span style="color:#ccc;font-size:0.9em;font-family:sans-serif;">
                    🎥 Complaint Videos — <span id="vidCounter">1 / ${videos.length}</span>
                </span>
                <button onclick="document.getElementById('videoModal').remove()"
                    style="background:none;border:none;color:#aaa;font-size:1.4em;cursor:pointer;line-height:1;">✕</button>
            </div>
            <div style="position:relative;min-height:380px;display:flex;align-items:center;justify-content:center;background:#000;">
                <video id="modalVideo" src="${videos[0]}" controls autoplay
                    style="max-width:100%;max-height:60vh;display:block;outline:none;"></video>
                ${videos.length > 1 ? `
                <button id="vidPrevBtn" onclick="changeModalVideo(-1)" style="
                    position:absolute;left:12px;
                    background:rgba(255,255,255,0.12);border:none;color:#fff;
                    font-size:1.6em;padding:10px 14px;border-radius:50%;cursor:pointer;">‹</button>
                <button id="vidNextBtn" onclick="changeModalVideo(1)" style="
                    position:absolute;right:12px;
                    background:rgba(255,255,255,0.12);border:none;color:#fff;
                    font-size:1.6em;padding:10px 14px;border-radius:50%;cursor:pointer;">›</button>` : ''}
            </div>
            <div id="videoThumbStrip" style="display:flex;gap:8px;padding:12px 16px;overflow-x:auto;background:#161616;"></div>
        </div>
    `;

    document.body.appendChild(modal);

    const strip = modal.querySelector('#videoThumbStrip');
    videos.forEach((src, i) => {
        const thumb = document.createElement('video');
        thumb.src = src;
        thumb.muted = true;
        thumb.style.cssText = `width:80px;height:52px;object-fit:cover;border-radius:6px;cursor:pointer;border:2px solid ${i === 0 ? '#4a90e2' : 'transparent'};flex-shrink:0;transition:border-color 0.2s;background:#000;`;
        thumb.onclick = () => goToVideo(i);
        strip.appendChild(thumb);
    });

    function goToVideo(i) {
        current = i;
        const vid = modal.querySelector('#modalVideo');
        vid.pause();
        vid.src = videos[i];
        vid.load();
        vid.play().catch(() => {});
        modal.querySelector('#vidCounter').textContent = `${i + 1} / ${videos.length}`;
        strip.querySelectorAll('video').forEach((t, j) => t.style.borderColor = j === i ? '#4a90e2' : 'transparent');
    }

    window.changeModalVideo = function (dir) {
        goToVideo((current + dir + videos.length) % videos.length);
    };

    // Close on backdrop click (but not the inner panel)
    modal.addEventListener('click', e => { if (e.target === modal) modal.remove(); });

    // Keyboard navigation
    const onVidKey = e => {
        if (e.key === 'ArrowRight') window.changeModalVideo(1);
        if (e.key === 'ArrowLeft') window.changeModalVideo(-1);
        if (e.key === 'Escape') { modal.remove(); document.removeEventListener('keydown', onVidKey); }
    };
    document.addEventListener('keydown', onVidKey);
};
