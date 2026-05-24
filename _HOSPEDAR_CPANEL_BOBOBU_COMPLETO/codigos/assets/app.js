document.querySelectorAll('[data-copy]').forEach((button) => {
  button.addEventListener('click', async () => {
    const value = button.getAttribute('data-copy') || '';
    const csrf = document.querySelector('.shell')?.getAttribute('data-csrf') || '';
    const notifyCopy = async () => {
      if (!button.hasAttribute('data-log-copy') || !csrf) return;
      const body = new URLSearchParams();
      body.set('csrf', csrf);
      body.set('action', 'copy_code');
      body.set('code', value);
      body.set('subject', button.getAttribute('data-subject') || '');
      try {
        await fetch(window.location.href, {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8' },
          body,
        });
      } catch (_) {}
    };
    try {
      await navigator.clipboard.writeText(value);
      await notifyCopy();
      if (button.tagName === 'BUTTON') {
        const old = button.textContent;
        button.textContent = 'Copiado';
        setTimeout(() => { button.textContent = old; }, 1100);
      } else {
        button.classList.add('copied');
        setTimeout(() => { button.classList.remove('copied'); }, 1100);
      }
    } catch (_) {
      window.prompt('Copie o codigo:', value);
      await notifyCopy();
    }
  });
});

function tickCountdowns() {
  const now = Math.floor(Date.now() / 1000);
  document.querySelectorAll('[data-expires-at]').forEach((card) => {
    const expiresAt = Number(card.getAttribute('data-expires-at') || '0');
    const remaining = expiresAt - now;
    if (!expiresAt || remaining <= 0) {
      card.remove();
      return;
    }
    const minutes = String(Math.floor(remaining / 60)).padStart(2, '0');
    const seconds = String(remaining % 60).padStart(2, '0');
    const target = card.querySelector('[data-countdown]');
    if (target) target.textContent = `${minutes}:${seconds}`;
  });
}

tickCountdowns();
setInterval(tickCountdowns, 1000);
