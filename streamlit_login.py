import streamlit as st
import pandas as pd
import secrets
import time
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from utils.db import get_engine
from utils.validators import validate_email, validate_password_strength, get_password_strength_indicator
from utils.email_service import send_password_reset_email, send_welcome_email

pwd_context = CryptContext(
    schemes=["argon2", "bcrypt_sha256", "bcrypt"],
    deprecated="auto"
)

# --- Helpers ---
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_user_permissions(conn, email: str) -> dict:
    query = text("""
        SELECT p.schema_name, MAX(p.permission) as max_permission
        FROM auth.users u
        JOIN auth.user_groups ug ON CAST(u.id AS INTEGER) = CAST(ug.user_id AS INTEGER)
        JOIN auth.group_schema_permissions p ON CAST(ug.group_id AS INTEGER) = CAST(p.group_id AS INTEGER)
        WHERE u.email = :email
        GROUP BY p.schema_name;
    """)
    result = conn.execute(query, {"email": email})
                                                                    
    return {row[0]: row[1] for row in result}

def check_login(email: str, password: str, conn) -> bool:
    """
    Ověří přihlašovací údaje včetně kontroly is_active.
    """
    row = conn.execute(
        text("SELECT password_hash, is_active FROM auth.users WHERE email = :email"),
        {"email": email}
    ).fetchone()
    
    if not row:
        return False
    
    hashed, is_active = row[0], row[1]
    
    # Kontrola, zda je účet aktivní
    if not is_active:
        st.error("⛔ Váš účet byl deaktivován. Kontaktujte administrátora.")
        return False
    
    try:
        valid, new_hash = pwd_context.verify_and_update(password, hashed)
    except ValueError as e:
        st.error("Chyba při ověřování hesla.")
        print("DEBUG bcrypt backend error:", e)
        return False
    
    if valid and new_hash:
        # Automatický upgrade hashe na novější schéma (argon2)
        conn.execute(
            text("UPDATE auth.users SET password_hash = :hash WHERE email = :email"),
            {"hash": new_hash, "email": email}
        )
    
    return bool(valid)

def create_password_reset_token(conn, email: str) -> tuple:
    """
    Vytvoří reset token pro daný e-mail.
    
    Returns:
        tuple: (success: bool, token: str, message: str)
    """
    # Ověříme, že uživatel existuje a je aktivní
    user = conn.execute(
        text("SELECT id, is_active FROM auth.users WHERE email = :email"),
        {"email": email}
    ).fetchone()
    
    if not user:
        # Z bezpečnostních důvodů neříkáme, že uživatel neexistuje
        return True, "", "Pokud účet s tímto e-mailem existuje, byl odeslán reset link."
    
    user_id, is_active = user[0], user[1]
    
    if not is_active:
        return False, "", "Tento účet je deaktivován. Kontaktujte administrátora."
    
    # Vygenerujeme bezpečný token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(hours=1)
    
    try:
        # Invalidujeme všechny staré nepoužité tokeny pro tohoto uživatele
        conn.execute(
            text("UPDATE auth.password_resets SET used = TRUE WHERE user_id = :user_id AND used = FALSE"),
            {"user_id": user_id}
        )
        
        # Vytvoříme nový token
        conn.execute(
            text("""
                INSERT INTO auth.password_resets (user_id, token, expires_at)
                VALUES (:user_id, :token, :expires_at)
            """),
            {"user_id": user_id, "token": token, "expires_at": expires_at}
        )
        
        return True, token, "Token byl vytvořen."
        
    except Exception as e:
        print(f"Chyba při vytváření tokenu: {e}")
        return False, "", "Došlo k chybě při vytváření reset tokenu."

def verify_reset_token(conn, token: str) -> tuple:
    """
    Ověří reset token a vrátí user_id.
    
    Returns:
        tuple: (user_id: int or None, email: str or None)
    """
    row = conn.execute(
        text("""
            SELECT pr.user_id, pr.expires_at, pr.used, u.email, u.is_active
            FROM auth.password_resets pr
            JOIN auth.users u ON pr.user_id = u.id
            WHERE pr.token = :token
        """),
        {"token": token}
    ).fetchone()
    
    if not row:
        return None, None
    
    user_id, expires_at, used, email, is_active = row[0], row[1], row[2], row[3], row[4]
    
    # Kontroly platnosti
    if used:
        return None, None
    
    if datetime.now() > expires_at:
        return None, None
    
    if not is_active:
        return None, None
    
    return user_id, email

