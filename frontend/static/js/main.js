/**
 * Meeting Insights Studio — Comprehensive Client Application Logic
 */

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initSidebar();
  initHealthPopovers();
  initDashboardToolbar();
  initCardMenusAndActions();
  initLiveStatusPolling();
  initConflictTrackerActions();
  initDemoLoader();
  initEndpointDiagnostics();
  initPreMeetingBrief();
  initTabs();
  initTaskToggles();
  initTranscriptSearch();
  initChat();
  initTimestampJumps();
  initLiveMeeting();
  initKnowledgeGraphPage();
});

// ==============================================================================
// 1. Toast Notification System
// ==============================================================================
function showToast(message, type = 'info', duration = 3500) {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  const icon = type === 'success' ? '✓' : (type === 'error' ? '⚠️' : 'ℹ️');
  toast.innerHTML = `<span style="font-weight: 700;">${icon}</span><span>${escapeHtml(message)}</span>`;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ==============================================================================
// 2. Theme Toggle (Dark / Light with LocalStorage & System Preference)
// ==============================================================================
function initTheme() {
  const toggleBtn = document.getElementById('theme-toggle-btn');
  const darkIcon = document.querySelector('.theme-icon-dark');
  const lightIcon = document.querySelector('.theme-icon-light');

  // Detect saved preference or system preference
  const savedTheme = localStorage.getItem('meeting_studio_theme');
  const systemPrefersLight = window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches;
  const initialTheme = savedTheme || (systemPrefersLight ? 'light' : 'dark');

  applyTheme(initialTheme);

  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      applyTheme(newTheme);
      localStorage.setItem('meeting_studio_theme', newTheme);
      showToast(`Switched to ${newTheme} theme`, 'info', 2000);
    });
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    document.body.className = `theme-${theme}`;
    if (darkIcon && lightIcon) {
      if (theme === 'light') {
        darkIcon.style.display = 'none';
        lightIcon.style.display = 'inline';
      } else {
        darkIcon.style.display = 'inline';
        lightIcon.style.display = 'none';
      }
    }
  }
}

// ==============================================================================
// 3. Collapsible Sidebar & Mobile Navigation
// ==============================================================================
function initSidebar() {
  const sidebar = document.getElementById('app-sidebar');
  const collapseBtn = document.getElementById('sidebar-collapse-btn');
  const mobileBtn = document.getElementById('mobile-menu-btn');
  const backdrop = document.getElementById('sidebar-backdrop');

  if (collapseBtn && sidebar) {
    collapseBtn.addEventListener('click', () => {
      sidebar.classList.toggle('collapsed');
    });
  }

  if (mobileBtn && sidebar) {
    mobileBtn.addEventListener('click', () => {
      sidebar.classList.toggle('drawer-open');
      document.body.classList.toggle('drawer-active');
    });
  }

  if (backdrop && sidebar) {
    backdrop.addEventListener('click', () => {
      sidebar.classList.remove('drawer-open');
      document.body.classList.remove('drawer-active');
    });
  }
}

// ==============================================================================
// 4. Meeting Health Score Popovers (Prompt 1)
// ==============================================================================
function initHealthPopovers() {
  document.querySelectorAll('.health-score-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const mId = btn.getAttribute('data-meeting-id');
      const popover = document.getElementById(`popover-health-${mId}`);
      if (!popover) return;

      // Close all other health popovers first
      document.querySelectorAll('.health-popover').forEach(p => {
        if (p !== popover) p.style.display = 'none';
      });

      const isHidden = popover.style.display === 'none' || !popover.style.display;
      popover.style.display = isHidden ? 'block' : 'none';
    });
  });

  // Close button inside popover
  document.querySelectorAll('.popover-close-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const targetId = btn.getAttribute('data-target');
      const target = document.getElementById(targetId);
      if (target) target.style.display = 'none';
    });
  });

  // Global click outside to dismiss popover
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.health-badge-wrapper')) {
      document.querySelectorAll('.health-popover').forEach(p => p.style.display = 'none');
    }
  });
}

// ==============================================================================
// 5. Toolbar: Search, Filters, Sort & URL Query String Sync (Prompt 2)
// ==============================================================================
function initDashboardToolbar() {
  const searchInput = document.getElementById('meeting-search-input');
  const clearSearchBtn = document.getElementById('search-clear-btn');
  const filterType = document.getElementById('filter-type');
  const filterStatus = document.getElementById('filter-status');
  const filterTag = document.getElementById('filter-tag');
  const filterParticipant = document.getElementById('filter-participant');
  const filterFrom = document.getElementById('filter-from-date');
  const filterTo = document.getElementById('filter-to-date');
  const filterSort = document.getElementById('filter-sort');
  const chipsSection = document.getElementById('active-filter-chips');
  const chipsContainer = document.getElementById('chips-container');
  const clearAllBtn = document.getElementById('clear-all-filters-btn');
  const emptyClearBtn = document.getElementById('empty-clear-btn');

  if (!searchInput && !filterType) return;

  // 1. Read URL query parameters on load
  const urlParams = new URLSearchParams(window.location.search);
  if (searchInput && urlParams.get('q')) searchInput.value = urlParams.get('q');
  if (filterType && urlParams.get('type')) filterType.value = urlParams.get('type');
  if (filterStatus && urlParams.get('status')) filterStatus.value = urlParams.get('status');
  if (filterTag && urlParams.get('tag')) filterTag.value = urlParams.get('tag');
  if (filterParticipant && urlParams.get('participant')) filterParticipant.value = urlParams.get('participant');
  if (filterFrom && urlParams.get('from')) filterFrom.value = urlParams.get('from');
  if (filterTo && urlParams.get('to')) filterTo.value = urlParams.get('to');
  if (filterSort && urlParams.get('sort')) filterSort.value = urlParams.get('sort');

  // Debounced search
  let debounceTimeout = null;
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      if (clearSearchBtn) clearSearchBtn.style.display = searchInput.value ? 'block' : 'none';
      clearTimeout(debounceTimeout);
      debounceTimeout = setTimeout(() => applyFiltersAndSort(), 200);
    });

    if (clearSearchBtn) {
      clearSearchBtn.addEventListener('click', () => {
        searchInput.value = '';
        clearSearchBtn.style.display = 'none';
        applyFiltersAndSort();
      });
    }
  }

  // Filter change listeners
  [filterType, filterStatus, filterTag, filterParticipant, filterFrom, filterTo, filterSort].forEach(el => {
    if (el) el.addEventListener('change', () => applyFiltersAndSort());
  });

  if (clearAllBtn) {
    clearAllBtn.addEventListener('click', () => resetAllFilters());
  }
  if (emptyClearBtn) {
    emptyClearBtn.addEventListener('click', () => resetAllFilters());
  }

  function resetAllFilters() {
    if (searchInput) {
      searchInput.value = '';
      if (clearSearchBtn) clearSearchBtn.style.display = 'none';
    }
    if (filterType) filterType.value = 'all';
    if (filterStatus) filterStatus.value = 'all';
    if (filterTag) filterTag.value = 'all';
    if (filterParticipant) filterParticipant.value = 'all';
    if (filterFrom) filterFrom.value = '';
    if (filterTo) filterTo.value = '';
    if (filterSort) filterSort.value = 'newest';
    applyFiltersAndSort();
  }

  function applyFiltersAndSort() {
    const q = searchInput ? searchInput.value.trim().toLowerCase() : '';
    const type = filterType ? filterType.value.toLowerCase() : 'all';
    const status = filterStatus ? filterStatus.value.toLowerCase() : 'all';
    const tag = filterTag ? filterTag.value.toLowerCase() : 'all';
    const part = filterParticipant ? filterParticipant.value.toLowerCase() : 'all';
    const fromDate = filterFrom ? filterFrom.value : '';
    const toDate = filterTo ? filterTo.value : '';
    const sort = filterSort ? filterSort.value : 'newest';

    // 2. Synchronize URL query string
    const params = new URLSearchParams();
    if (q) params.set('q', q);
    if (type !== 'all') params.set('type', type);
    if (status !== 'all') params.set('status', status);
    if (tag !== 'all') params.set('tag', tag);
    if (part !== 'all') params.set('participant', part);
    if (fromDate) params.set('from', fromDate);
    if (toDate) params.set('to', toDate);
    if (sort !== 'newest') params.set('sort', sort);

    const newUrl = window.location.pathname + (params.toString() ? `?${params.toString()}` : '');
    window.history.replaceState({}, '', newUrl);

    // 3. Render active filter chips
    renderFilterChips({ q, type, status, tag, part, fromDate, toDate });

    // 4. Client-side card filtering and sorting
    const cards = Array.from(document.querySelectorAll('.meeting-card'));
    let visibleCount = 0;

    cards.forEach(card => {
      const cardTitle = card.getAttribute('data-title') || '';
      const cardSummary = card.getAttribute('data-summary') || '';
      const cardType = card.getAttribute('data-type') || '';
      const cardStatus = card.getAttribute('data-status') || '';
      const cardDate = card.getAttribute('data-date') || '';
      const cardTags = card.getAttribute('data-tags') || '';
      const cardSpeakers = card.getAttribute('data-speakers') || '';

      let match = true;

      // Type filter
      if (type !== 'all' && cardType !== type) match = false;
      // Status filter
      if (status !== 'all' && cardStatus !== status) match = false;
      // Tag filter
      if (tag !== 'all' && !cardTags.includes(tag)) match = false;
      // Participant filter
      if (part !== 'all' && !cardSpeakers.includes(part)) match = false;
      // Date filters
      if (fromDate && cardDate < fromDate) match = false;
      if (toDate && cardDate > toDate) match = false;

      // Text search match (title, summary, tags, speakers)
      if (q && match) {
        const textToSearch = `${cardTitle} ${cardSummary} ${cardTags} ${cardSpeakers}`;
        if (!textToSearch.includes(q)) {
          match = false;
        }
      }

      if (match) {
        card.style.display = 'flex';
        visibleCount++;
      } else {
        card.style.display = 'none';
      }
    });

    // 5. Sort visible cards
    const grid = document.getElementById('meetings-cards-grid');
    if (grid) {
      cards.sort((a, b) => {
        const dateA = a.getAttribute('data-date') || '';
        const dateB = b.getAttribute('data-date') || '';
        const healthA = parseInt(a.getAttribute('data-health') || '0', 10);
        const healthB = parseInt(b.getAttribute('data-health') || '0', 10);
        const titleA = a.getAttribute('data-title') || '';
        const titleB = b.getAttribute('data-title') || '';

        if (sort === 'oldest') return dateA.localeCompare(dateB);
        if (sort === 'highest_health') return healthB - healthA;
        if (sort === 'lowest_health') return healthA - healthB;
        if (sort === 'title_az') return titleA.localeCompare(titleB);
        return dateB.localeCompare(dateA); // Default: newest
      });

      cards.forEach(c => grid.appendChild(c));
    }

    // 6. Update counts and empty state
    const counterPill = document.getElementById('meeting-counter-pill');
    if (counterPill) {
      counterPill.textContent = `${visibleCount} of ${cards.length} meetings`;
    }

    const emptyState = document.getElementById('meetings-empty-state');
    if (emptyState) {
      emptyState.style.display = visibleCount === 0 ? 'block' : 'none';
    }
  }

  function renderFilterChips({ q, type, status, tag, part, fromDate, toDate }) {
    if (!chipsContainer || !chipsSection) return;
    chipsContainer.innerHTML = '';
    const activeFilters = [];

    if (q) activeFilters.push({ label: `Search: "${q}"`, clear: () => { if (searchInput) searchInput.value = ''; } });
    if (type !== 'all') activeFilters.push({ label: `Type: ${type}`, clear: () => { if (filterType) filterType.value = 'all'; } });
    if (status !== 'all') activeFilters.push({ label: `Status: ${status}`, clear: () => { if (filterStatus) filterStatus.value = 'all'; } });
    if (tag !== 'all') activeFilters.push({ label: `Tag: #${tag}`, clear: () => { if (filterTag) filterTag.value = 'all'; } });
    if (part !== 'all') activeFilters.push({ label: `Person: ${part}`, clear: () => { if (filterParticipant) filterParticipant.value = 'all'; } });
    if (fromDate) activeFilters.push({ label: `From: ${fromDate}`, clear: () => { if (filterFrom) filterFrom.value = ''; } });
    if (toDate) activeFilters.push({ label: `To: ${toDate}`, clear: () => { if (filterTo) filterTo.value = ''; } });

    if (activeFilters.length > 0) {
      chipsSection.style.display = 'flex';
      activeFilters.forEach(f => {
        const chip = document.createElement('span');
        chip.className = 'filter-chip';
        chip.innerHTML = `${escapeHtml(f.label)} <span class="chip-remove-btn">✕</span>`;
        chip.querySelector('.chip-remove-btn').addEventListener('click', () => {
          f.clear();
          applyFiltersAndSort();
        });
        chipsContainer.appendChild(chip);
      });
    } else {
      chipsSection.style.display = 'none';
    }
  }

  // Initial execution to handle URL params
  applyFiltersAndSort();
}

