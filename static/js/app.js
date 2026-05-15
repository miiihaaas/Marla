// sticky header bg
const header = document.getElementById('header');
const onScroll = () => {
  if (window.scrollY > 24) header.classList.add('scrolled');
  else header.classList.remove('scrolled');
};
window.addEventListener('scroll', onScroll, { passive: true });
onScroll();

// active nav link via IntersectionObserver
const sections = ['home', 'usluge', 'o-nama', 'kontakt'].map(id => document.getElementById(id));
const links = document.querySelectorAll('.nav-links a');
const linkFor = id => document.querySelector('.nav-links a[href="#' + id + '"]');
const setActive = id => {
  links.forEach(a => a.classList.remove('active'));
  const l = linkFor(id);
  if (l) l.classList.add('active');
};
const io = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) setActive(e.target.id);
  });
}, { rootMargin: '-45% 0px -50% 0px', threshold: 0 });
sections.forEach(s => s && io.observe(s));

// contact form submit
const form = document.getElementById('contactForm');
const submitBtn = document.getElementById('submitBtn');
const statusEl = document.getElementById('formStatus');

const setStatus = (msg, kind) => {
  statusEl.textContent = msg || '';
  statusEl.classList.remove('error', 'success');
  if (kind) statusEl.classList.add(kind);
};

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  setStatus('', null);

  const data = Object.fromEntries(new FormData(form).entries());

  const originalHtml = submitBtn.innerHTML;
  submitBtn.disabled = true;
  submitBtn.innerHTML = 'Šalje se…';

  try {
    const res = await fetch('/api/contact', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    let payload = {};
    try { payload = await res.json(); } catch (_) {}

    if (res.ok && payload.ok) {
      submitBtn.innerHTML = 'Hvala — javljamo se ✓';
      submitBtn.style.background = '#7eb8e8';
      submitBtn.style.color = '#0c1a2d';
      form.reset();
      setTimeout(() => {
        submitBtn.innerHTML = originalHtml;
        submitBtn.style.background = '';
        submitBtn.style.color = '';
        submitBtn.disabled = false;
      }, 2400);
    } else {
      submitBtn.innerHTML = originalHtml;
      submitBtn.disabled = false;
      setStatus(payload.error || 'Došlo je do greške, pokušajte ponovo.', 'error');
    }
  } catch (err) {
    submitBtn.innerHTML = originalHtml;
    submitBtn.disabled = false;
    setStatus('Došlo je do greške, pokušajte ponovo.', 'error');
  }
});
