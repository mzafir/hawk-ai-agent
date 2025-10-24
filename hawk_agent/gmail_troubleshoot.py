#!/usr/bin/env python3
"""
Gmail troubleshooting and setup helper
"""
import webbrowser

def check_gmail_setup():
    print("🔧 Gmail Access Troubleshooting")
    print("=" * 35)
    
    print("\n📋 Step 1: Check 2-Factor Authentication")
    print("1. Go to: https://myaccount.google.com/security")
    print("2. Look for '2-Step Verification' section")
    
    has_2fa = input("\nDo you see '2-Step Verification' as ON? (y/n): ").lower().strip()
    
    if has_2fa != 'y':
        print("\n❌ 2-Factor Authentication is required for App Passwords")
        print("📝 Enable 2FA first:")
        print("1. Go to: https://myaccount.google.com/security")
        print("2. Click '2-Step Verification'")
        print("3. Follow setup instructions")
        
        open_link = input("\nOpen 2FA setup link? (y/n): ").lower().strip()
        if open_link == 'y':
            webbrowser.open("https://myaccount.google.com/security")
        return False
    
    print("\n📋 Step 2: Create App Password")
    print("1. Go to: https://myaccount.google.com/apppasswords")
    print("2. Select app: 'Mail'")
    print("3. Select device: 'Other (Custom name)'")
    print("4. Enter: 'Hawk Agent'")
    print("5. Click 'Generate'")
    
    open_app_passwords = input("\nOpen App Passwords page? (y/n): ").lower().strip()
    if open_app_passwords == 'y':
        webbrowser.open("https://myaccount.google.com/apppasswords")
    
    print("\n📝 Alternative URLs to try:")
    print("- https://security.google.com/settings/security/apppasswords")
    print("- https://myaccount.google.com/u/0/apppasswords")
    
    app_password = input("\nEnter your 16-character App Password (or 'skip'): ").strip()
    
    if app_password.lower() == 'skip':
        return False
    
    if len(app_password.replace(' ', '')) != 16:
        print("❌ App Password should be 16 characters")
        return False
    
    # Test the connection
    email_address = input("Enter your Gmail address: ").strip()
    
    print(f"\n🧪 Testing Gmail connection...")
    return test_gmail_connection(email_address, app_password)

def test_gmail_connection(email_address, app_password):
    """Test Gmail IMAP connection"""
    try:
        import imaplib
        
        # Remove spaces from app password
        clean_password = app_password.replace(' ', '')
        
        print("Connecting to Gmail IMAP...")
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(email_address, clean_password)
        mail.select("inbox")
        
        # Test search
        status, messages = mail.search(None, 'ALL')
        email_count = len(messages[0].split()) if messages[0] else 0
        
        mail.logout()
        
        print(f"✅ Gmail connection successful!")
        print(f"📧 Found {email_count} emails in inbox")
        
        # Save credentials for future use
        save_creds = input("\nSave credentials for Hawk Agent? (y/n): ").lower().strip()
        if save_creds == 'y':
            with open('.env', 'a') as f:
                f.write(f"\nEMAIL_ADDRESS={email_address}\n")
                f.write(f"EMAIL_PASSWORD={clean_password}\n")
            print("💾 Credentials saved to .env file")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        
        if "Application-specific password required" in str(e):
            print("\n💡 Solutions:")
            print("1. Make sure 2FA is enabled")
            print("2. Use App Password, not regular password")
            print("3. Try: https://myaccount.google.com/apppasswords")
        
        return False

if __name__ == "__main__":
    if check_gmail_setup():
        print("\n🎉 Gmail setup complete! You can now run Hawk Agent.")
        print("Run: python hawk_agent.py")
    else:
        print("\n🔧 Please complete Gmail setup and try again.")