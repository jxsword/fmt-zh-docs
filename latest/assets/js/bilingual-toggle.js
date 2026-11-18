// Bilingual toggle functionality for fmt Chinese documentation

(function() {
  'use strict';

  const STORAGE_KEY = 'fmt-zh-bilingual';
  const OVERLAY_ID = 'bilingual-overlay';
  const TOGGLE_ID = 'bilingual-toggle';

  // Get original text from data attributes
  function getOriginalText(element) {
    return element.dataset.original || element.textContent;
  }

  // Store original text in data attributes
  function storeOriginalTexts() {
    const translatableElements = document.querySelectorAll(
      '.md-content p, .md-content li, .md-content td, .md-content th, .md-content h1, .md-content h2, .md-content h3, .md-content h4, .md-content h5, .md-content h6'
    );
    
    translatableElements.forEach(el => {
      if (!el.dataset.original && el.textContent.trim()) {
        el.dataset.original = el.textContent;
      }
    });
  }

  // Toggle bilingual mode
  function toggleBilingual() {
    const isActive = document.body.classList.toggle('bilingual-mode');
    localStorage.setItem(STORAGE_KEY, isActive);
    
    if (isActive) {
      showBilingualOverlay();
    } else {
      hideBilingualOverlay();
    }
    
    updateToggleButton(isActive);
  }

  // Show bilingual comparison overlay
  function showBilingualOverlay() {
    let overlay = document.getElementById(OVERLAY_ID);
    
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = OVERLAY_ID;
      overlay.className = 'bilingual-overlay';
      document.body.appendChild(overlay);
    }
    
    const content = document.querySelector('.md-content');
    if (!content) return;
    
    // Clone content for overlay
    const clone = content.cloneNode(true);
    
    // Add original text as data attributes if not present
    const translatableElements = clone.querySelectorAll(
      'p, li, td, th, h1, h2, h3, h4, h5, h6'
    );
    
    translatableElements.forEach(el => {
      if (el.dataset.original) return;
      // Try to find corresponding element in original content
      const originalEl = content.querySelector(el.tagName.toLowerCase() + ':nth-of-type(' + 
        Array.from(el.parentNode.children).indexOf(el) + 1 + ')');
      if (originalEl && originalEl.dataset.original) {
        el.dataset.original = originalEl.dataset.original;
      }
    });
    
    // Build bilingual comparison
    let html = '<div class="content"><h1>中英对照</h1>';
    
    const sections = clone.querySelectorAll('h1, h2, h3, h2, h3, h4, h5, h6, p, ul, ol, table');
    let currentSection = null;
    
    sections.forEach(el => {
      if (el.tagName.match(/^H[1-6]$/)) {
        if (currentSection) {
          html += '</div>';
        }
        currentSection = el.textContent;
        html += `<h2>${el.textContent}</h2><div class="bilingual-content">`;
      } else if (el.tagName === 'P' || el.tagName === 'LI') {
        const original = el.dataset.original || '';
        const translated = el.textContent;
        if (original && original !== translated) {
          html += `<div class="bilingual-row">
            <div class="original">${escapeHtml(original)}</div>
            <div class="translated">${escapeHtml(translated)}</div>
          </div>`;
        }
      }
    });
    
    if (currentSection) {
      html += '</div>';
    }
    
    html += '<button class="close-overlay" onclick="closeBilingualOverlay()">关闭</button></div>';
    overlay.innerHTML = html;
    overlay.classList.add('active');
  }

  function hideBilingualOverlay() {
    const overlay = document.getElementById(OVERLAY_ID);
    if (overlay) {
      overlay.classList.remove('active');
    }
  }

  function closeBilingualOverlay() {
    document.body.classList.remove('bilingual-mode');
    localStorage.setItem(STORAGE_KEY, 'false');
    hideBilingualOverlay();
    updateToggleButton(false);
  }

  function updateToggleButton(isActive) {
    const btn = document.getElementById(TOGGLE_ID);
    if (!btn) return;
    
    if (isActive) {
      btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>';
      btn.title = '关闭双语对照';
    } else {
      btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>';
      btn.title = '开启双语对照';
    }
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // Initialize
  function init() {
    // Restore bilingual mode from storage
    const isActive = localStorage.getItem(STORAGE_KEY) === 'true';
    if (isActive) {
      document.body.classList.add('bilingual-mode');
      showBilingualOverlay();
    }
    
    // Store original texts
    storeOriginalTexts();
    
    // Create toggle button
    const btn = document.createElement('button');
    btn.id = TOGGLE_ID;
    btn.className = 'bilingual-toggle';
    btn.setAttribute('aria-label', '切换双语对照');
    btn.onclick = toggleBilingual;
    document.body.appendChild(btn);
    
    updateToggleButton(document.body.classList.contains('bilingual-mode'));
  }

  // Expose functions globally
  window.toggleBilingual = toggleBilingual;
  window.closeBilingualOverlay = closeBilingualOverlay;

  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();