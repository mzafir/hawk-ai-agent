#!/usr/bin/env python3
"""
Quick demo runner for Hawk Agent
"""
import sys
from demo_k1k12 import main as demo_k1k12
from hawk_agent import HawkAgent

def show_menu():
    print("🦅 Hawk Agent - Demo Menu")
    print("=" * 30)
    print("1. K1-K12 Project Demo (with mock emails)")
    print("2. Full Analysis (requires Gmail setup)")
    print("3. Gmail Setup Instructions")
    print("4. Exit")
    print()

def main():
    while True:
        show_menu()
        choice = input("Select option (1-4): ").strip()
        
        if choice == "1":
            print("\n🚀 Running K1-K12 Demo with Claude Analysis...")
            demo_k1k12()
            break
            
        elif choice == "2":
            print("\n🚀 Running Full Hawk Agent...")
            agent = HawkAgent()
            agent.run_analysis()
            break
            
        elif choice == "3":
            print("\n📧 Gmail Setup Instructions:")
            print("See GMAIL_SETUP.md for detailed instructions")
            print("Quick steps:")
            print("1. Enable 2-Factor Authentication")
            print("2. Create App Password for 'Mail'")
            print("3. Use the 16-character App Password (not regular password)")
            print()
            
        elif choice == "4":
            print("👋 Goodbye!")
            sys.exit(0)
            
        else:
            print("❌ Invalid choice. Please select 1-4.")
            print()

if __name__ == "__main__":
    main()