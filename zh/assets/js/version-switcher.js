// Version switcher for fmt Chinese documentation

(function() {
  'use strict';

  const STORAGE_KEY = 'fmt-zh-version';

  function init() {
    // Restore last selected version
    const savedVersion = localStorage.getItem(STORAGE_KEY);
    const versionSelect = document.querySelector('.md-version select, [data-md-version]');
    
    if (versionSelect && savedVersion) {
      // Check if the saved version is in the options
      const options = Array.from(versionSelect.options).map(opt => opt.value);
      if (options.includes(savedVersion)) {
        versionSelect.value = savedVersion;
        // If current URL doesn't match, redirect
        const currentVersion = getCurrentVersion();
        if (currentVersion !== savedVersion) {
          window.location.href = '/' + savedVersion + window.location.pathname.replace(/^\/[^/]+/, '');
        }
      }
    }
    
    // Listen for version changes
    if (versionSelect) {
      versionSelect.addEventListener('change', function() {
        const version = this.value;
        localStorage.setItem(STORAGE_KEY, version);
        
        // Redirect to the selected version
        const currentPath = window.location.pathname;
        const newPath = currentPath.replace(/^\/[^/]+/, '/' + version);
        window.location.href = newPath;
      });
    }
    
    // Add version badge to header
    addVersionBadge();
  }

  function getCurrentVersion() {
    const path = window.location.pathname;
    const match = path.match(/^\/([^/]+)/);
    return match ? match[1] : 'latest';
  }

  function addVersionBadge() {
    const header = document.querySelector('.md-header__topic, .md-header__title');
    if (!header) return;
    
    const version = getCurrentVersion();
    if (version === 'latest') return;
    
    const badge = document.createElement('span');
    badge.className = 'version-badge';
    badge.textContent = 'v' + version;
    badge.style.cssText = `
      display: inline-block;
      margin-left: 0.5rem;
      padding: 0.15rem 0.5rem;
      background: var(--md-primary-fg-color);
      color: var(--md-primary-bg-color);
      border-radius: 4px;
      font-size: 0.75em;
      font-weight: 600;
      vertical-align: middle;
    `;
    
    header.appendChild(badge);
  }

  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();