#!/usr/bin/env python3
"""
Quick launcher for Hawk Chat Agent
"""
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hawk_chat_agent import HawkChatAgent

def main():
    print("🚀 Starting Hawk Chat Agent...")
    
    try:
        agent = HawkChatAgent()
        agent.start_chat()
    except KeyboardInterrupt:
        print("\n👋 Chat session ended.")
    except Exception as e:
        print(f"❌ Error starting chat agent: {e}")
        print("Make sure you have:")
        print("1. Valid credentials.json file")
        print("2. .env file with EMAIL_ADDRESS and EMAIL_PASSWORD")
        print("3. Required dependencies installed (pip install -r requirements.txt)")

if __name__ == "__main__":
    main()