# Notifications Module

Modul pro správu a odesílání emailových notifikací v Data Browser aplikaci.

## Struktura

```
notifications/
├── __init__.py              # Module exports
├── email_service.py         # Hlavní služba pro odesílání emailů
├── template_engine.py       # Engine pro renderování šablon
└── templates/               # Email šablony
    ├── base.html           # Základní HTML layout
    ├── welcome.html        # Uvítací email
    ├── password_reset.html # Reset hesla
    ├── cs/                 # České textové verze
    │   ├── welcome.txt
    │   └── password_reset.txt
    └── en/                 # Anglické textové verze
        ├── welcome.txt
        └── password_reset.txt
```

## Použití

### Základní použití

```python
from notifications.email_service import EmailService

# Odeslání uvítacího emailu
EmailService.send_welcome_email("user@example.com")

# Odeslání reset hesla
EmailService.send_password_reset_email("user@example.com", "reset_token_xyz")

# Odeslání notifikace o schválení skupiny
EmailService.send_group_approval_notification("user@example.com", "Editors")
```

### Konfigurace SMTP

SMTP konfigurace se načítá ze `secrets.toml`:

```toml
SMTP_SERVER = "smtp.mailersend.net"
SMTP_PORT = 587
SMTP_USER = "user@example.com"
SMTP_PASSWORD = "your_password"
SMTP_SENDER_NAME = "Data Browser"
```

## EmailService

Hlavní třída pro odesílání emailů.

### Metody

#### `send_welcome_email(recipient_email: str) -> bool`

Odešle uvítací email po registraci.

**Parametry:**
- `recipient_email`: Email adresa příjemce

**Returns:** `True` pokud se odeslání podařilo

**Příklad:**
```python
success = EmailService.send_welcome_email("newuser@example.com")
if success:
    print("Welcome email sent!")
```

#### `send_password_reset_email(recipient_email: str, reset_token: str) -> bool`

Odešle email s odkazem pro reset hesla.

**Parametry:**
- `recipient_email`: Email adresa příjemce
- `reset_token`: Jedinečný token pro reset

**Returns:** `True` pokud se odeslání podařilo

**Příklad:**
```python
token = "abc123xyz"
success = EmailService.send_password_reset_email("user@example.com", token)
```

#### `send_group_approval_notification(recipient_email: str, group_name: str) -> bool`

Odešle notifikaci o schválení přístupu ke skupině.

**Parametry:**
- `recipient_email`: Email adresa příjemce
- `group_name`: Název schválené skupiny

**Returns:** `True` pokud se odeslání podařilo

## TemplateEngine

Engine pro renderování email šablon s podporou lokalizace.

### Metody

#### `render_text(template_name: str, context: Dict[str, Any], locale: str = "cs") -> str`

Vykreslí textovou verzi emailu.

**Parametry:**
- `template_name`: Jméno šablony (bez přípony)
- `context`: Slovník s daty pro šablonu
- `locale`: Jazyková mutace (`cs` nebo `en`)

**Returns:** Vykreslený text

**Příklad:**
```python
from notifications.template_engine import TemplateEngine

engine = TemplateEngine()
text = engine.render_text(
    "welcome",
    {"app_name": "Data Browser", "app_url": "https://app.com"},
    locale="cs"
)
```

#### `render_html(template_name: str, context: Dict[str, Any]) -> str`

Vykreslí HTML verzi emailu.

**Parametry:**
- `template_name`: Jméno šablony (bez přípony)
- `context`: Slovník s daty pro šablonu

**Returns:** Vykreslený HTML

## Tvorba vlastních šablon

### 1. HTML šablony

Vytvořte soubor `templates/muj_email.html`:

```html
<div class="email-header">
    <h1>{{title}}</h1>
</div>

<div class="email-content">
    <p>{{message}}</p>
    
    <div class="button-container">
        <a href="{{action_url}}" class="button">{{button_text}}</a>
    </div>
</div>

<div class="email-footer">
    <p>S pozdravem,<br>{{app_name}} tým</p>
</div>
```

### 2. Textové šablony

Vytvořte soubor `templates/cs/muj_email.txt`:

```
=====================================
{{title}}
=====================================

{{message}}

Odkaz: {{action_url}}

S pozdravem,
{{app_name}} tým
```

### 3. Použití vlastní šablony