def complete_password_reset(conn, token: str, new_password: str) -> tuple:
    """
    Dokončí reset hesla pomocí tokenu.
    
    Returns:
        tuple: (success: bool, message: str)
    """
    user_id, email = verify_reset_token(conn, token)
    
    if not user_id:
        return False, "Reset token je neplatný nebo vypršel. Požádejte o nový."
    
    # Hashujeme nové heslo
    hashed = hash_password(new_password)
    
    try:
        # Aktualizujeme heslo
        conn.execute(
            text("UPDATE auth.users SET password_hash = :hash WHERE id = :user_id"),
            {"hash": hashed, "user_id": user_id}
        )
        
        # Označíme token jako použitý
        conn.execute(
            text("UPDATE auth.password_resets SET used = TRUE WHERE token = :token"),
            {"token": token}
        )
        
        return True, f"Heslo bylo úspěšně změněno pro {email}. Nyní se můžete přihlásit."
        
    except Exception as e:
        print(f"Chyba při resetu hesla: {e}")
        return False, "Došlo k chybě při změně hesla. Zkuste to znovu."

# --- UI Formuláře ---

def login_form():
    """Přihlašovací formulář"""
    st.subheader("Přihlášení")
    
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="vas.email@example.com")
        password = st.text_input("Heslo", type="password")
        submitted = st.form_submit_button("🔓 Přihlásit", use_container_width=True)
        
        if submitted:
            # Validace
            if not email or not password:
                st.error("Vyplňte všechna pole.")
                return
            
            with get_engine().begin() as conn:
                                                                              
                if check_login(email, password, conn):
                    st.session_state.logged_in = True
                    st.session_state.user_email = email
                                                                        
                    st.session_state.permissions = get_user_permissions(conn, email)
                    st.success(f"✅ Přihlášen jako {email}")
                    st.rerun()
                else:
                    st.error("❌ Neplatné přihlašovací údaje")
    
    # Odkaz na reset hesla
    st.markdown("---")
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🔑 Zapomněl jsem heslo", use_container_width=True):
            st.session_state.show_password_reset = True
            st.rerun()

def password_reset_request_form():
    """Formulář pro žádost o reset hesla"""
    st.subheader("🔑 Reset hesla")
    st.info("Zadejte váš e-mail a pošleme vám odkaz pro reset hesla.")
    
    with st.form("password_reset_request_form"):
        email = st.text_input("Email", placeholder="vas.email@example.com")
        submitted = st.form_submit_button("📧 Odeslat reset link", use_container_width=True)
        
        if submitted:
            if not email:
                st.error("Zadejte e-mailovou adresu.")
                return
            
            # Validace formátu e-mailu
            is_valid, error_msg = validate_email(email)
            if not is_valid:
                st.error(error_msg)
                return
            
            with get_engine().begin() as conn:
                success, token, message = create_password_reset_token(conn, email)
                
                if success and token:
                    # Odešleme e-mail
                    if send_password_reset_email(email, token):
                        st.success("✅ E-mail s instrukcemi byl odeslán. Zkontrolujte svou schránku.")
                        st.info("💡 Odkaz je platný 1 hodinu.")
                    else:
                        st.error("❌ Chyba při odesílání e-mailu. Zkuste to znovu později.")
                elif success:
                    # Generický message (uživatel neexistuje, ale neříkáme to)
                    st.success("✅ " + message)
                else:
                    st.error("❌ " + message)
    
    st.markdown("---")
    if st.button("← Zpět na přihlášení", use_container_width=True):
        st.session_state.show_password_reset = False
        st.rerun()

def get_groups(conn):
    """Načte seznam skupin z databáze"""
    result = conn.execute(text("SELECT id, name FROM auth.groups ORDER BY name"))
    return {row[1]: row[0] for row in result}

