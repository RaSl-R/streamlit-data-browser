"""
Template engine pro email šablony
"""
from pathlib import Path
from typing import Dict, Any, Optional
from core.logger import logger

class TemplateEngine:
    """Jednoduchý template engine pro email šablony"""
    
    def __init__(self, templates_dir: str = "notifications/templates"):
        self.templates_dir = Path(templates_dir)
        
    def _load_template(self, template_path: Path) -> Optional[str]:
        """
        Načte šablonu ze souboru.
        
        Args:
            template_path: Cesta k šabloně
            
        Returns:
            Obsah šablony nebo None
        """
        try:
            if not template_path.exists():
                logger.warning(f"Template not found: {template_path}")
                return None
            
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error loading template {template_path}: {e}")
            return None
    
    def _render_template(self, template: str, context: Dict[str, Any]) -> str:
        """
        Vykreslí šablonu s kontextem (jednoduchá replace substituce).
        
        Args:
            template: Šablona jako string
            context: Slovník s hodnotami pro substituci
            
        Returns:
            Vykreslená šablona
        """
        result = template
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))
        return result
    
    def render_text(
        self,
        template_name: str,
        context: Dict[str, Any],
        locale: str = "cs"
    ) -> str:
        """
        Vykreslí textovou verzi emailu.
        
        Args:
            template_name: Jméno šablony (bez přípony)
            context: Kontext pro vykreslení
            locale: Jazyková mutace (cs/en)
            
        Returns:
            Vykreslená textová šablona
        """
        # Pokusíme se načíst lokalizovanou verzi
        template_path = self.templates_dir / locale / f"{template_name}.txt"
        template = self._load_template(template_path)
        
        # Fallback na základní verzi
        if not template:
            template = self._get_default_text_template(template_name)
        
        return self._render_template(template, context)
    
    def render_html(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Vykreslí HTML verzi emailu.
        
        Args:
            template_name: Jméno šablony (bez přípony)
            context: Kontext pro vykreslení
            
        Returns:
            Vykreslená HTML šablona
        """
        # Načteme HTML šablonu
        template_path = self.templates_dir / f"{template_name}.html"
        template = self._load_template(template_path)
        
        # Fallback na základní verzi
        if not template:
            template = self._get_default_html_template(template_name)
        
        # Načteme base template a vložíme do něj content
        base_template = self._load_base_template()
        
        # Vykreslíme content
        rendered_content = self._render_template(template, context)
        
        # Vložíme do base
        context_with_content = {**context, "content": rendered_content}
        return self._render_template(base_template, context_with_content)
    
    def _load_base_template(self) -> str:
        """Načte base HTML šablonu"""
        base_path = self.templates_dir / "base.html"
        base = self._load_template(base_path)
        
        if not base:
            # Fallback na minimální base
            return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { 
            font-family: Arial, sans-serif; 
            line-height: 1.6; 
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            background-color: #4CAF50;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 5px 5px 0 0;
        }
        .content {
            background-color: #f9f9f9;
            padding: 30px;
            border-radius: 0 0 5px 5px;
        }
        .button {
            background-color: #4CAF50;
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 4px;
            display: inline-block;
            margin: 20px 0;
        }
        .footer {
            text-align: center;
            color: #999;
            font-size: 0.8em;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }
    </style>
</head>
<body>
    {{content}}
</body>
</html>
"""
        return base
    
    def _get_default_text_template(self, template_name: str) -> str:
        """Vrátí výchozí textovou šablonu"""
        templates = {
            "password_reset": """
Dobrý den,

obdrželi jsme požadavek na reset hesla pro váš účet v aplikaci {{app_name}}.

Pro reset hesla klikněte na následující odkaz:
{{reset_url}}

Odkaz je platný {{expiry_hours}} hodinu.

Pokud jste o reset hesla nežádali, ignorujte tento e-mail.

S pozdravem,
{{app_name}} tým
""",
            "welcome": """
Vítejte v aplikaci {{app_name}}!

Váš účet byl úspěšně vytvořen.

Nyní se můžete přihlásit a začít pracovat s daty:
{{app_url}}

S pozdravem,
{{app_name}} tým
"""
        }
        
        return templates.get(template_name, "{{content}}")
    
    def _get_default_html_template(self, template_name: str) -> str:
        """Vrátí výchozí HTML šablonu"""
        templates = {
            "password_reset": """
<div class="header">
    <h1>Reset hesla</h1>
</div>
<div class="content">
    <p>Dobrý den,</p>
    <p>obdrželi jsme požadavek na reset hesla pro váš účet v aplikaci <strong>{{app_name}}</strong>.</p>
    <p>Pro reset hesla klikněte na tlačítko níže:</p>
    <p style="text-align: center;">
        <a href="{{reset_url}}" class="button">Resetovat heslo</a>
    </p>
    <p style="color: #666; font-size: 0.9em;">
        Odkaz je platný {{expiry_hours}} hodinu.
    </p>
    <p style="color: #666; font-size: 0.9em;">
        Pokud jste o reset hesla nežádali, ignorujte tento e-mail.
    </p>
</div>
<div class="footer">
    <p>S pozdravem,<br>{{app_name}} tým</p>
</div>
""",
            "welcome": """
<div class="header">
    <h1>Vítejte v {{app_name}}!</h1>
</div>
<div class="content">
    <p>Dobrý den,</p>
    <p>Váš účet byl úspěšně vytvořen.</p>
    <p>Nyní se můžete přihlásit a začít pracovat s daty.</p>
    <p style="text-align: center;">
        <a href="{{app_url}}" class="button">Přihlásit se</a>
    </p>
</div>
<div class="footer">
    <p>S pozdravem,<br>{{app_name}} tým</p>
</div>
"""
        }
        
        return templates.get(template_name, "<div>{{content}}</div>")