```python
from notifications.email_service import EmailService

class CustomEmailService(EmailService):
    @staticmethod
    def send_custom_email(recipient: str, title: str, message: str):
        service = EmailService()
        
        context = {
            "title": title,
            "message": message,
            "action_url": "https://app.com/action",
            "button_text": "Klikněte zde",
            "app_name": service.app_config.app_name
        }
        
        text_body = service.template_engine.render_text("muj_email", context)
        html_body = service.template_engine.render_html("muj_email", context)
        
        message = service._create_message(
            recipient=recipient,
            subject=title,
            text_body=text_body,
            html_body=html_body
        )
        
        return service._send_message(message)
```

## Placeholder systém

Šablony používají jednoduchý placeholder systém s dvojitými závorkami:

- `{{variable}}` - bude nahrazeno hodnotou z contextu

**Dostupné proměnné v základních šablonách:**

### Welcome email
- `{{app_name}}` - Název aplikace
- `{{app_url}}` - URL aplikace

### Password reset
- `{{app_name}}` - Název aplikace
- `{{reset_url}}` - URL pro reset hesla
- `{{expiry_hours}}` - Počet hodin platnosti

## CSS styly

Šablony používají inline CSS pro maximální kompatibilitu s email klienty.

Dostupné CSS třídy v `base.html`:
- `.email-header` - Hlavička emailu (zelená)
- `.email-content` - Hlavní obsah
- `.email-footer` - Patička
- `.button` - Zelené tlačítko pro akce
- `.button-container` - Kontejner pro centrování tlačítka
- `.info-box` - Modrý informační box
- `.warning-box` - Oranžový varovný box
- `.success-box` - Zelený úspěšný box
- `.small-text` - Menší text (0.85em)
- `.divider` - Horizontální dělící čára

## Lokalizace

Aplikace podporuje dvě jazykové mutace:

### České šablony (`cs/`)
- Výchozí jazyk aplikace
- Používá se pokud není specifikováno jinak

### Anglické šablony (`en/`)
- Alternativní jazyk
- Použijte přepnutím `locale="en"` při renderování

**Přidání nového jazyka:**

1. Vytvořte složku `templates/sk/` (např. pro slovenštinu)
2. Vytvořte `.txt` soubory pro každou šablonu
3. Použijte `render_text(..., locale="sk")`

## Error handling

EmailService zachytává následující chyby:

- `EmailError` - Obecná chyba při odesílání
- `SMTPAuthenticationError` - Chyba autentizace
- `SMTPException` - SMTP chyby

**Příklad:**

```python
from core.exceptions import EmailError

try:
    EmailService.send_welcome_email("user@example.com")
except EmailError as e:
    logger.error(f"Failed to send email: {e}")
    # Fallback logika
```

## Testování

### Testování šablon

```python
from notifications.template_engine import TemplateEngine

engine = TemplateEngine()

# Test renderování
context = {"app_name": "Test App", "app_url": "http://test.com"}
html = engine.render_html("welcome", context)
print(html)
```

### Testování bez SMTP

Pro testování bez skutečného odesílání emailů:

```python
# V secrets.toml nastavte prázdné hodnoty
SMTP_USER = ""
SMTP_PASSWORD = ""

# EmailService automaticky přeskočí odesílání
result = EmailService.send_welcome_email("test@example.com")
# result bude False, ale bez chyby
```

## Best Practices

1. **Vždy použijte try-except** při odesílání emailů
2. **Logujte všechny email operace** pro debugging
3. **Testujte šablony** před nasazením do produkce
4. **Používejte textové i HTML verze** pro kompatibilitu
5. **Neposílejte citlivá data** v emailech
6. **Kontrolujte SMTP konfiguraci** před spuštěním
7. **Používejte rate limiting** pro hromadné emaily

## Troubleshooting

### Email se neodešle

1. Zkontrolujte SMTP credentials v `secrets.toml`
2. Ověřte, že SMTP server je dostupný
3. Zkontrolujte logy: `logs/app.log`
4. Ověřte firewall pravidla

### Šablona se nenačte

1. Zkontrolujte, že soubor existuje v `templates/`
2. Ověřte správnou cestu: `templates/cs/welcome.txt`
3. Engine použije fallback pokud soubor chybí

### Placeholder se nevykreslí

1. Zkontrolujte syntax: `{{variable}}` (dvojité závorky)
2. Ověřte, že klíč existuje v contextu
3. Placeholder musí být exact match (case-sensitive)

## Závislosti

- `smtplib` - Odesílání emailů (standardní knihovna)
- `email.mime` - MIME zprávy (standardní knihovna)
- `config.settings` - Konfigurace aplikace
- `core.logger` - Logování
- `core.exceptions` - Custom výjimky