def password_reset_form(token: str):
    """Formulář pro nastavení nového hesla pomocí tokenu"""
    st.subheader("🔐 Nastavení nového hesla")
    
    # Ověříme token hned na začátku
    with get_engine().begin() as conn:
        user_id, email = verify_reset_token(conn, token)
        
        if not user_id:
            st.error("❌ Tento reset link je neplatný nebo vypršel.")
            st.info("⏱ Platnost linku je 1 hodina. Požádejte o nový reset link.")
            
            # Tlačítko MIMO form - bezpečné
            if st.button("🔄 Požádat o nový link", use_container_width=True):
                st.session_state.show_password_reset = True
                st.query_params.clear()
                st.rerun()
            return
    
    st.success(f"✅ Reset link je platný pro: {email}")
    
    # --- ZAČÁTEK FORMULÁŘE ---
    with st.form("password_reset_form"):
        new_password = st.text_input("Nové heslo", type="password", key="reset_new_pass")
        
        # Ukazatel síly hesla
        if new_password:
            strength = get_password_strength_indicator(new_password)
            st.caption(f"Síla hesla: {strength}")
        
        confirm = st.text_input("Potvrzení nového hesla", type="password", key="reset_confirm_pass")
        
        submitted = st.form_submit_button("🔒 Nastavit nové heslo", use_container_width=True)
    # --- KONEC FORMULÁŘE (nic dalšího uvnitř!) ---
    
    # Zpracování MIMO formulář
    if submitted:
        # Kontrola shody hesel
        if new_password != confirm:
            st.error("❌ Hesla se neshodují")
            return
        
        # Validace síly hesla
        is_valid, error_msg = validate_password_strength(new_password)
        if not is_valid:
            st.error(f"❌ {error_msg}")
            return
        
        # Dokončíme reset
        with get_engine().begin() as conn:
            success, message = complete_password_reset(conn, token, new_password)
        
        if success:
            st.success(f"✅ {message}")
            st.balloons()
            
            # KLÍČOVÉ: Vyčistíme URL a state PŘED rerun
            st.query_params.clear()
            st.session_state.show_password_reset = False
            
            # Zobrazíme info zprávu
            st.info("🔄 Přesměrovávám na přihlášení...")
            
            # Krátká pauza pro přečtení zprávy
            import time
            time.sleep(1.5)
            
            # Automatické přesměrování
            st.rerun()
        else:
            st.error(f"❌ {message}")


