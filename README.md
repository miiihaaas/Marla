# PR Marla Beograd

Statički landing sajt + minimalan Flask backend za prijem kontakt forme i prosleđivanje na email.

## Struktura

```
.
├── app.py                # Flask backend (/, /api/contact)
├── passenger_wsgi.py     # Entry point za cPanel Python App (a2 hosting)
├── requirements.txt
├── .env.example          # Template za env varijable
├── .env                  # Lokalne env varijable (NE commit-ovati)
├── index.html            # Glavni landing
└── static/
    ├── css/styles.css
    ├── js/app.js
    ├── assets/           # business-team.jpg (hero pozadina)
    └── uploads/          # rezervisano za buduće slike (portrete tima)
```

## Lokalno pokretanje (Windows / PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# uredi .env i unesi prave SMTP kredencijale
python app.py
```

Sajt je dostupan na `http://localhost:5000`.

### Lokalno pokretanje (Linux / macOS)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

## Email konfiguracija

Backend čita SMTP podešavanja iz environment varijabli:

| Varijabla    | Opis                                                  |
|--------------|-------------------------------------------------------|
| `SMTP_HOST`  | SMTP server (npr. `smtp.gmail.com`, `mail.a2hosting`) |
| `SMTP_PORT`  | Port (`465` za SSL)                                   |
| `SMTP_USER`  | SMTP korisničko ime                                   |
| `SMTP_PASS`  | SMTP lozinka (Gmail: app password)                    |
| `MAIL_FROM`  | "From" adresa                                          |
| `MAIL_TO`    | Primalac forme                                        |
| `FLASK_ENV`  | `production` ili `development`                        |

Lokalno se čitaju iz `.env`. U produkciji se postavljaju kroz cPanel UI.

### Promena primaoca

Da bi se izmenila adresa na koju stižu poruke iz forme:

- **Lokalno:** uredi `MAIL_TO` u `.env` i restartuj `python app.py`
- **Produkcija:** u cPanel-u → Setup Python App → Environment variables → izmeni `MAIL_TO` → restartuj aplikaciju

## Deployment na a2 hosting (cPanel)

1. **cPanel → Setup Python App → Create Application**
   - Python version: 3.10+ (najnoviji dostupan)
   - Application root: npr. `prmarla_app` (folder unutar home-a)
   - Application URL: domen ili poddomen
   - Application startup file: `passenger_wsgi.py`
   - Application Entry point: `application`
2. Aktiviraj kreirani virtual environment (komandu prikazuje cPanel) i instaliraj zavisnosti:
   ```bash
   pip install -r requirements.txt
   ```
   Alternativno: u cPanel UI → Configuration files → unesi `requirements.txt` i klikni *Run pip install*.
3. **Postavi environment varijable** kroz cPanel (Setup Python App → Environment variables): sve iz tabele iznad. `.env` fajl u produkciji nije neophodan (kod fallback-uje na `os.environ`).
4. **Upload-uj fajlove** u Application root (kroz File Manager ili git): sve osim `.env`, `venv/`, `__pycache__/`.
5. **Restart Python App** iz cPanel-a.

## Endpoint

- `GET /` — `index.html`
- `GET /static/...` — statički fajlovi (CSS, JS, slike)
- `POST /api/contact` — prima JSON `{name, email, phone, message}`
  - `200 {ok: true}` — email poslat
  - `400 {ok: false, error: "..."}` — validacija nije prošla
  - `500 {ok: false, error: "Greška pri slanju, pokušajte ponovo."}` — SMTP problem
