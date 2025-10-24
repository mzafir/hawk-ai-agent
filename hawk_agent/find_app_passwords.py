#!/usr/bin/env python3
"""
Help find App Passwords in Google Account
"""
import webbrowser

def find_app_passwords():
    print("🔍 Finding App Passwords in Google Account")
    print("=" * 40)
    
    print("Since 2FA is enabled, try these URLs in order:")
    print()
    
    urls = [
        "https://myaccount.google.com/apppasswords",
        "https://security.google.com/settings/security/apppasswords", 
        "https://myaccount.google.com/u/0/apppasswords",
        "https://accounts.google.com/b/0/IssuedAuthSubTokens"
    ]
    
    for i, url in enumerate(urls, 1):
        print(f"{i}. {url}")
    
    print("\n📝 Alternative method:")
    print("1. Go to: https://myaccount.google.com/security")
    print("2. Scroll down to 'Signing in to Google'")
    print("3. Look for 'App passwords' or '2-Step Verification'")
    print("4. Click on '2-Step Verification'")
    print("5. Scroll down to find 'App passwords'")
    
    choice = input("\nWhich URL should I open? (1-4 or 'manual'): ").strip()
    
    if choice in ['1', '2', '3', '4']:
        url_index = int(choice) - 1
        print(f"Opening: {urls[url_index]}")
        webbrowser.open(urls[url_index])
    elif choice.lower() == 'manual':
        print("Opening Google Account Security page...")
        webbrowser.open("https://myaccount.google.com/security")
    
    print("\n📋 Once you find App Passwords:")
    print("1. Click 'Select app' → Choose 'Mail'")
    print("2. Click 'Select device' → Choose 'Other (Custom name)'")
    print("3. Type: 'Hawk Agent'")
    print("4. Click 'Generate'")
    print("5. Copy the 16-character password (like: abcd efgh ijkl mnop)")
    
    app_password = input("\nPaste your App Password here: ").strip()
    
    if len(app_password.replace(' ', '')) == 16:
        print("✅ App Password format looks correct!")
        
        # Test it
        email = input("Enter your Gmail address: ").strip()
        test_connection(email, app_password)
    else:
        print("❌ App Password should be 16 characters")
        print("Make sure you copied the full password")

def test_connection(email, app_password):
    """Quick test of Gmail connection"""
    try:
        import imaplib
        clean_password = app_password.replace(' ', '')
        
        print("🧪 Testing connection...")
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(email, clean_password)
        mail.select("inbox")
        mail.logout()
        
        print("🎉 SUCCESS! Gmail connection works!")
        print("\nNow you can run Hawk Agent:")
        print("python hawk_agent.py")
        
        # Save to .env
        with open('.env', 'w') as f:
            f.write(f"EMAIL_ADDRESS={email}\n")
            f.write(f"EMAIL_PASSWORD={clean_password}\n")
        print("💾 Credentials saved to .env file")
        
    except Exception as e:
        print(f"❌ Still not working: {e}")
        print("Double-check the App Password and try again")

if __name__ == "__main__":
    find_app_passwords()