def register_form():
    """Registrační formulář s automatickým přesměrováním"""
    st.subheader("📝 Registrace nového účtu")
    
    with st.form("register_form"):
        email = st.text_input("Email", placeholder="vas.email@example.com")
        password = st.text_input("Heslo", type="password", key="reg_password")
        
        # Ukazatel síly hesla
        if password:
            strength = get_password_strength_indicator(password)
            st.caption(f"Síla hesla: {strength}")
        
        confirm = st.text_input("Potvrzení hesla", type="password")
        
        with get_engine().begin() as conn:
            groups_dict = get_groups(conn)
        
        if groups_dict:
            requested_group_name = st.selectbox("Požadovaná skupina", options=list(groups_dict.keys()))
        else:
            st.warning("Nejsou dostupné žádné skupiny.")
            requested_group_name = None
        
        submitted = st.form_submit_button("📝 Registrovat", use_container_width=True)
    
    if submitted:
        # Validace e-mailu
        is_valid_email, email_error = validate_email(email)
        if not is_valid_email:
            st.error(f"❌ {email_error}")
            return
        
        # Kontrola shody hesel
        if password != confirm:
            st.error("❌ Hesla se neshodují")
            return
        
        # Validace síly hesla
        is_valid_password, password_error = validate_password_strength(password)
        if not is_valid_password:
            st.error(f"❌ {password_error}")
            return
        
        if not requested_group_name:
            st.error("❌ Vyberte skupinu")
            return

        # Hashování a ukládání
        hashed = hash_password(password)
        requested_group_id = groups_dict.get(requested_group_name)
        
        try:
            with get_engine().begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO auth.users (email, password_hash, requested_group_id)
                        VALUES (:email, :hash, :requested_group_id)
                    """),
                    {"email": email, "hash": hashed, "requested_group_id": requested_group_id}
                )
            
            st.success("✅ Registrace proběhla úspěšně!")
            st.info("🔄 Nyní se můžete přihlásit. Přesměrovávám...")
            
            # Volitelně odešleme uvítací e-mail
            send_welcome_email(email)
            
            # Krátká pauza pro přečtení zprávy
            import time
            time.sleep(2)
            
            # Automatické přesměrování na login
            st.rerun()
            
        except IntegrityError as e:
            if "unique_email" in str(e).lower() or "duplicate" in str(e).lower():
                st.error("❌ Tento e-mail je již registrován.")
            else:
                st.error(f"❌ Chyba databáze: {e}")
        except Exception as e:
            st.error(f"❌ Chyba: {e}")

def change_password_form():
    """Formulář pro změnu hesla přihlášeného uživatele"""
    st.subheader("Změna hesla")
    
    with st.form("change_password_form"):
        old_password = st.text_input("Staré heslo", type="password")
        new_password = st.text_input("Nové heslo", type="password", key="change_new_password")
        
        # Ukazatel síly hesla
        if new_password:
            strength = get_password_strength_indicator(new_password)
            st.caption(f"Síla hesla: {strength}")
        
        confirm = st.text_input("Potvrzení nového hesla", type="password")
        submitted = st.form_submit_button("✔️ Změnit heslo", use_container_width=True)
        
        if submitted:
            if new_password != confirm:
                st.error("❌ Nová hesla se neshodují")
                return
            
            # Validace síly hesla
            is_valid, error_msg = validate_password_strength(new_password)
            if not is_valid:
                st.error(f"❌ {error_msg}")
                return
            
            with get_engine().begin() as conn:
                if not check_login(st.session_state.user_email, old_password, conn):
                        
                    st.error("❌ Staré heslo není správné")
                    return
                
                hashed = hash_password(new_password)
                conn.execute(
                    text("UPDATE auth.users SET password_hash = :hash WHERE email = :email"),
                    {"hash": hashed, "email": st.session_state.user_email}
                )
                st.success("✅ Heslo bylo změněno")

def request_group_form():
    """Formulář pro žádost o přiřazení ke skupině"""
    st.subheader("Žádost o skupinu")
    
    with get_engine().begin() as conn:
        groups_dict = {}
        try:
                                                  
            result = conn.execute(
                text("SELECT id, name FROM auth.groups ORDER BY name")
            )
            groups_dict = {row.name: row.id for row in result}
            
                                                                        
            current_req_row = conn.execute(
                text("""
                    SELECT g.name, u.requested_group_id
                    FROM auth.users u
                    LEFT JOIN auth.groups g ON CAST(u.requested_group_id AS INTEGER) = CAST(g.id AS INTEGER)
                    WHERE u.email = :email
                """),
                {"email": st.session_state.user_email}
            ).first()
            
            if current_req_row:
                current_req_name = current_req_row.name
                current_req_id = current_req_row.requested_group_id
            else:
                current_req_name = None
                current_req_id = None

        except Exception as e:
            st.error(f"Chyba při načítání dat: {e}")
            return
        
                                   
        if current_req_id is None:
            st.caption("Aktuálně nemáš podanou žádost o skupinu.")
        else:
            st.caption(f"✉️ Aktuálně požádáno o skupinu: **{current_req_name}**")
        
        if not groups_dict:
            st.info("Nejsou dostupné žádné skupiny.")
            return
        
                
        with st.form("request_group_form"):
            requested_group_name = st.selectbox(
                "Požadovaná skupina",
                options=list(groups_dict.keys())
            )
            submitted = st.form_submit_button("📤 Odeslat žádost", use_container_width=True)
            
            if submitted:
                requested_group_id = groups_dict.get(requested_group_name)
                try:
                    with get_engine().begin() as conn:
                        conn.execute(
                            text("""
                                UPDATE auth.users
                                SET requested_group_id = CAST(:requested_group_id AS INTEGER)
                                WHERE email = :email
                            """),
                            {
                                "requested_group_id": requested_group_id,
                                "email": st.session_state.user_email
                            }
                        )
                    st.cache_data.clear()
                    st.success(f"✅ Žádost o skupinu '{requested_group_name}' byla odeslána.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Chyba při odesílání žádosti: {e}")

def logout():
    """Odhlášení uživatele"""
    st.session_state.clear()
    st.rerun()