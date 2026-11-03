/**
 * EL CUENTO DE FIRULÉ • APP.JS
 * Lógica interactiva para la web familiar:
 * - Reproductor de video interactivo con Canvas Confetti
 * - Slider comparador Before/After táctil y responsive (clip-path)
 * - Telemetría y analítica interna hacia Raspberry Pi 5 (Tailscale Funnel HTTPS)
 */

document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const video = document.getElementById('playerVideo');
  const videoOverlay = document.getElementById('videoOverlay');
  const btnBigPlay = document.getElementById('btnBigPlay');
  const btnDispararFestejo = document.getElementById('btnDispararFestejo');
  const videoStatusText = document.getElementById('videoStatusText');

  const btnScrollToVideo = document.getElementById('btnScrollToVideo');
  const btnScrollToCompare = document.getElementById('btnScrollToCompare');
  const btnSongLink = document.getElementById('btnSongLink');

  // Slider Before/After elements
  const baSlider = document.getElementById('baSlider');

  // =========================================================================
  // 1. TELEMETRY & ANALYTICS CLIENT (Same-Origin via Netlify Serverless Function)
  // Bypasses all browser Private Network Access warnings completely.
  // =========================================================================
  const TRACKER_URL = '/api/track';
  
  // Persistent anonymous session (cryptographically strong)
  let sessionId = localStorage.getItem('firule_session_id');
  if (!sessionId) {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
      sessionId = 'session_' + crypto.randomUUID();
    } else {
      sessionId = 'session_' + Math.random().toString(36).substring(2, 10) + '_' + Date.now();
    }
    localStorage.setItem('firule_session_id', sessionId);
  }

  function sendTelemetry(eventType, extraData = {}) {
    const payload = {
      session_id: sessionId,
      event: eventType,
      screen: `${window.screen.width}x${window.screen.height} (viewport: ${window.innerWidth}x${window.innerHeight})`,
      referrer: document.referrer || 'directo',
      data: {
        timestamp: new Date().toISOString(),
        url: window.location.href,
        userAgent: navigator.userAgent,
        language: navigator.language,
        orientation: window.screen.orientation ? window.screen.orientation.type : 'unknown',
        ...extraData
      }
    };

    const jsonStr = JSON.stringify(payload);

    // Try sendBeacon first (doesn't block unloading), fallback to fetch keepalive
    if (navigator.sendBeacon) {
      try {
        const blob = new Blob([jsonStr], { type: 'application/json' });
        navigator.sendBeacon(TRACKER_URL, blob);
        return;
      } catch (e) {}
    }

    try {
      fetch(TRACKER_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: jsonStr,
        keepalive: true
      }).catch(() => {});
    } catch (e) {}
  }

  // Initial page view event
  sendTelemetry('page_view', { loadTime: performance.now() });

  // Heartbeat ping every 20 seconds only when tab is visible to avoid background flooding
  let timeOnPageSeconds = 0;
  setInterval(() => {
    if (!document.hidden) {
      timeOnPageSeconds += 20;
      sendTelemetry('heartbeat', { secondsOnPage: timeOnPageSeconds });
    }
  }, 20000);

  // =========================================================================
  // 2. SMOOTH SCROLLING
  // =========================================================================
  if (btnScrollToVideo) {
    btnScrollToVideo.addEventListener('click', () => {
      document.getElementById('seccion-video').scrollIntoView({ behavior: 'smooth' });
      sendTelemetry('click_scroll_video');
    });
  }

  if (btnScrollToCompare) {
    btnScrollToCompare.addEventListener('click', () => {
      document.getElementById('seccion-comparador').scrollIntoView({ behavior: 'smooth' });
      sendTelemetry('click_scroll_compare');
    });
  }

  if (btnSongLink) {
    btnSongLink.addEventListener('click', () => {
      sendTelemetry('click_song_canticuenticos');
    });
  }

  // =========================================================================
  // 3. VIDEO PLAYBACK, RETENTION FUNNEL & CELEBRATION
  // =========================================================================
  let progressReported = { '25': false, '50': false, '75': false, '100': false };

  function playVideo() {
    video.play();
    videoOverlay.classList.add('hidden');
    if (videoStatusText) {
      videoStatusText.textContent = '🔊 Reproduciendo cuento de Firulé...';
    }
  }

  if (btnBigPlay) {
    btnBigPlay.addEventListener('click', playVideo);
  }

  if (videoOverlay) {
    videoOverlay.addEventListener('click', playVideo);
  }

  video.addEventListener('play', () => {
    videoOverlay.classList.add('hidden');
    if (videoStatusText) {
      videoStatusText.textContent = '🔊 Escuchando la voz de Isaí y María...';
    }
    sendTelemetry('video_play', { currentTime: video.currentTime });
  });

  video.addEventListener('pause', () => {
    if (videoStatusText) {
      videoStatusText.textContent = '⏸️ Video en pausa';
    }
    sendTelemetry('video_pause', { currentTime: video.currentTime });
  });

  // Track video viewing milestones (25%, 50%, 75%)
  video.addEventListener('timeupdate', () => {
    if (!video.duration) return;
    const pct = (video.currentTime / video.duration) * 100;

    if (pct >= 25 && !progressReported['25']) {
      progressReported['25'] = true;
      sendTelemetry('video_progress_25', { time: video.currentTime });
    }
    if (pct >= 50 && !progressReported['50']) {
      progressReported['50'] = true;
      sendTelemetry('video_progress_50', { time: video.currentTime });
    }
    if (pct >= 75 && !progressReported['75']) {
      progressReported['75'] = true;
      sendTelemetry('video_progress_75', { time: video.currentTime });
    }
  });

  // When video ends -> 100% RETENTION & CELEBRATION!
  video.addEventListener('ended', () => {
    if (videoOverlay) {
      videoOverlay.classList.remove('hidden');
    }
    if (videoStatusText) {
      videoStatusText.innerHTML = '🌟 <strong>¡BRAVO ISAÍ! ¡Hermoso cuento!</strong> 👏🐶❤️';
    }
    if (!progressReported['100']) {
      progressReported['100'] = true;
      sendTelemetry('video_ended', { duration: video.duration });
    }
    dispararFestejoCompleto();
  });

  // Button to trigger celebration manually
  if (btnDispararFestejo) {
    btnDispararFestejo.addEventListener('click', () => {
      sendTelemetry('confetti_click');
      dispararFestejoCompleto();
    });
  }

  // =========================================================================
  // 4. CANVAS CONFETTI EXPLOSION
  // =========================================================================
  function dispararFestejoCompleto() {
    if (typeof confetti !== 'function') return;

    const count = 180;
    const defaults = {
      origin: { y: 0.7 },
      zIndex: 9999
    };

    function fire(particleRatio, opts) {
      confetti(Object.assign({}, defaults, opts, {
        particleCount: Math.floor(count * particleRatio)
      }));
    }

    fire(0.25, {
      spread: 26,
      startVelocity: 55,
      colors: ['#e74c3c', '#f1c40f', '#3498db']
    });
    fire(0.2, {
      spread: 60,
      colors: ['#2ecc71', '#e67e22', '#9b59b6']
    });
    fire(0.35, {
      spread: 100,
      decay: 0.91,
      scalar: 1.2,
      colors: ['#fd79a8', '#fed330', '#55efc4']
    });
    fire(0.1, {
      spread: 120,
      startVelocity: 25,
      decay: 0.92,
      scalar: 1.4
    });
    fire(0.1, {
      spread: 120,
      startVelocity: 45
    });

    // Second wave 450ms later
    setTimeout(() => {
      confetti({
        particleCount: 70,
        angle: 60,
        spread: 55,
        origin: { x: 0 },
        zIndex: 9999
      });
      confetti({
        particleCount: 70,
        angle: 120,
        spread: 55,
        origin: { x: 1 },
        zIndex: 9999
      });
    }, 450);
  }

  // =========================================================================
  // 5. BEFORE / AFTER COMPARATIVE SLIDER (CLIP-PATH BASED)
  // =========================================================================
  if (baSlider) {
    let isDragging = false;
    let hasLoggedInteraction = false;

    function updateSlider(clientX) {
      const rect = baSlider.getBoundingClientRect();
      let offsetX = clientX - rect.left;
      
      // Clamp between 0 and rect.width
      if (offsetX < 0) offsetX = 0;
      if (offsetX > rect.width) offsetX = rect.width;

      const percentage = ((offsetX / rect.width) * 100).toFixed(2);
      baSlider.style.setProperty('--ba-pos', `${percentage}%`);
      baSlider.setAttribute('aria-valuenow', Math.round(percentage));

      if (!hasLoggedInteraction) {
        hasLoggedInteraction = true;
        sendTelemetry('slider_moved', { initialPos: percentage });
      }
    }

    // Keyboard navigation (Accessibility)
    baSlider.addEventListener('keydown', (e) => {
      let currentVal = parseFloat(baSlider.getAttribute('aria-valuenow') || '50');
      let step = 5;
      if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') {
        currentVal = Math.max(0, currentVal - step);
        baSlider.style.setProperty('--ba-pos', `${currentVal}%`);
        baSlider.setAttribute('aria-valuenow', currentVal);
        e.preventDefault();
      } else if (e.key === 'ArrowRight' || e.key === 'ArrowUp') {
        currentVal = Math.min(100, currentVal + step);
        baSlider.style.setProperty('--ba-pos', `${currentVal}%`);
        baSlider.setAttribute('aria-valuenow', currentVal);
        e.preventDefault();
      } else if (e.key === 'Home') {
        baSlider.style.setProperty('--ba-pos', '0%');
        baSlider.setAttribute('aria-valuenow', 0);
        e.preventDefault();
      } else if (e.key === 'End') {
        baSlider.style.setProperty('--ba-pos', '100%');
        baSlider.setAttribute('aria-valuenow', 100);
        e.preventDefault();
      }
    });

    // Mouse Events
    baSlider.addEventListener('mousedown', (e) => {
      isDragging = true;
      updateSlider(e.clientX);
    });

    window.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      updateSlider(e.clientX);
    });

    window.addEventListener('mouseup', () => {
      isDragging = false;
    });

    // Touch Events (Mobile)
    baSlider.addEventListener('touchstart', (e) => {
      isDragging = true;
      if (e.touches.length > 0) {
        updateSlider(e.touches[0].clientX);
      }
    }, { passive: true });

    window.addEventListener('touchmove', (e) => {
      if (!isDragging) return;
      if (e.touches.length > 0) {
        updateSlider(e.touches[0].clientX);
      }
    }, { passive: true });

    window.addEventListener('touchend', () => {
      isDragging = false;
    });

    // Initial position (50%)
    baSlider.style.setProperty('--ba-pos', '50%');
  }

  // =========================================================================
  // 6. MAGNETIC LETTERS SOUND / INTERACTION
  // =========================================================================
  const magnets = document.querySelectorAll('.magnet');
  magnets.forEach(m => {
    m.addEventListener('click', () => {
      m.style.transform = 'scale(1.25) rotate(' + (Math.random() * 20 - 10) + 'deg)';
      sendTelemetry('magnet_clicked', { letter: m.textContent.trim() });
      setTimeout(() => {
        m.style.transform = '';
      }, 350);
    });
  });
});