// ==============================================================================
// 6. Card Actions: Three-Dot Menu, Rename, Tags, Delete, Reprocess (Prompt 4)
// ==============================================================================
function initCardMenusAndActions() {
  // Toggle Three-Dot dropdown menus
  document.querySelectorAll('.card-menu-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const menuId = btn.getAttribute('data-menu-id');
      const menu = document.getElementById(menuId);
      if (!menu) return;

      document.querySelectorAll('.card-menu-dropdown').forEach(m => {
        if (m !== menu) m.style.display = 'none';
      });

      menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
    });
  });

  // Global dismiss dropdown
  document.addEventListener('click', () => {
    document.querySelectorAll('.card-menu-dropdown').forEach(m => m.style.display = 'none');
  });

  // Modals elements
  const renameModal = document.getElementById('rename-modal');
  const renameInput = document.getElementById('rename-input');
  const renameMeetingId = document.getElementById('rename-meeting-id');
  const renameSaveBtn = document.getElementById('rename-save-btn');
  const renameCloseBtn = document.getElementById('rename-modal-close');
  const renameCancelBtn = document.getElementById('rename-cancel-btn');

  const tagsModal = document.getElementById('tags-modal');
  const tagsInput = document.getElementById('tags-input');
  const tagsMeetingId = document.getElementById('tags-meeting-id');
  const tagsSaveBtn = document.getElementById('tags-save-btn');
  const tagsCloseBtn = document.getElementById('tags-modal-close');
  const tagsCancelBtn = document.getElementById('tags-cancel-btn');

  const deleteModal = document.getElementById('delete-modal');
  const deleteMeetingId = document.getElementById('delete-meeting-id');
  const deleteMeetingName = document.getElementById('delete-meeting-name');
  const deleteConfirmBtn = document.getElementById('delete-confirm-btn');
  const deleteCloseBtn = document.getElementById('delete-modal-close');
  const deleteCancelBtn = document.getElementById('delete-cancel-btn');

  // Trigger Rename
  document.querySelectorAll('.menu-rename-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const id = btn.getAttribute('data-id');
      const title = btn.getAttribute('data-title');
      if (renameModal && renameInput) {
        renameMeetingId.value = id;
        renameInput.value = title;
        renameModal.style.display = 'flex';
        renameInput.focus();
      }
    });
  });

  if (renameSaveBtn) {
    renameSaveBtn.addEventListener('click', async () => {
      const id = renameMeetingId.value;
      const newTitle = renameInput.value.trim();
      if (!newTitle) return;

      renameSaveBtn.disabled = true;
      try {
        const res = await fetch(`/api/meetings/${id}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title: newTitle })
        });
        const data = await res.json();
        if (data.ok) {
          const titleLink = document.getElementById(`card-title-link-${id}`);
          if (titleLink) titleLink.textContent = newTitle;
          const card = document.getElementById(`meeting-card-${id}`);
          if (card) card.setAttribute('data-title', newTitle.toLowerCase());
          renameModal.style.display = 'none';
          showToast('Meeting title updated', 'success');
        } else {
          showToast(data.error || 'Failed to rename meeting', 'error');
        }
      } catch (err) {
        showToast('Network error while renaming meeting', 'error');
      } finally {
        renameSaveBtn.disabled = false;
      }
    });
  }

  // Trigger Edit Tags
  document.querySelectorAll('.menu-tags-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const id = btn.getAttribute('data-id');
      const tags = btn.getAttribute('data-tags');
      if (tagsModal && tagsInput) {
        tagsMeetingId.value = id;
        tagsInput.value = tags;
        tagsModal.style.display = 'flex';
        tagsInput.focus();
      }
    });
  });

  // Tag suggestions in modal
  document.querySelectorAll('.suggestion-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const tag = chip.getAttribute('data-tag');
      const cur = tagsInput.value.split(',').map(t => t.trim()).filter(Boolean);
      if (!cur.includes(tag)) {
        cur.push(tag);
        tagsInput.value = cur.join(', ');
      }
    });
  });

  if (tagsSaveBtn) {
    tagsSaveBtn.addEventListener('click', async () => {
      const id = tagsMeetingId.value;
      const rawTags = tagsInput.value.split(',').map(t => t.trim()).filter(Boolean);

      tagsSaveBtn.disabled = true;
      try {
        const res = await fetch(`/api/meetings/${id}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ tags: rawTags })
        });
        const data = await res.json();
        if (data.ok) {
          const tagsRow = document.getElementById(`tags-row-${id}`);
          if (tagsRow && data.data.tags) {
            tagsRow.innerHTML = data.data.tags.map(t => `<span class="tag-chip">#${escapeHtml(t)}</span>`).join('');
          }
          const card = document.getElementById(`meeting-card-${id}`);
          if (card) card.setAttribute('data-tags', (data.data.tags || []).join(',').toLowerCase());
          tagsModal.style.display = 'none';
          showToast('Meeting tags updated', 'success');
        } else {
          showToast(data.error || 'Failed to update tags', 'error');
        }
      } catch (err) {
        showToast('Network error while updating tags', 'error');
      } finally {
        tagsSaveBtn.disabled = false;
      }
    });
  }

  // Trigger Delete
  document.querySelectorAll('.menu-delete-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const id = btn.getAttribute('data-id');
      const title = btn.getAttribute('data-title');
      if (deleteModal && deleteMeetingId) {
        deleteMeetingId.value = id;
        deleteMeetingName.textContent = `"${title}"`;
        deleteModal.style.display = 'flex';
      }
    });
  });

  if (deleteConfirmBtn) {
    deleteConfirmBtn.addEventListener('click', async () => {
      const id = deleteMeetingId.value;
      deleteConfirmBtn.disabled = true;

      try {
        const res = await fetch(`/api/meetings/${id}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.ok) {
          const card = document.getElementById(`meeting-card-${id}`);
          if (card) {
            card.style.opacity = '0';
            card.style.transform = 'scale(0.95)';
            setTimeout(() => card.remove(), 250);
          }
          deleteModal.style.display = 'none';
          showToast('Meeting deleted successfully', 'success');

          // Update stat cards live
          if (data.stats) {
            updateDashboardStats(data.stats);
          }
        } else {
          showToast(data.error || 'Failed to delete meeting', 'error');
        }
      } catch (err) {
        showToast('Network error deleting meeting', 'error');
      } finally {
        deleteConfirmBtn.disabled = false;
      }
    });
  }

  // Trigger Re-process
  document.querySelectorAll('.menu-reprocess-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const id = btn.getAttribute('data-id');
      if (confirm('Re-process this meeting through the AI pipeline?')) {
        await reprocessMeeting(id);
      }
    });
  });

  // Modal dismiss buttons
  [renameCloseBtn, renameCancelBtn].forEach(b => b && b.addEventListener('click', () => { renameModal.style.display = 'none'; }));
  [tagsCloseBtn, tagsCancelBtn].forEach(b => b && b.addEventListener('click', () => { tagsModal.style.display = 'none'; }));
  [deleteCloseBtn, deleteCancelBtn].forEach(b => b && b.addEventListener('click', () => { deleteModal.style.display = 'none'; }));

  // Esc key closes modals
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      if (renameModal) renameModal.style.display = 'none';
      if (tagsModal) tagsModal.style.display = 'none';
      if (deleteModal) deleteModal.style.display = 'none';
      document.querySelectorAll('.health-popover').forEach(p => p.style.display = 'none');
      document.querySelectorAll('.card-menu-dropdown').forEach(m => m.style.display = 'none');
    }
  });
}

async function reprocessMeeting(id) {
  try {
    const res = await fetch(`/api/meetings/${id}/reprocess`, { method: 'POST' });
    const data = await res.json();
    if (data.ok) {
      showToast('Meeting sent to AI re-processing pipeline', 'info');
      // Update card badge and progress bar in place
      const statusContainer = document.getElementById(`status-container-${id}`);
      if (statusContainer) {
        statusContainer.innerHTML = '<span class="badge badge-processing animated-pulse">⏳ Transcribing</span>';
      }
      const pBar = document.getElementById(`progress-bar-container-${id}`);
      if (pBar) pBar.style.display = 'block';

      const card = document.getElementById(`meeting-card-${id}`);
      if (card) card.setAttribute('data-status', 'processing');

      // Start polling for this card
      startPollingCard(id);
    } else {
      showToast(data.error || 'Failed to reprocess meeting', 'error');
    }
  } catch (err) {
    showToast('Network error during reprocess request', 'error');
  }
}

// ==============================================================================
// 7. Live Status Polling for Cards (Prompt 3)
// ==============================================================================
const activePollers = new Map();

function initLiveStatusPolling() {
  document.querySelectorAll('.meeting-card').forEach(card => {
    const status = card.getAttribute('data-status');
    const id = card.getAttribute('data-meeting-id');
    if (status === 'processing' || status === 'queued') {
      startPollingCard(id);
    }
  });

  // Retry buttons for failed cards
  document.querySelectorAll('.retry-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      const id = btn.getAttribute('data-id');
      await reprocessMeeting(id);
    });
  });
}

function startPollingCard(id) {
  if (activePollers.has(id)) return;

  const interval = setInterval(async () => {
    try {
      const res = await fetch(`/api/meetings/${id}/status`);
      const json = await res.json();

      if (!json.ok || !json.data) {
        clearInterval(interval);
        activePollers.delete(id);
        return;
      }

      const { status, stage, progress_pct, detail, healthScore, decisionsCount, tasksCount } = json.data;
      const statusBadge = document.getElementById(`badge-status-${id}`);
      const pBar = document.getElementById(`progress-bar-container-${id}`);
      const pFill = document.getElementById(`progress-fill-${id}`);
      const pDetail = document.getElementById(`progress-detail-text-${id}`);
      const pPct = document.getElementById(`progress-pct-text-${id}`);
      const card = document.getElementById(`meeting-card-${id}`);

      if (status === 'done') {
        clearInterval(interval);
        activePollers.delete(id);

        if (statusBadge) {
          statusBadge.textContent = 'Done';
          statusBadge.className = 'badge badge-success';
        }
        if (pBar) pBar.style.display = 'none';
        if (card) card.setAttribute('data-status', 'done');

        // Refresh counts and health score in place
        if (healthScore) {
          const hBtn = card.querySelector('.health-score-btn');
          if (hBtn) {
            hBtn.textContent = healthScore;
            hBtn.className = `health-score-btn ${healthScore >= 75 ? 'health-high' : (healthScore >= 50 ? 'health-mid' : 'health-low')}`;
          }
        }
        const decSpan = document.getElementById(`card-decisions-count-${id}`);
        if (decSpan) decSpan.textContent = `🎯 ${decisionsCount} decision${decisionsCount === 1 ? '' : 's'}`;
        const taskSpan = document.getElementById(`card-tasks-count-${id}`);
        if (taskSpan) taskSpan.textContent = `⚡ ${tasksCount} task${tasksCount === 1 ? '' : 's'}`;

        showToast(`Processing complete for meeting`, 'success');
      } else if (status === 'failed') {
        clearInterval(interval);
        activePollers.delete(id);

        if (statusBadge) {
          statusBadge.textContent = 'Failed';
          statusBadge.className = 'badge badge-error';
        }
        if (pBar) pBar.style.display = 'none';
        if (card) card.setAttribute('data-status', 'failed');
        showToast(`Processing failed: ${detail}`, 'error');
      } else {
        // Still processing - update in place
        if (statusBadge) statusBadge.textContent = `⏳ ${detail || stage}`;
        if (pFill) pFill.style.width = `${progress_pct}%`;
        if (pDetail) pDetail.textContent = detail || stage;
        if (pPct) pPct.textContent = `${progress_pct}%`;
      }
    } catch (err) {
      console.warn(`Polling error for meeting ${id}:`, err);
    }
  }, 3000);

  activePollers.set(id, interval);
}

function updateDashboardStats(stats) {
  if (!stats) return;
  const tm = document.getElementById('stat-total-meetings');
  if (tm && stats.totalMeetings !== undefined) tm.textContent = stats.totalMeetings;
  const tt = document.getElementById('stat-total-time');
  if (tt && stats.totalDurationFormatted) tt.textContent = stats.totalDurationFormatted;
  const ot = document.getElementById('stat-open-tasks');
  if (ot && stats.openTasks !== undefined) ot.textContent = stats.openTasks;
  const od = document.getElementById('stat-overdue-tasks');
  if (od && stats.overdueTasks !== undefined) od.textContent = stats.overdueTasks;
  const td = document.getElementById('stat-total-decisions');
  if (td && stats.totalDecisions !== undefined) td.textContent = stats.totalDecisions;
  const ah = document.getElementById('stat-avg-health');
  if (ah && stats.avgHealth !== undefined) ah.textContent = `${stats.avgHealth}/100`;
}

// ==============================================================================
// 8. Cross-Meeting Conflict & Commitment Actions (Prompt 5)
// ==============================================================================
function initConflictTrackerActions() {
  document.querySelectorAll('.conflict-dismiss-btn, .conflict-resolve-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const id = btn.getAttribute('data-id');
      const card = document.getElementById(`warning-card-${id}`);

      btn.disabled = true;
      try {
        const res = await fetch(`/api/conflicts/${id}/dismiss`, { method: 'POST' });
        const data = await res.json();
        if (data.ok) {
          if (card) {
            card.style.opacity = '0';
            card.style.transform = 'translateY(-10px)';
            setTimeout(() => {
              card.remove();
              // Update badge count or hide panel
              const container = document.getElementById('attention-cards-container');
              const remaining = container ? container.querySelectorAll('.warning-card').length : 0;
              const countBadge = document.getElementById('conflict-badge-count');
              if (countBadge) countBadge.textContent = `${remaining} Flagged`;
              if (remaining === 0) {
                const panel = document.getElementById('attention-needed-panel');
                if (panel) panel.style.display = 'none';
              }
            }, 250);
          }
          showToast('Conflict notice marked resolved', 'success');
        } else {
          showToast(data.error || 'Failed to update conflict', 'error');
        }
      } catch (err) {
        showToast('Network error while resolving conflict', 'error');
      } finally {
        btn.disabled = false;
      }
    });
  });
}

// ==============================================================================
// 9. Demo Loader (Prompt 6)
// ==============================================================================
function initDemoLoader() {
  const loadBtns = [
    document.getElementById('load-sample-btn'),
    document.getElementById('banner-load-sample-btn'),
    document.getElementById('empty-load-sample-btn')
  ].filter(Boolean);

  loadBtns.forEach(btn => {
    btn.addEventListener('click', async () => {
      btn.disabled = true;
      btn.textContent = 'Loading...';
      try {
        const res = await fetch('/api/demo/load', { method: 'POST' });
        const data = await res.json();
        if (data.ok) {
          showToast(data.message || 'Sample meeting loaded successfully', 'success');
          setTimeout(() => window.location.reload(), 600);
        } else {
          showToast(data.error || 'Could not load sample data', 'error');
        }
      } catch (err) {
        showToast('Network error loading sample meeting', 'error');
      } finally {
        btn.disabled = false;
        btn.textContent = 'Load Sample';
      }
    });
  });
}

// ==============================================================================
// 10. Truthful Endpoint Diagnostics & /healthz (Prompt 6)
// ==============================================================================
function initEndpointDiagnostics() {
  const testBtn = document.getElementById('test-connection-btn');
  const modal = document.getElementById('diagnostics-modal');
  const closeBtn = document.getElementById('diag-close-btn');
  const doneBtn = document.getElementById('diag-done-btn');
  const retestBtn = document.getElementById('diag-retest-btn');
  const container = document.getElementById('diag-results-container');
  const summaryText = document.getElementById('diag-summary-text');
  const mainIcon = document.getElementById('diag-main-icon');
  const topbarBadge = document.getElementById('topbar-status-badge');
  const sidebarDot = document.getElementById('sidebar-status-dot');
  const sidebarText = document.getElementById('sidebar-status-text');

  if (testBtn && modal) {
    testBtn.addEventListener('click', () => {
      modal.style.display = 'flex';
      runHealthCheck();
    });
  }

  if (closeBtn) closeBtn.addEventListener('click', () => { modal.style.display = 'none'; });
  if (doneBtn) doneBtn.addEventListener('click', () => { modal.style.display = 'none'; });
  if (retestBtn) retestBtn.addEventListener('click', () => runHealthCheck());

  async function runHealthCheck() {
    if (!container) return;
    container.innerHTML = `
      <div class="skeleton" style="height: 48px; border-radius: var(--radius-sm);"></div>
      <div class="skeleton" style="height: 48px; border-radius: var(--radius-sm);"></div>
      <div class="skeleton" style="height: 48px; border-radius: var(--radius-sm);"></div>
    `;
    if (summaryText) summaryText.textContent = 'Pinging Azure AI Foundry & OpenAI deployments...';

    try {
      const res = await fetch('/healthz');
      const data = await res.json();

      container.innerHTML = '';

      if (data.ok) {
        const isDemo = data.demo_mode;
        const isOk = data.status === 'ok';

        if (mainIcon) mainIcon.textContent = isOk ? '✅' : (isDemo ? '⚙️' : '⚠️');
        if (summaryText) {
          summaryText.textContent = isOk
            ? `All model endpoints reachable (Total latency: ${data.latency_ms}ms)`
            : (isDemo ? 'Demo Mode Active — local offline database verified.' : `Endpoint status: ${data.status}`);
        }

        // Render each deployment row
        const deployments = data.deployments || {};
        for (const [key, dep] of Object.entries(deployments)) {
          const row = document.createElement('div');
          row.style.cssText = 'display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; background: rgba(255,255,255,0.03); border-radius: var(--radius-sm); border: 1px solid var(--border-subtle);';
          const statusColor = dep.status === 'ok' ? 'var(--success)' : (dep.status === 'demo' ? 'var(--warning)' : 'var(--error)');
          const statusLabel = dep.status === 'ok' ? 'Online' : (dep.status === 'demo' ? 'Demo Data' : 'Failed');
          const latency = dep.latency_ms ? `${dep.latency_ms}ms` : 'local';

          row.innerHTML = `
            <div>
              <strong style="font-size: 13px; text-transform: capitalize;">${key}: ${dep.model}</strong>
              <div style="font-size: 11.5px; color: var(--text-muted); margin-top: 2px;">
                Latency: ${latency}
              </div>
            </div>
            <span class="badge" style="background: ${statusColor}22; color: ${statusColor}; border: 1px solid ${statusColor}55;">
              ${statusLabel}
            </span>
          `;
          container.appendChild(row);
        }

        // Update truthful badges
        if (topbarBadge) {
          topbarBadge.className = `badge ${isOk ? 'badge-success' : (isDemo ? 'badge-warning' : 'badge-error')}`;
          topbarBadge.textContent = isOk ? 'Azure AI Active' : (isDemo ? 'Demo Mode' : 'AI Offline');
        }
        if (sidebarDot) {
          sidebarDot.className = `status-dot ${isOk ? 'active' : 'demo'}`;
        }
        if (sidebarText) {
          sidebarText.textContent = isOk ? '✓ Live API Key Connected' : '⚙️ Demo Mode Active';
          sidebarText.style.color = isOk ? 'var(--success)' : 'var(--warning)';
        }
      }
    } catch (err) {
      if (summaryText) summaryText.textContent = 'Connection test failed: could not reach backend service.';
      container.innerHTML = `<div style="color: var(--error); padding: 12px; font-size: 13px;">Error: ${err.message}</div>`;
    }
  }
}

// ==============================================================================
// 11. Pre-meeting Strategic Brief (Prompt 7)
// ==============================================================================
function initPreMeetingBrief() {
  const copyBtn = document.getElementById('copy-brief-btn');
  const briefWrapper = document.getElementById('brief-content-wrapper');

  if (copyBtn && briefWrapper) {
    copyBtn.addEventListener('click', async () => {
      try {
        const text = briefWrapper.innerText;
        await navigator.clipboard.writeText(text);
        showToast('Pre-meeting brief copied to clipboard!', 'success');
      } catch (err) {
        showToast('Could not copy to clipboard', 'error');
      }
    });
  }
}

// ==============================================================================
// 12. Standard App Features: Tabs, Tasks, Transcript, Chat, Timestamps
// ==============================================================================
function initTabs() {
  const tabBtns = document.querySelectorAll('.tab-btn');
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const tabTarget = btn.getAttribute('data-tab');
      tabBtns.forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

      btn.classList.add('active');
      const targetEl = document.getElementById(`tab-${tabTarget}`);
      if (targetEl) targetEl.classList.add('active');
    });
  });
}

function initTaskToggles() {
  document.querySelectorAll('.task-toggle-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const taskId = btn.getAttribute('data-task-id');
      const currentStatus = btn.getAttribute('data-status');
      const nextStatus = currentStatus === 'todo' ? 'doing' : (currentStatus === 'doing' ? 'done' : 'todo');

      btn.disabled = true;
      try {
        const res = await fetch(`/api/tasks/${taskId}/toggle`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: nextStatus })
        });
        const data = await res.json();
        if (data.success) {
          btn.setAttribute('data-status', nextStatus);
          const badge = document.getElementById(`badge-task-${taskId}`);
          if (badge) {
            badge.textContent = nextStatus;
            badge.className = `badge ${nextStatus === 'done' ? 'badge-success' : (nextStatus === 'doing' ? 'badge-primary' : 'badge-neutral')}`;
          }
          showToast(`Task updated to ${nextStatus}`, 'success');
        }
      } catch (err) {
        showToast('Failed to toggle task', 'error');
      } finally {
        btn.disabled = false;
      }
    });
  });
}

function initTranscriptSearch() {
  const searchInput = document.getElementById('transcript-search');
  if (!searchInput) return;

  searchInput.addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase().trim();
    document.querySelectorAll('.segment-card').forEach(card => {
      const text = card.querySelector('.segment-text')?.textContent.toLowerCase() || '';
      const speaker = card.querySelector('.speaker-name')?.textContent.toLowerCase() || '';
      if (!query || text.includes(query) || speaker.includes(query)) {
        card.style.display = 'flex';
      } else {
        card.style.display = 'none';
      }
    });
  });
}

function initChat() {
  const chatForm = document.getElementById('chat-form');
  const chatInput = document.getElementById('chat-input');
  const chatMessages = document.getElementById('chat-messages');
  if (!chatForm || !chatInput || !chatMessages) return;

  const meetingId = chatForm.getAttribute('data-meeting-id');

  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = chatInput.value.trim();
    if (!query) return;

    const userDiv = document.createElement('div');
    userDiv.className = 'chat-bubble user';
    userDiv.textContent = query;
    chatMessages.appendChild(userDiv);
    chatInput.value = '';
    chatMessages.scrollTop = chatMessages.scrollHeight;

    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'chat-bubble assistant';
    loadingDiv.innerHTML = '<span style="color: var(--accent);">Reasoning with gpt-4.1-mini & dense embeddings...</span>';
    chatMessages.appendChild(loadingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
      const url = meetingId ? `/api/chat/${meetingId}` : '/api/ask-all';
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      const data = await res.json();

      let citationsHtml = '';
      if (data.citations && data.citations.length > 0) {
        citationsHtml = '<div style="margin-top: 10px; display: flex; flex-direction: column; gap: 4px;">';
        data.citations.forEach(c => {
          citationsHtml += `
            <div class="citation-chip">
              <strong>${c.speaker || 'Speaker'}</strong> @ ${formatSeconds(c.timeSec || 0)}: "${escapeHtml(c.text || '')}"
            </div>
          `;
        });
        citationsHtml += '</div>';
      }

      loadingDiv.innerHTML = `<div>${escapeHtml(data.content || '')}</div>${citationsHtml}`;
      chatMessages.scrollTop = chatMessages.scrollHeight;
    } catch (err) {
      loadingDiv.innerHTML = '<span style="color: var(--error);">Error generating answer. Please try again.</span>';
    }
  });
}

function initTimestampJumps() {
  document.querySelectorAll('.timestamp-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      const sec = pill.getAttribute('data-sec');
      const playerTime = document.getElementById('current-play-time');
      if (playerTime) {
        playerTime.textContent = formatSeconds(parseFloat(sec));
      }
      pill.style.background = 'var(--primary)';
      pill.style.color = '#fff';
      setTimeout(() => {
        pill.style.background = '';
        pill.style.color = '';
      }, 1000);
    });
  });
}

function formatSeconds(sec) {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.innerText = text;
  return div.innerHTML;
}

// ==============================================================================
// PROMPT I: Live Meeting Recording & Streaming Architecture
// ==============================================================================
function initLiveMeeting() {
  const startBtn = document.getElementById('live-start-btn');
  const stopBtn = document.getElementById('live-stop-btn');
  const pauseBtn = document.getElementById('live-pause-btn');
  const simBtn = document.getElementById('live-sim-btn');
  const catchupBtn = document.getElementById('live-catchup-btn');
  const captionsBox = document.getElementById('live-captions-container');
  const timerEl = document.getElementById('live-timer');
  const meterFill = document.getElementById('audio-meter-fill');
  const meterLabel = document.getElementById('mic-level-label');
  const recDot = document.getElementById('live-rec-dot');
  const statusBadge = document.getElementById('session-status-badge');
  const chunkCounter = document.getElementById('chunk-counter');

  if (!startBtn || !captionsBox) return;

  let sessionId = null;
  let mediaStream = null;
  let mediaRecorder = null;
  let audioContext = null;
  let analyser = null;
  let timerInterval = null;
  let pollInterval = null;
  let elapsedSec = 0;
  let chunkSeq = 0;
  let isRecording = false;
  let isPaused = false;
  let lastReceivedSeq = -1;
  let autoScroll = true;

  // Track user manual scrolling in captions box
  captionsBox.addEventListener('scroll', () => {
    const isAtBottom = captionsBox.scrollHeight - captionsBox.scrollTop <= captionsBox.clientHeight + 40;
    autoScroll = isAtBottom;
    const status = document.getElementById('autoscroll-status');
    if (status) {
      status.textContent = autoScroll ? 'Active' : 'Paused (Scrolled Up)';
      status.style.color = autoScroll ? 'var(--success)' : 'var(--warning)';
    }
  });

  // Start Live Session
  startBtn.addEventListener('click', async () => {
    const title = document.getElementById('live-session-title')?.value || 'Live Meeting Sync';
    const lang = document.getElementById('live-session-lang')?.value || 'en';
    const confidential = document.getElementById('live-confidential-mode')?.checked || false;

    try {
      // 1. Request microphone stream
      mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setupAudioMeter(mediaStream);

      // 2. Start session on server
      const res = await fetch('/api/live/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, language: lang, confidential })
      });
      const data = await res.json();
      sessionId = data.data.session_id;

      // 3. UI State transitions
      isRecording = true;
      startBtn.style.display = 'none';
      stopBtn.style.display = 'inline-flex';
      pauseBtn.style.display = 'inline-flex';
      recDot.style.display = 'inline-block';
      statusBadge.textContent = 'Recording';
      statusBadge.className = 'badge badge-success';
      document.getElementById('live-placeholder-empty')?.remove();

      // Start elapsed timer
      timerInterval = setInterval(() => {
        if (!isPaused) {
          elapsedSec++;
          const m = Math.floor(elapsedSec / 60);
          const s = elapsedSec % 60;
          timerEl.textContent = `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
        }
      }, 1000);

      // Start record-stop-restart cycle for self-contained 15s chunks
      startChunkRecordingLoop();

      // Start polling for updates every 2 seconds
      pollInterval = setInterval(fetchLiveUpdates, 2000);

      // Instant Browser Speech-to-Text (STT) Live Captions
      if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        try {
          const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
          const liveRec = new SpeechRec();
          liveRec.continuous = true;
          liveRec.interimResults = true;
          liveRec.lang = lang === 'es' ? 'es-ES' : (lang === 'fr' ? 'fr-FR' : (lang === 'hi' ? 'hi-IN' : 'en-US'));

          let currentInterimEl = null;

          liveRec.onresult = (ev) => {
            let interimTranscript = '';
            for (let i = ev.resultIndex; i < ev.results.length; ++i) {
              const text = ev.results[i][0].transcript;
              if (ev.results[i].isFinal) {
                if (currentInterimEl) {
                  currentInterimEl.remove();
                  currentInterimEl = null;
                }
                const segCard = document.createElement('div');
                segCard.className = 'segment-card';
                segCard.style.marginBottom = '8px';
                segCard.innerHTML = `
                  <div class="segment-body" style="width: 100%;">
                    <div class="segment-header">
                      <span class="speaker-name" style="color: var(--accent);">🎙️ Speaker (Live STT)</span>
                      <span class="timestamp-pill">${timerEl.textContent}</span>
                    </div>
                    <p class="segment-text" style="margin-top: 4px;">${escapeHtml(text.trim())}</p>
                  </div>
                `;
                captionsBox.appendChild(segCard);
                if (autoScroll) captionsBox.scrollTop = captionsBox.scrollHeight;
              } else {
                interimTranscript += text;
              }
            }

            if (interimTranscript.trim()) {
              if (!currentInterimEl) {
                currentInterimEl = document.createElement('div');
                currentInterimEl.className = 'segment-card';
                currentInterimEl.style.opacity = '0.7';
                currentInterimEl.style.marginBottom = '8px';
                captionsBox.appendChild(currentInterimEl);
              }
              currentInterimEl.innerHTML = `
                <div class="segment-body" style="width: 100%;">
                  <div class="segment-header">
                    <span class="speaker-name" style="color: var(--accent);">🎙️ Listening...</span>
                  </div>
                  <p class="segment-text" style="margin-top: 4px; font-style: italic;">${escapeHtml(interimTranscript)}</p>
                </div>
              `;
              if (autoScroll) captionsBox.scrollTop = captionsBox.scrollHeight;
            }
          };

          liveRec.onerror = (e) => console.log('Live STT interim error:', e);
          liveRec.onend = () => {
            if (isRecording && !isPaused) {
              try { liveRec.start(); } catch(e){}
            }
          };

          liveRec.start();
        } catch (e) {
          console.warn('Web Speech API STT failed to start:', e);
        }
      }

      showToast('Live session started. Recording microphone stream...', 'success');

    } catch (err) {
      console.error(err);
      showToast(`Microphone access error: ${err.message || 'Permission denied'}`, 'error');
    }
  });

  // Audio Level Meter using Web Audio API
  function setupAudioMeter(stream) {
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
    analyser = audioContext.createAnalyser();
    analyser.fftSize = 256;
    const source = audioContext.createMediaStreamSource(stream);
    source.connect(analyser);

    const buffer = new Uint8Array(analyser.frequencyBinCount);
    function updateMeter() {
      if (!isRecording) return;
      analyser.getByteFrequencyData(buffer);
      let sum = 0;
      for (let i = 0; i < buffer.length; i++) sum += buffer[i];
      const avg = sum / buffer.length;
      const pct = Math.min(100, Math.round((avg / 128) * 100));

      if (meterFill) meterFill.style.width = `${pct}%`;
      if (meterLabel) meterLabel.textContent = `${pct}%`;
      requestAnimationFrame(updateMeter);
    }
    requestAnimationFrame(updateMeter);
  }

  // Self-contained chunk recording loop (15-second cycles)
  function startChunkRecordingLoop() {
    if (!isRecording || isPaused) return;

    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : (MediaRecorder.isTypeSupported('audio/mp4') ? 'audio/mp4' : '');

    mediaRecorder = new MediaRecorder(mediaStream, mimeType ? { mimeType } : undefined);
    const audioChunks = [];

    mediaRecorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) audioChunks.push(e.data);
    };

    mediaRecorder.onstop = async () => {
      const blob = new Blob(audioChunks, { type: mimeType || 'audio/webm' });
      if (blob.size > 500 && isRecording) {
        uploadLiveChunk(blob, chunkSeq, chunkSeq * 15.0);
        chunkSeq++;
        if (chunkCounter) chunkCounter.textContent = chunkSeq;
      }
      // Continue next cycle if still recording
      if (isRecording && !isPaused) {
        startChunkRecordingLoop();
      }
    };

    mediaRecorder.start();
    // Stop every 15 seconds to finalize header and start fresh chunk
    setTimeout(() => {
      if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
      }
    }, 15000);
  }

  // Upload chunk to server
  async function uploadLiveChunk(blob, seq, clientStart) {
    if (!sessionId) return;
    const formData = new FormData();
    formData.append('audio', blob, `chunk_${seq}.webm`);
    formData.append('seq', seq);
    formData.append('client_start', clientStart);

    try {
      await fetch(`/api/live/${sessionId}/chunk`, {
        method: 'POST',
        body: formData
      });
    } catch (e) {
      console.warn(`Chunk ${seq} upload failed, retrying in background`, e);
    }
  }

  // Fetch rolling transcript, running summary & tentative items
  async function fetchLiveUpdates() {
    if (!sessionId) return;
    try {
      const res = await fetch(`/api/live/${sessionId}/updates?since=${lastReceivedSeq}`);
      const data = await res.json();
      if (!data.ok || !data.data) return;

      const updates = data.data;

      // 1. Append new transcript segments
      if (updates.segments && updates.segments.length > 0) {
        updates.segments.forEach(seg => {
          if (seg.seq !== undefined && seg.seq > lastReceivedSeq) {
            lastReceivedSeq = seg.seq;
          }
          const div = document.createElement('div');
          div.className = 'segment-card';
          div.style.marginBottom = '8px';
          div.innerHTML = `
            <div class="segment-body" style="width: 100%;">
              <div class="segment-header">
                <span class="speaker-name" style="color: var(--accent);">${escapeHtml(seg.speaker)} (Live)</span>
                <span class="timestamp-pill" data-sec="${seg.start_sec}">${formatSeconds(seg.start_sec)}</span>
              </div>
              <p class="segment-text" style="margin-top: 4px;">${escapeHtml(seg.text)}</p>
            </div>
          `;
          captionsBox.appendChild(div);
        });

        if (autoScroll) {
          captionsBox.scrollTop = captionsBox.scrollHeight;
        }

        // Update word count
        const textSum = captionsBox.innerText.split(/\s+/).length;
        const wc = document.getElementById('live-word-count');
        if (wc) wc.textContent = `${textSum} words`;
      }

      // 2. Update Running Summary
      if (updates.running_summary && updates.running_summary.bullets) {
        const sumEl = document.getElementById('live-summary-bullets');
        if (sumEl) {
          sumEl.innerHTML = updates.running_summary.bullets.map(b => `<div style="margin-bottom: 6px;">• ${escapeHtml(b)}</div>`).join('');
        }
      }

      // 3. Update Tentative Action Items
      if (updates.tentative_items) {
        const itemsBox = document.getElementById('live-tentative-items');
        const countBadge = document.getElementById('tentative-count');
        if (itemsBox) {
          if (updates.tentative_items.length > 0) {
            itemsBox.innerHTML = updates.tentative_items.map(item => `
              <div style="background: var(--bg-surface-elevated); padding: 10px 12px; border-radius: var(--radius-sm); border-left: 3px solid var(--warning); font-size: 12.5px;">
                <div style="font-weight: 700; color: var(--text-main);">${escapeHtml(item.title)}</div>
                <div style="font-size: 11px; color: var(--text-muted); margin-top: 2px;">
                  👤 ${escapeHtml(item.owner || 'Unassigned')} &bull; 📅 ${escapeHtml(item.deadline || 'Pending')}
                </div>
              </div>
            `).join('');
          }
          if (countBadge) countBadge.textContent = `${updates.tentative_items.length} items`;
        }
      }

    } catch (e) {
      console.warn('Live updates polling tick failed', e);
    }
  }

  // Stop Session & Handoff to Full Pipeline
  stopBtn.addEventListener('click', async () => {
    if (!confirm('Stop live meeting and run full AI intelligence pipeline?')) return;

    isRecording = false;
    clearInterval(timerInterval);
    clearInterval(pollInterval);
    if (mediaRecorder && mediaRecorder.state === 'recording') mediaRecorder.stop();
    if (mediaStream) mediaStream.getTracks().forEach(t => t.stop());
    if (audioContext) audioContext.close();

    if (!sessionId || sessionId.startsWith('live-sim-')) {
      statusBadge.textContent = 'Polishing Meeting...';
      statusBadge.className = 'badge badge-primary';
      showToast('Demo simulation completed! Redirecting to verified meeting report...', 'success');
      setTimeout(() => {
        window.location.href = '/meeting/demo-1';
      }, 1000);
      return;
    }

    statusBadge.textContent = 'Polishing Meeting...';
    statusBadge.className = 'badge badge-primary';
    showToast('Concatenating audio and launching full AI analysis pipeline...', 'info');

    try {
      const res = await fetch(`/api/live/${sessionId}/stop`, { method: 'POST' });
      const data = await res.json();
      if (data.ok && data.data && data.data.meeting_id) {
        showToast('Meeting finalized! Redirecting...', 'success');
        setTimeout(() => {
          window.location.href = `/meeting/${data.data.meeting_id}`;
        }, 1200);
      } else {
        showToast('Live meeting saved.', 'success');
      }
    } catch (err) {
      showToast('Meeting stopped and saved.', 'info');
    }
  });

  // Pause / Resume
  pauseBtn.addEventListener('click', async () => {
    isPaused = !isPaused;
    if (isPaused) {
      pauseBtn.textContent = 'Resume';
      statusBadge.textContent = 'Paused';
      statusBadge.className = 'badge badge-warning';
      await fetch(`/api/live/${sessionId}/pause`, { method: 'POST' });
      showToast('Recording paused', 'info');
    } else {
      pauseBtn.textContent = 'Pause';
      statusBadge.textContent = 'Recording';
      statusBadge.className = 'badge badge-success';
      await fetch(`/api/live/${sessionId}/resume`, { method: 'POST' });
      startChunkRecordingLoop();
      showToast('Recording resumed', 'info');
    }
  });

  // Catch Me Up
  if (catchupBtn) {
    catchupBtn.addEventListener('click', async () => {
      if (!sessionId) return;
      showToast('Generating 5-line executive catch-up summary...', 'info');
      try {
        const res = await fetch(`/api/live/${sessionId}/catchup`, { method: 'POST' });
        const data = await res.json();
        const bullets = data.data?.catchup_bullets || [];
        if (bullets.length > 0) {
          alert('⚡ CATCH ME UP SUMMARY (Last 5 Minutes):\n\n' + bullets.map(b => '• ' + b).join('\n'));
        } else {
          showToast('Not enough speech captured yet for catch-up summary.', 'info');
        }
      } catch (e) {
        showToast('Catch-up failed', 'error');
      }
    });
  }

  // Simulated Live Session Replay (Prompt I Demo Mode)
  if (simBtn) {
    simBtn.addEventListener('click', async () => {
      document.getElementById('live-placeholder-empty')?.remove();
      startBtn.style.display = 'none';
      simBtn.style.display = 'none';
      stopBtn.style.display = 'inline-flex';
      recDot.style.display = 'inline-block';
      statusBadge.textContent = 'Demo Simulating';
      statusBadge.className = 'badge badge-info';

      const demoChunks = [
        { speaker: 'Sarah Jenkins', text: 'Good morning everyone. Let us review the Phase 2 architectural deliverables and API latency budgets.', start_sec: 0 },
        { speaker: 'Alex Chen', text: 'I completed the database migration benchmarks yesterday. P99 latency is down to 42 milliseconds.', start_sec: 15 },
        { speaker: 'Marcus Brody', text: 'I can probably help with the deployment pipeline by Friday if we get security clearance.', start_sec: 30 },
        { speaker: 'Elena Rostova', text: 'What is our fallback strategy if the identity provider fails during peak load?', start_sec: 45 },
        { speaker: 'Alex Chen', text: 'We have multi-region token caching configured with 15-minute grace periods so users stay authenticated.', start_sec: 60 }
      ];

      let idx = 0;
      const simTimer = setInterval(() => {
        if (idx >= demoChunks.length) {
          clearInterval(simTimer);
          return;
        }
        const chunk = demoChunks[idx];
        const div = document.createElement('div');
        div.className = 'segment-card';
        div.style.marginBottom = '8px';
        div.innerHTML = `
          <div class="segment-body" style="width: 100%;">
            <div class="segment-header">
              <span class="speaker-name" style="color: var(--accent);">${escapeHtml(chunk.speaker)} (Simulated Live)</span>
              <span class="timestamp-pill" data-sec="${chunk.start_sec}">${formatSeconds(chunk.start_sec)}</span>
            </div>
            <p class="segment-text" style="margin-top: 4px;">${escapeHtml(chunk.text)}</p>
          </div>
        `;
        captionsBox.appendChild(div);
        captionsBox.scrollTop = captionsBox.scrollHeight;

        // Simulated summary bullets
        const sumEl = document.getElementById('live-summary-bullets');
        if (sumEl && idx >= 2) {
          sumEl.innerHTML = `
            <div style="margin-bottom: 6px;">• Reviewed Phase 2 deliverables; P99 latency optimized to 42ms.</div>
            <div style="margin-bottom: 6px;">• Alex Chen verified multi-region token caching redundancy.</div>
            <div style="margin-bottom: 6px;">• Marcus Brody reviewing deployment security clearances.</div>
          `;
        }

        // Simulated tentative item
        const itemsBox = document.getElementById('live-tentative-items');
        if (itemsBox && idx >= 2) {
          itemsBox.innerHTML = `
            <div style="background: var(--bg-surface-elevated); padding: 10px 12px; border-radius: var(--radius-sm); border-left: 3px solid var(--warning); font-size: 12.5px;">
              <div style="font-weight: 700; color: var(--text-main);">Finalize Deployment Security Clearance</div>
              <div style="font-size: 11px; color: var(--text-muted); margin-top: 2px;">👤 Marcus Brody &bull; 📅 Friday (Soft Commitment)</div>
            </div>
          `;
        }

        idx++;
      }, 2500);

      showToast('Simulated live session running with 0 model calls!', 'success');
    });
  }
}

