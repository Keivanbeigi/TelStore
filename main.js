document.addEventListener('DOMContentLoaded', () => {
  // Progressive enhancement: Add copy button to pre blocks
  const codeBlocks = document.querySelectorAll('pre');
  codeBlocks.forEach((pre) => {
    const code = pre.querySelector('code');
    if (!code) return;

    const copyBtn = document.createElement('button');
    copyBtn.type = 'button';
    copyBtn.className = 'copy-btn';
    copyBtn.textContent = 'Copy';
    copyBtn.setAttribute('aria-label', 'Copy code to clipboard');

    copyBtn.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(code.innerText.trim());
        copyBtn.textContent = 'Copied!';
        copyBtn.classList.add('copied');
        setTimeout(() => {
          copyBtn.textContent = 'Copy';
          copyBtn.classList.remove('copied');
        }, 2000);
      } catch (err) {
        copyBtn.textContent = 'Failed';
        setTimeout(() => {
          copyBtn.textContent = 'Copy';
        }, 2000);
      }
    });

    pre.appendChild(copyBtn);
  });

  // Progressive enhancement: Highlight active docs sidebar item
  const docsSections = document.querySelectorAll('.docs-section[id]');
  const docsLinks = document.querySelectorAll('.docs-nav a[href^="#"]');

  if (docsSections.length > 0 && docsLinks.length > 0 && 'IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const id = entry.target.getAttribute('id');
          docsLinks.forEach((link) => {
            if (link.getAttribute('href') === `#${id}`) {
              link.classList.add('active');
            } else {
              link.classList.remove('active');
            }
          });
        }
      });
    }, { rootMargin: '-20% 0px -70% 0px' });

    docsSections.forEach((section) => observer.observe(section));
  }
});
