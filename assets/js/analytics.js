// Analytics tracking for fmt Chinese documentation

(function() {
  'use strict';

  // Configuration
  const GA_MEASUREMENT_ID = 'G-XXXXXXXXXX'; // Replace with actual GA4 Measurement ID
  const PLAUSIBLE_DOMAIN = 'fmt-zh.example.com'; // Replace with actual domain

  // Initialize Google Analytics 4
  function initGA() {
    if (typeof gtag === 'function') return;
    
    window.dataLayer = window.dataLayer || [];
    function gtag() { dataLayer.push(arguments); }
    window.gtag = gtag;
    gtag('js', new Date());
    gtag('config', GA_MEASUREMENT_ID, {
      page_path: window.location.pathname,
      send_page_view: true
    });
    
    // Load GA script
    const script = document.createElement('script');
    script.async = true;
    script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}`;
    document.head.appendChild(script);
  }

  // Initialize Plausible Analytics (privacy-friendly alternative)
  function initPlausible() {
    if (window.plausible) return;
    
    const script = document.createElement('script');
    script.defer = true;
    script.dataset.domain = PLAUSIBLE_DOMAIN;
    script.src = 'https://plausible.io/js/script.js';
    document.head.appendChild(script);
  }

  // Track custom events
  function trackEvent(eventName, parameters = {}) {
    if (typeof gtag === 'function') {
      gtag('event', eventName, parameters);
    }
    
    if (window.plausible) {
      window.plausible(eventName, { props: parameters });
    }
  }

  // Track page views for SPA navigation
  function trackPageView(path) {
    trackEvent('page_view', { page_path: path });
  }

  // Track version switches
  function trackVersionSwitch(fromVersion, toVersion) {
    trackEvent('version_switch', { from_version: fromVersion, to_version: toVersion });
  }

  // Track bilingual mode toggle
  function trackBilingualToggle(enabled) {
    trackEvent('bilingual_toggle', { enabled: enabled });
  }

  // Track search queries
  function trackSearch(query, resultsCount) {
    trackEvent('search', { query: query, results_count: resultsCount });
  }

  // Track external link clicks
  function trackExternalLink(url) {
    trackEvent('external_link_click', { url: url });
  }

  // Track PDF downloads
  function trackPDFDownload(version) {
    trackEvent('pdf_download', { version: version });
  }

  // Initialize on DOM ready
  function init() {
    // Initialize analytics (choose one)
    // initGA(); // Uncomment to use Google Analytics
    // initPlausible(); // Uncomment to use Plausible
    
    // Track initial page view
    trackPageView(window.location.pathname);
    
    // Track version switcher
    const versionSelect = document.querySelector('.md-version select, [data-md-version]');
    if (versionSelect) {
      versionSelect.addEventListener('change', function(e) {
        trackVersionSwitch(window.location.pathname.split('/')[1] || 'latest', e.target.value);
      });
    }
    
    // Track bilingual toggle
    const bilingualToggle = document.getElementById('bilingual-toggle');
    if (bilingualToggle) {
      bilingualToggle.addEventListener('click', function() {
        const enabled = document.body.classList.contains('bilingual-mode');
        trackBilingualToggle(!enabled);
      });
    }
    
    // Track search
    const searchInput = document.querySelector('.md-search__input');
    if (searchInput) {
      let debounceTimer;
      searchInput.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
          if (this.value.trim().length >= 2) {
            trackSearch(this.value.trim(), 0); // Results count would need integration with search plugin
          }
        }, 300);
      });
    }
    
    // Track external links
    document.addEventListener('click', function(e) {
      const link = e.target.closest('a[href^="http"]');
      if (link && !link.href.includes(window.location.hostname)) {
        trackExternalLink(link.href);
      }
    });
    
    // Track PDF download buttons
    document.addEventListener('click', function(e) {
      const link = e.target.closest('a[href$=".pdf"]');
      if (link) {
        const version = window.location.pathname.split('/')[1] || 'latest';
        trackPDFDownload(version);
      }
    });
  }

  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Expose tracking functions globally for manual use
  window.fmtZHTrack = {
    event: trackEvent,
    pageView: trackPageView,
    versionSwitch: trackVersionSwitch,
    bilingualToggle: trackBilingualToggle,
    search: trackSearch,
    externalLink: trackExternalLink,
    pdfDownload: trackPDFDownload
  };
})();