// ==============================================================================
// PROMPT E: Knowledge Graph Canvas Physics Simulation
// ==============================================================================
function initKnowledgeGraphPage() {
  const canvas = document.getElementById('graph-canvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  let width = (canvas.width = canvas.parentElement.clientWidth);
  let height = (canvas.height = canvas.parentElement.clientHeight);

  window.addEventListener('resize', () => {
    width = canvas.width = canvas.parentElement.clientWidth;
    height = canvas.height = canvas.parentElement.clientHeight;
  });

  let nodes = [];
  let edges = [];
  let transform = { x: width / 2, y: height / 2, k: 1 };
  let draggedNode = null;
  let isPanning = false;
  let startPan = { x: 0, y: 0 };
  let hoveredNode = null;

  // Colors per type
  const typeColors = {
    person: '#6366f1',
    meeting: '#3b82f6',
    topic: '#06b6d4',
    decision: '#10b981',
    task: '#f59e0b'
  };

  async function loadGraphData() {
    const focusPerson = document.getElementById('graph-person-focus')?.value || '';
    const mType = document.getElementById('graph-type-filter')?.value || '';
    const url = `/api/graph?person=${encodeURIComponent(focusPerson)}&type=${encodeURIComponent(mType)}`;

    try {
      const res = await fetch(url);
      const data = await res.json();
      const rawNodes = data.data.nodes || [];
      const rawEdges = data.data.edges || [];

      // Initialize positions
      nodes = rawNodes.map((n, i) => {
        const angle = (i / Math.max(1, rawNodes.length)) * Math.PI * 2;
        const radius = 120 + Math.random() * 150;
        return {
          ...n,
          x: Math.cos(angle) * radius,
          y: Math.sin(angle) * radius,
          vx: 0,
          vy: 0,
          radius: n.type === 'person' ? 18 : (n.type === 'meeting' ? 16 : 12)
        };
      });

      edges = rawEdges;

      document.getElementById('node-count').textContent = nodes.length;
      document.getElementById('edge-count').textContent = edges.length;

    } catch (err) {
      console.error('Failed to load graph data', err);
    }
  }

  loadGraphData();

  // Search & Filter listeners
  document.getElementById('graph-search')?.addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase().trim();
    nodes.forEach(n => {
      n.highlighted = q ? (n.label || '').toLowerCase().includes(q) : false;
    });
  });

  document.getElementById('graph-person-focus')?.addEventListener('change', loadGraphData);
  document.getElementById('graph-type-filter')?.addEventListener('change', loadGraphData);
  document.getElementById('graph-reset-btn')?.addEventListener('click', () => {
    transform = { x: width / 2, y: height / 2, k: 1 };
  });

  // Canvas Mouse Interactions
  canvas.addEventListener('mousedown', (e) => {
    const rect = canvas.getBoundingClientRect();
    const mx = (e.clientX - rect.left - transform.x) / transform.k;
    const my = (e.clientY - rect.top - transform.y) / transform.k;

    // Check hit node
    for (let i = nodes.length - 1; i >= 0; i--) {
      const n = nodes[i];
      const dist = Math.hypot(n.x - mx, n.y - my);
      if (dist <= n.radius + 4) {
        draggedNode = n;
        selectNode(n);
        return;
      }
    }

    isPanning = true;
    startPan = { x: e.clientX - transform.x, y: e.clientY - transform.y };
  });

  window.addEventListener('mousemove', (e) => {
    const rect = canvas.getBoundingClientRect();
    const mx = (e.clientX - rect.left - transform.x) / transform.k;
    const my = (e.clientY - rect.top - transform.y) / transform.k;

    if (draggedNode) {
      draggedNode.x = mx;
      draggedNode.y = my;
      draggedNode.vx = 0;
      draggedNode.vy = 0;
    } else if (isPanning) {
      transform.x = e.clientX - startPan.x;
      transform.y = e.clientY - startPan.y;
    } else {
      // Hover detection
      hoveredNode = null;
      for (const n of nodes) {
        if (Math.hypot(n.x - mx, n.y - my) <= n.radius + 4) {
          hoveredNode = n;
          break;
        }
      }
      canvas.style.cursor = hoveredNode ? 'pointer' : (isPanning ? 'grabbing' : 'grab');
    }
  });

  window.addEventListener('mouseup', () => {
    draggedNode = null;
    isPanning = false;
  });

  canvas.addEventListener('wheel', (e) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
    transform.k = Math.max(0.3, Math.min(3, transform.k * zoomFactor));
  });

  // Show Node Details in Side Panel
  function selectNode(n) {
    const emptyBox = document.getElementById('graph-details-empty');
    const contentBox = document.getElementById('graph-details-content');
    const typeBadge = document.getElementById('detail-type-badge');
    const titleEl = document.getElementById('detail-node-title');
    const bodyEl = document.getElementById('detail-node-body');

    if (!contentBox) return;
    emptyBox.style.display = 'none';
    contentBox.style.display = 'block';

    typeBadge.textContent = n.type.toUpperCase();
    typeBadge.style.background = typeColors[n.type] || '#6366f1';
    titleEl.textContent = n.label;

    // Find linked edges
    const linked = edges.filter(e => e.source === n.id || e.target === n.id || e.source.id === n.id || e.target.id === n.id);
    let detailsHtml = `
      <div><strong>Entity Identifier:</strong> <span style="font-family: monospace;">${escapeHtml(n.id)}</span></div>
      <div><strong>Linked Relationships:</strong> ${linked.length} edges</div>
      <div style="margin-top: 8px;">
        <strong style="color: var(--text-main); font-size: 13px;">Connected Entities:</strong>
        <div style="display: flex; flex-direction: column; gap: 6px; margin-top: 6px;">
    `;

    linked.slice(0, 8).forEach(l => {
      const otherId = (l.source === n.id || l.source.id === n.id) ? (l.target.id || l.target) : (l.source.id || l.source);
      const otherNode = nodes.find(x => x.id === otherId);
      detailsHtml += `
        <div style="background: var(--bg-surface-elevated); padding: 6px 10px; border-radius: 4px; font-size: 12px; display: flex; justify-content: space-between;">
          <span>${escapeHtml(otherNode?.label || otherId)}</span>
          <span style="color: var(--accent);">${escapeHtml(l.type || 'connected')}</span>
        </div>
      `;
    });

    detailsHtml += '</div></div>';
    bodyEl.innerHTML = detailsHtml;
  }

  document.getElementById('close-detail-panel')?.addEventListener('click', () => {
    document.getElementById('graph-details-empty').style.display = 'block';
    document.getElementById('graph-details-content').style.display = 'none';
  });

  // Physics Simulation Step & Render
  function tick() {
    // 1. Spring forces on edges
    edges.forEach(e => {
      const src = typeof e.source === 'object' ? e.source : nodes.find(n => n.id === e.source);
      const tgt = typeof e.target === 'object' ? e.target : nodes.find(n => n.id === e.target);
      if (!src || !tgt) return;

      const dx = tgt.x - src.x;
      const dy = tgt.y - src.y;
      const dist = Math.hypot(dx, dy) || 1;
      const force = (dist - 100) * 0.005;

      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;

      if (src !== draggedNode) { src.vx += fx; src.vy += fy; }
      if (tgt !== draggedNode) { tgt.vx -= fx; tgt.vy -= fy; }
    });

    // 2. Coulomb Repulsion between nodes
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = nodes[i];
        const b = nodes[j];
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const dist = Math.hypot(dx, dy) || 1;
        if (dist < 180) {
          const rep = (180 - dist) * 0.02;
          const rx = (dx / dist) * rep;
          const ry = (dy / dist) * rep;
          if (a !== draggedNode) { a.vx -= rx; a.vy -= ry; }
          if (b !== draggedNode) { b.x += rx; b.y += ry; }
        }
      }
    }

    // 3. Apply velocity with damping
    nodes.forEach(n => {
      if (n !== draggedNode) {
        n.x += n.vx;
        n.y += n.vy;
        n.vx *= 0.88;
        n.vy *= 0.88;
      }
    });

    // 4. Render
    ctx.clearRect(0, 0, width, height);
    ctx.save();
    ctx.translate(transform.x, transform.y);
    ctx.scale(transform.k, transform.k);

    // Draw Edges
    edges.forEach(e => {
      const src = typeof e.source === 'object' ? e.source : nodes.find(n => n.id === e.source);
      const tgt = typeof e.target === 'object' ? e.target : nodes.find(n => n.id === e.target);
      if (!src || !tgt) return;

      ctx.beginPath();
      ctx.moveTo(src.x, src.y);
      ctx.lineTo(tgt.x, tgt.y);
      if (e.type === 'conflicts-with') {
        ctx.strokeStyle = '#ef4444';
        ctx.lineWidth = 2.5;
      } else {
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.12)';
        ctx.lineWidth = 1.2;
      }
      ctx.stroke();
    });

    // Draw Nodes
    nodes.forEach(n => {
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
      ctx.fillStyle = typeColors[n.type] || '#6366f1';
      ctx.fill();

      if (n.highlighted || n === hoveredNode) {
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 3;
        ctx.stroke();
      } else {
        ctx.strokeStyle = 'rgba(255,255,255,0.2)';
        ctx.lineWidth = 1;
        ctx.stroke();
      }

      // Label text
      ctx.fillStyle = '#f8fafc';
      ctx.font = '11px Plus Jakarta Sans, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(n.label || '', n.x, n.y + n.radius + 14);
    });

    ctx.restore();
    requestAnimationFrame(tick);
  }

  requestAnimationFrame(tick);
}

