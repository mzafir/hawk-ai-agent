# 💬 Hawk Chat Agent - Conversational Interface

A conversational AI agent that analyzes emails and project communications to answer natural language questions about project status, communication bottlenecks, and responsibilities.

## 🎯 Key Features

- **Natural Language Queries**: Ask questions like "Do you see any communication related to tusd?"
- **Communication Analysis**: Identifies who communications are waiting on
- **Bottleneck Detection**: Finds stuck or blocked communications
- **Responsibility Tracking**: Shows who needs to respond to what
- **Memory**: Remembers conversation context for better responses

## 🚀 Quick Start

### Demo Version (No Setup Required)
```bash
python hawk_chat_demo.py
```

### Full Version (Requires Setup)
```bash
python start_chat.py
```

## 💬 Example Conversations

**User:** "Do you see any communication related to tusd?"

**Hawk:** "📧 I found 3 communications related to tusd:

1. **TUSD - Budget Approval Needed for Q4**
   From: john.smith@tusd.edu
   Date: Mon, 18 Dec 2023 14:30:00
   Preview: Hi team, we need approval for the Q4 budget allocation...

⚠️ **Communications needing attention:**
• 'TUSD - Budget Approval Needed for Q4' - waiting on External vendor/partner"

---

**User:** "Who is the communication hung on?"

**Hawk:** "🚫 Found 2 potentially stuck communications:

**TUSD Technology Rollout Timeline**
• Waiting 5 days for response
• From: sarah.johnson@vendor.com
• Needs attention from: TUSD team

**K12 Platform Integration Status**
• Waiting 7 days for response
• From: lisa.wong@techpartner.com
• Needs attention from: TUSD team"

## 🎭 Demo Mode Features

The demo version includes:
- 5 realistic mock emails for TUSD project
- 3 sample projects with different statuses
- Communication pattern analysis
- Bottleneck detection
- No credentials required

## 🔧 Full Version Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup Google Sheets API**
   ```bash
   python setup_credentials.py
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your email credentials
   ```

4. **Start Chat**
   ```bash
   python start_chat.py
   ```

## 💡 Available Commands

### In Chat:
- `load project [name/number]` - Load project data
- `load emails [project]` - Load email data
- `help` - Show help information
- `quit` - Exit chat

### Example Queries:
- "Do you see any communication related to [company]?"
- "Who is the communication hung on?"
- "What communications are stuck?"
- "Show me the project status"
- "Who needs to respond?"
- "Are there any pending responses?"

## 🧠 How It Works

1. **Entity Extraction**: Identifies company/project names from your query
2. **Email Search**: Finds relevant communications in loaded data
3. **Pattern Analysis**: Analyzes communication patterns and timing
4. **Bottleneck Detection**: Identifies stuck communications based on:
   - Time since last activity
   - Question indicators in content
   - Response patterns
5. **Responsibility Assignment**: Determines who should respond based on:
   - Email domains (internal vs external)
   - Communication context
   - Historical patterns

## 🔍 Analysis Capabilities

- **Communication Tracking**: Who's talking to whom
- **Response Timing**: How long communications have been waiting
- **Bottleneck Identification**: Where communications get stuck
- **Responsibility Mapping**: Who should respond to what
- **Pattern Recognition**: Recurring communication issues

## 🎯 Use Cases

- **Project Managers**: Track communication status across projects
- **Sales Teams**: Monitor prospect communication health
- **Customer Success**: Identify at-risk client communications
- **Operations**: Find process bottlenecks in email workflows

## 🔒 Privacy & Security

- All analysis happens locally
- No email content is stored permanently
- Uses AWS Bedrock for AI analysis (if configured)
- Respects existing Google Sheets and Gmail permissions

## 🛠️ Troubleshooting

**"No communications found"**
- Load project data first: `load project [name]`
- Load emails: `load emails [project]`
- Check entity spelling in your query

**"Email connection failed"**
- Verify .env file has correct EMAIL_ADDRESS and EMAIL_PASSWORD
- Use Gmail App Password, not regular password
- Enable 2-factor authentication

**"Google Sheets not connected"**
- Run `python setup_credentials.py`
- Ensure credentials.json is valid
- Check spreadsheet sharing permissions