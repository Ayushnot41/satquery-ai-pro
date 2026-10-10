/* Compatibility bridge: every original cockpit function remains in the source. */
(() => {
  const params = new URLSearchParams(location.search);
  const embedded = params.get('embed') === '1';
  if (embedded) document.body.classList.add('pro-embedded');
  const notice = document.createElement('aside');
  notice.className = 'pro-console-notice';
  notice.innerHTML = '<span><strong>SIMULATION CONSOLE</strong> · Orbital tracks, detections, radar, intelligence and benchmarks are illustrative. Map imagery may come from external providers.</span><a href="/#home" target="_top">Return to Pro workspace ↗</a>';
  document.body.prepend(notice);
  const account = () => { window.top.location.href = '/#settings'; };
  // Identity is managed by the verified Pro account screen, never by local demo grants.
  for (const name of ['openAuthModal','executeGoogleLogin','submitEmailAuth','sendPhoneOtp','verifyPhoneOtp']) {
    if (typeof window[name] === 'function') window[name] = account;
  }
  if (typeof saveUserSession === 'function') window.saveUserSession = async () => {
    const response = await fetch('/api/auth/me');
    if (!response.ok) return account();
    currentAuthSession = await response.json();
    updateAuthUI();
  };
  localStorage.removeItem('bhuvision_auth_session');
  window.executeLogout = async () => {
    const response = await fetch('/api/auth/logout', {method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});
    if (response.ok) {currentAuthSession=null;window.top.location.href='/';}
  };
  fetch('/api/auth/me').then(r => r.ok ? r.json() : null).then(data => {
    if (data && typeof updateAuthUI === 'function') {currentAuthSession = data; updateAuthUI();}
  }).catch(() => {});
  window.addEventListener('DOMContentLoaded', () => {
    const requested = params.get('screen');
    if (requested && ['home','mission','workspace','sar','disaster','debate','evaluation','futuristic','defense','comparison'].includes(requested)) switchTab(requested);
  });
})();