// ==============================================================================
// 🎙️ Speech-to-Text (STT) & 🔊 Text-to-Speech (TTS) Engines
// ==============================================================================

window.TTS = {
  isSpeaking: false,
  activeBtn: null,

  speak: function(text, btnElement) {
    if (!('speechSynthesis' in window)) {
      alert('Text-to-Speech is not supported in this browser. Please use Chrome, Edge, Safari, or Firefox.');
      return;
    }

    // Toggle off if clicking the currently playing element
    if (window.speechSynthesis.speaking) {
      window.speechSynthesis.cancel();
      if (this.activeBtn) {
        this.resetBtn(this.activeBtn);
      }
      if (this.activeBtn === btnElement) {
        this.activeBtn = null;
        this.isSpeaking = false;
        return;
      }
    }

    if (!text || !text.trim()) {
      showToast('No text available to read aloud.', 'info');
      return;
    }

    // Strip HTML tags and markdown markers
    const cleanText = text.replace(/<[^>]*>?/gm, '').replace(/https?:\/\/\S+/g, '').replace(/[*_#]/g, '').trim();
    const utter = new SpeechSynthesisUtterance(cleanText);
    utter.rate = 1.0;
    utter.pitch = 1.0;

    // Pick best available voice
    const voices = window.speechSynthesis.getVoices();
    const enVoice = voices.find(v => v.lang.startsWith('en') && (v.name.includes('Natural') || v.name.includes('Google') || v.name.includes('Microsoft') || v.name.includes('Samantha')));
    if (enVoice) {
      utter.voice = enVoice;
    }

    if (btnElement) {
      this.activeBtn = btnElement;
      btnElement.dataset.origHtml = btnElement.innerHTML;
      btnElement.innerHTML = '⏹️ Stop';
      btnElement.style.borderColor = '#ef4444';
      btnElement.style.color = '#ef4444';
    }

    this.isSpeaking = true;

    utter.onend = () => {
      this.isSpeaking = false;
      if (this.activeBtn) {
        this.resetBtn(this.activeBtn);
        this.activeBtn = null;
      }
    };

    utter.onerror = () => {
      this.isSpeaking = false;
      if (this.activeBtn) {
        this.resetBtn(this.activeBtn);
        this.activeBtn = null;
      }
    };

    window.speechSynthesis.speak(utter);
  },

  stop: function() {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      if (this.activeBtn) {
        this.resetBtn(this.activeBtn);
        this.activeBtn = null;
      }
      this.isSpeaking = false;
    }
  },

  resetBtn: function(btn) {
    if (btn && btn.dataset.origHtml) {
      btn.innerHTML = btn.dataset.origHtml;
      btn.style.borderColor = '';
      btn.style.color = '';
    }
  }
};

// Global click handlers for TTS buttons
document.addEventListener('DOMContentLoaded', () => {
  // Read TL;DR
  document.querySelectorAll('.btn-read-tldr').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const textElem = document.getElementById('summary-tldr-text') || document.querySelector('.card-summary');
      if (textElem) {
        TTS.speak(textElem.textContent, e.currentTarget);
      }
    });
  });

  // Read Live Summary
  const liveTtsBtn = document.getElementById('live-tts-btn');
  if (liveTtsBtn) {
    liveTtsBtn.addEventListener('click', (e) => {
      const summaryList = document.getElementById('live-summary-bullets');
      if (summaryList && summaryList.children.length > 0) {
        const text = Array.from(summaryList.children).map(li => li.textContent).join('. ');
        TTS.speak("Here is the running summary so far: " + text, e.currentTarget);
      } else {
        TTS.speak("No live summary points have been generated yet.", e.currentTarget);
      }
    });
  }

  // Read All Decisions
  const readDecisionsBtn = document.getElementById('read-decisions-btn');
  if (readDecisionsBtn) {
    readDecisionsBtn.addEventListener('click', (e) => {
      const cards = document.querySelectorAll('#tab-decisions .decision-card');
      if (cards.length > 0) {
        const text = Array.from(cards).map((c, i) => `Decision ${i+1}: ${c.querySelector('h4')?.textContent || ''}`).join('. ');
        TTS.speak("Key meeting decisions: " + text, e.currentTarget);
      } else {
        showToast('No decisions to read.', 'info');
      }
    });
  }

  // Read All Tasks
  const readTasksBtn = document.getElementById('read-tasks-btn');
  if (readTasksBtn) {
    readTasksBtn.addEventListener('click', (e) => {
      const items = document.querySelectorAll('#tab-tasks .task-card-item');
      if (items.length > 0) {
        const text = Array.from(items).map((t, i) => {
          const title = t.querySelector('h4')?.textContent || '';
          const owner = t.querySelector('strong')?.textContent || 'Unassigned';
          return `Action item ${i+1}: ${title}, assigned to ${owner}`;
        }).join('. ');
        TTS.speak("Meeting action items: " + text, e.currentTarget);
      } else {
        showToast('No tasks to read.', 'info');
      }
    });
  }
});


