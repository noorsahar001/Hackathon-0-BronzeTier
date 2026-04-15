# Company Handbook

## Core Operating Principles

This handbook defines the rules and guidelines for the AI Employee system. All automated processes and human operators must follow these rules.

---

## Communication Rules

### Email Processing
- **Only process emails marked as important** - Ignore regular/promotional emails
- **Always be polite in replies** - Use professional, courteous language
- **Never send emails without human approval in production mode** - DRY_RUN must be false only after explicit authorization
- **Log every email interaction** - Record sender, subject, timestamp, and action taken

### Response Guidelines
- Acknowledge receipt within 24 hours (when approved)
- Keep responses concise and actionable
- Always include context from the original message
- Use templates for common scenarios

---

## Financial Rules

### Payment Processing
- **Flag any payment over $500 for human approval** - Create high-priority action item
- **Never authorize payments automatically** - All payments require human confirmation
- **Log all financial transactions** - Include amount, recipient, purpose, timestamp
- **Verify account balances before suggesting payments**

### Budget Monitoring
- Track spending against budgets
- Alert when approaching budget limits (80% threshold)
- Weekly financial summary reports

---

## File Management Rules

### Core Principle
- **Never delete files** - Always move to /Done instead
- **Preserve original filenames** - Add timestamps if duplicates exist
- **Create metadata for all files** - Track source, timestamp, status

### Folder Structure
- **/Inbox** - New items awaiting processing
- **/Needs_Action** - Items requiring human attention
- **/Done** - Completed/archived items
- **/Logs** - System logs and activity records
- **/Plans** - Strategic plans and future tasks

### File Naming Convention
- Use descriptive names: `EMAIL_<id>.md`, `TASK_<date>_<description>.md`
- Include timestamps: `YYYY-MM-DD` format
- No spaces in filenames (use underscores)

---

## Action Logging Rules

### What to Log
- **Every action taken** - No exceptions
- **Timestamp** - ISO 8601 format (YYYY-MM-DD HH:MM:SS)
- **Action type** - Email processed, file moved, task created, etc.
- **Result** - Success, failure, pending human review
- **Error details** - If action failed, log the reason

### Log Format
```
[TIMESTAMP] [LEVEL] [COMPONENT] - Action description
```

Example:
```
[2026-04-11 14:30:22] [INFO] [GmailWatcher] - Processed email from john@example.com
[2026-04-11 14:30:25] [WARNING] [GmailWatcher] - Payment of $750 flagged for approval
```

---

## Security Rules

### Credentials
- **Never store credentials in code** - Use environment variables
- **Never commit .env files** - Only commit .env.example
- **Rotate tokens regularly** - Every 90 days minimum
- **Use OAuth2 for Gmail** - Never use password authentication

### Data Privacy
- Don't log sensitive information (passwords, credit cards, SSNs)
- Redact PII in logs when necessary
- Secure file permissions on vault directory

---

## Error Handling Rules

### When Errors Occur
- **Log the error** - Include full stack trace
- **Don't crash** - Gracefully handle and continue
- **Notify human** - Create action item for critical errors
- **Retry with backoff** - For transient failures (network issues)

### Recovery Procedures
- Maintain state to resume after crashes
- Track processed items to avoid duplicates
- Validate data before processing

---

## Testing Rules

### Development Mode
- **DRY_RUN=true by default** - Never take real actions during testing
- **Use test data** - Don't test with production emails/files
- **Log all would-be actions** - Show what would happen in production

### Before Production
- Test all watchers independently
- Verify error handling
- Confirm logging works correctly
- Get human approval for production deployment

---

## Human Oversight

### When to Request Human Approval
- Any financial transaction
- Sending emails (until proven reliable)
- Deleting or modifying important files
- Unusual patterns detected
- System errors that can't be auto-resolved

### Escalation Priorities
- **CRITICAL** - System down, security breach, data loss
- **HIGH** - Payment approval needed, important email requires response
- **MEDIUM** - Unusual activity, non-critical errors
- **LOW** - Informational, routine summaries

---

## Continuous Improvement

### Review Cycle
- Weekly review of logs and actions
- Monthly handbook updates based on learnings
- Quarterly system optimization

### Metrics to Track
- Response time to emails
- Error rate
- Human intervention frequency
- Task completion rate

---

*Last Updated: 2026-04-11*
*Version: 1.0*
