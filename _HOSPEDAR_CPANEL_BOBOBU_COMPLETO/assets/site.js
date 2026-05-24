const form = document.querySelector('#leadForm');
const message = document.querySelector('#formMessage');

function showMessage(text, error = false) {
  message.hidden = false;
  message.textContent = text;
  message.classList.toggle('error', error);
}

if (form) {
  const whatsapp = form.querySelector('[name="whatsapp"]');
  if (whatsapp) {
    whatsapp.addEventListener('input', () => {
      whatsapp.value = whatsapp.value.replace(/[^\d+()\-\s]/g, '').slice(0, 32);
    });
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const button = form.querySelector('button');
    button.disabled = true;
    button.textContent = 'Enviando...';

    try {
      const data = Object.fromEntries(new FormData(form).entries());
      if (!data.whatsapp && !data.telegram && !data.discord) {
        throw new Error('Preencha pelo menos WhatsApp, Telegram ou Discord.');
      }
      data.action = 'submit_lead';
      const response = await fetch('api/leads.php', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      const result = await response.json();
      if (!result.ok) {
        throw new Error(result.error || 'Nao consegui enviar agora.');
      }
      form.reset();
      showMessage(result.message || 'Recebido. Em breve entrarei em contato.');
    } catch (error) {
      showMessage(error.message || 'Erro ao enviar.', true);
    } finally {
      button.disabled = false;
      button.textContent = 'Enviar';
    }
  });
}
