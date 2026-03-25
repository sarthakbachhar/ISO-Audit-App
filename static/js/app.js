/**
 * ISO 27001 Audit App — Frontend JavaScript
 * Handles drag-and-drop upload, check card expansion, and result filtering.
 */

document.addEventListener('DOMContentLoaded', () => {
    initDropZone();
    initFilterTabs();
});

/* ============================================================
   Drag & Drop Upload
   ============================================================ */
function initDropZone() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('configFile');
    const filePreview = document.getElementById('filePreview');
    const fileName = document.getElementById('fileName');
    const fileRemove = document.getElementById('fileRemove');
    const submitBtn = document.getElementById('submitBtn');
    const dropContent = document.querySelector('.drop-zone-content');

    if (!dropZone) return;

    // Click to browse
    dropZone.addEventListener('click', (e) => {
        if (e.target === fileRemove || fileRemove?.contains(e.target)) return;
        fileInput.click();
    });

    // File selected via input
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            showFilePreview(fileInput.files[0]);
        }
    });

    // Drag events
    ['dragenter', 'dragover'].forEach(event => {
        dropZone.addEventListener(event, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add('drag-over');
        });
    });

    ['dragleave', 'drop'].forEach(event => {
        dropZone.addEventListener(event, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove('drag-over');
        });
    });

    dropZone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            const file = files[0];
            if (file.name.endsWith('.json')) {
                // Create a new DataTransfer to set the file on the input
                const dt = new DataTransfer();
                dt.items.add(file);
                fileInput.files = dt.files;
                showFilePreview(file);
            } else {
                showFlash('Please upload a JSON file.', 'error');
            }
        }
    });

    // Remove file
    if (fileRemove) {
        fileRemove.addEventListener('click', (e) => {
            e.stopPropagation();
            fileInput.value = '';
            filePreview.style.display = 'none';
            dropContent.style.display = 'block';
            submitBtn.disabled = true;
        });
    }

    function showFilePreview(file) {
        fileName.textContent = file.name;
        filePreview.style.display = 'flex';
        dropContent.style.display = 'none';
        submitBtn.disabled = false;

        // Animate
        filePreview.style.animation = 'none';
        filePreview.offsetHeight; // trigger reflow
        filePreview.style.animation = 'fadeIn 0.3s ease';
    }
}

/* ============================================================
   Check Card Toggle (Results Page)
   ============================================================ */
function toggleCheck(header) {
    const card = header.closest('.check-card');
    card.classList.toggle('expanded');
}

/* ============================================================
   Filter Tabs (Results Page)
   ============================================================ */
function initFilterTabs() {
    const tabs = document.querySelectorAll('.filter-tab');
    if (tabs.length === 0) return;

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Update active tab
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            const filter = tab.dataset.filter;
            const cards = document.querySelectorAll('.check-card');

            cards.forEach(card => {
                if (filter === 'all') {
                    card.style.display = '';
                } else {
                    card.style.display = card.dataset.status === filter ? '' : 'none';
                }
            });

            // Also show/hide control group headers if all their cards are hidden
            const groups = document.querySelectorAll('.control-group');
            groups.forEach(group => {
                const visibleCards = group.querySelectorAll('.check-card:not([style*="display: none"])');
                group.style.display = visibleCards.length > 0 ? '' : 'none';
            });
        });
    });
}

/* ============================================================
   Flash Message Helper
   ============================================================ */
function showFlash(message, category = 'info') {
    const container = document.querySelector('.flash-container') || createFlashContainer();

    const flash = document.createElement('div');
    flash.className = `flash-message flash-${category}`;
    flash.innerHTML = `
        <span class="flash-icon">${category === 'error' ? '✕' : 'ℹ'}</span>
        ${message}
        <button class="flash-close" onclick="this.parentElement.remove()">×</button>
    `;
    container.appendChild(flash);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (flash.parentElement) {
            flash.style.opacity = '0';
            flash.style.transform = 'translateY(-10px)';
            setTimeout(() => flash.remove(), 300);
        }
    }, 5000);
}

function createFlashContainer() {
    const container = document.createElement('div');
    container.className = 'flash-container';
    document.querySelector('.navbar')?.after(container) ||
        document.body.prepend(container);
    return container;
}
