# Reconnaissance Scenarios & Automation Workflows

## Overview

This document outlines reconnaissance scenarios and automation workflows based on proven bug bounty and security research methodologies. These workflows leverage open-source OSINT tools to automate the enumeration and discovery phase of security assessments.

**Source Reference:** [Recon with Me - Dhiyanesh Geek](https://dhiyaneshgeek.github.io/bug/bounty/2020/02/06/recon-with-me/)

---

## 🎯 Core Reconnaissance Workflow

### Phase 1: Subdomain Enumeration

**Primary Tool:** Subfinder (ProjectDiscovery)

**Basic Usage:**
```bash
subfinder -d target.com
```

**Verbose Mode (View Sources):**
```bash
subfinder -d target.com -v
```

**Key Points:**
- Can discover 50,000+ subdomains quickly
- Uses multiple passive sources: Chaos, ThreatMiner, Sublist3r, AlienVault, etc.
- **Critical:** API keys significantly improve results (see API Key Setup below)

**Results Comparison:**
- **Without API Keys:** ~50,246 subdomains
- **With Free API Keys:** ~165,063 subdomains (+114,817 additional)
- **Trade-off:** API-based enumeration is slower but more comprehensive

---

## 🔑 API Key Configuration

### Why API Keys Matter

Many Subfinder sources require API keys to function. Without them, you're limited to free/public sources. With API keys, you can access premium data sources that significantly increase discovery rates.

**Location:** `~/.config/subfinder/config.yaml`

### Free API Key Sources

All of the following services offer **free tiers** with limited requests:

#### 1. BinaryEdge
- **Signup:** https://app.binaryedge.io/account/api
- **Steps:**
  1. Sign up and verify account
  2. Navigate to API settings
  3. Generate token

#### 2. Censys
- **Signup:** https://censys.io/account/api
- **Steps:**
  1. Sign up and verify account
  2. Get API ID and Secret

#### 3. Certspotter
- **Signup:** https://sslmate.com/account/api_credentials
- **Limits:** 100 queries/hour (free)
- **Steps:**
  1. Sign up
  2. Get API key from account settings

#### 4. Chaos (ProjectDiscovery)
- **Signup:** https://chaos.projectdiscovery.io/#/
- **Access:** 
  - Early access via signup queue (weekly invites)
  - Contributor access via PRs to `github.com/projectdiscovery/*`

#### 5. DNSdb
- **Signup:** Community account (requires company email - can use temp email)
- **Limits:** 30-day renewal with email confirmation
- **Steps:**
  1. Sign up with company email
  2. Verify email
  3. Get API key

#### 6. GitHub
- **Signup:** https://github.com/settings/tokens
- **Steps:**
  1. Create personal access token
  2. Add to config

#### 7. IntelX
- **Signup:** https://intelx.io/account?tab=developer
- **Limits:** 1 week trial (free)
- **Steps:**
  1. Sign up and verify
  2. Get API details from developer tab

#### 8. PassiveTotal (RiskIQ)
- **Signup:** https://community.riskiq.com/settings
- **Steps:**
  1. Sign up and verify
  2. Get KEY and Secret from settings

#### 9. Robtex
- **Signup:** https://www.robtex.com/dashboard/
- **Steps:**
  1. Sign in with Google account
  2. Get API key from dashboard

#### 10. SecurityTrails
- **Signup:** https://securitytrails.com/app/account/credentials
- **Limits:** 50 API requests/month (free)
- **Steps:**
  1. Sign up and verify
  2. Get API key from credentials page

#### 11. Shodan
- **Signup:** https://account.shodan.io/
- **Steps:**
  1. Register account
  2. Get API key from account page

#### 12. Spyse
- **Signup:** https://spyse.com/user
- **Limits:** 100 API tokens valid for 5 days (trial)
- **Steps:**
  1. Register and verify
  2. Get API token from user page

#### 13. URLScan
- **Signup:** https://urlscan.io/user/profile/
- **Steps:**
  1. Sign up and verify
  2. Create new API key

#### 14. VirusTotal
- **Signup:** https://www.virustotal.com/gui/user/username/apikey
- **Steps:**
  1. Register and verify
  2. Get API key from user settings

#### 15. ZoomEye
- **Signup:** https://www.zoomeye.org/profile
- **Steps:**
  1. Register account
  2. Get API key from profile

---

## 🔄 Complete Automation Workflow

### Workflow Components

1. **Subfinder** - Subdomain enumeration
2. **Httpx** - HTTP probe (check alive domains)
3. **Nuclei** - Vulnerability scanning
4. **Notify** - Slack/Discord notifications
5. **Anew** - Deduplication and new domain detection

### Initial Setup (First Run)

**Purpose:** Establish baseline subdomain list

```bash
subfinder -silent -dL domains.txt | anew subs.txt
```

**Parameters:**
- `-silent`: Suppress banner/verbose output
- `-dL`: Read domains from file
- `anew`: Only add new subdomains (avoids duplicates)

**Output:** `subs.txt` with all discovered subdomains

### Continuous Monitoring (Automated)

**Purpose:** Find new subdomains, check if alive, scan for vulnerabilities, and notify

```bash
while true; do 
  subfinder -dL domains.txt -all | anew subs.txt | httpx | nuclei -t nuclei-templates/ | notify
  sleep 3600
done
```

**Workflow Breakdown:**
1. **`subfinder -dL domains.txt -all`** - Enumerate all subdomains (with API keys)
2. **`anew subs.txt`** - Filter only new subdomains (not in existing list)
3. **`httpx`** - Probe HTTP/HTTPS services (filter alive domains)
4. **`nuclei -t nuclei-templates/`** - Scan for vulnerabilities using templates
5. **`notify`** - Send results to Slack/Discord
6. **`sleep 3600`** - Wait 1 hour before next iteration

**Benefits:**
- ✅ Focuses on **NEW** subdomains only (no duplicates)
- ✅ Automatically checks if domains are alive
- ✅ Scans for vulnerabilities immediately
- ✅ Real-time notifications
- ✅ Continuous monitoring (runs every hour)

---

## 📊 Real-World Impact

### Example Scenario

**Timeline:**
- **3:54 PM** - Alert received (new subdomain discovered)
- **3:59 PM** - Vulnerability reported to bug bounty program
- **Result:** Triaged and Validated ✅

**Key Success Factors:**
1. **Automation** - Continuous monitoring catches new assets immediately
2. **Deduplication** - Focus on new findings only
3. **Speed** - Quick notification enables fast response
4. **Comprehensive** - API keys provide maximum coverage

---

## 🛠️ Tool Integration with Our OSINT Framework

### Mapping to Our Tools

| Recon Tool | Our Implementation | Status |
|------------|-------------------|--------|
| **Subfinder** | `subfinder_langchain.py` / `subfinder_crewai.py` | ✅ Implemented |
| **Nuclei** | `nuclei_langchain.py` / `nuclei_crewai.py` | ✅ Implemented |
| **Httpx** | Not yet implemented | ⚠️ Future |
| **Notify** | Not yet implemented | ⚠️ Future |
| **Anew** | Not yet implemented | ⚠️ Future |

### Recommended Workflow Integration

Our OSINT tools can be integrated into this workflow:

```python
# Phase 1: Subdomain Enumeration
subdomains = subfinder_enum(domain="target.com")

# Phase 2: Filter Alive (requires httpx implementation)
alive_domains = httpx_probe(subdomains)

# Phase 3: Vulnerability Scanning
vulnerabilities = nuclei_scan(targets=alive_domains)

# Phase 4: Notification (requires notify implementation)
notify_slack(vulnerabilities)
```

---

## 🎯 Use Cases

### Use Case 1: Continuous Subdomain Monitoring

**Scenario:** Monitor a target domain for new subdomains

**Workflow:**
1. Run Subfinder with API keys configured
2. Compare against baseline using Anew
3. Alert on new discoveries

**Implementation:**
```python
# Initial baseline
baseline = subfinder_enum(domain="target.com")

# Continuous monitoring
while True:
    current = subfinder_enum(domain="target.com")
    new = filter_new_subdomains(current, baseline)
    if new:
        notify(new)
    time.sleep(3600)  # Check every hour
```

### Use Case 2: Vulnerability Discovery Pipeline

**Scenario:** Automated vulnerability scanning of new assets

**Workflow:**
1. Discover subdomains
2. Filter alive domains
3. Scan with Nuclei
4. Report findings

**Implementation:**
```python
# Discover
subdomains = subfinder_enum(domain="target.com")

# Filter alive (when httpx implemented)
alive = httpx_probe(subdomains)

# Scan
for domain in alive:
    findings = nuclei_scan(target=domain)
    if findings:
        report(findings)
```

### Use Case 3: Bug Bounty Automation

**Scenario:** Continuous monitoring for bug bounty programs

**Workflow:**
1. Monitor multiple domains
2. Detect new subdomains
3. Immediate vulnerability scanning
4. Real-time notifications

**Benefits:**
- First to discover new assets
- Fast vulnerability reporting
- Competitive advantage in bug bounties

---

## 📝 Configuration Files

### Subfinder Config

**Location:** `~/.config/subfinder/config.yaml`

**Structure:**
```yaml
binaryedge:
  - api-key-here

censys:
  - api-id
  - api-secret

certspotter:
  - api-key-here

# ... (other services)
```

### Notify Config

**Location:** `~/.config/notify/notify.conf`

**Required Fields:**
- `slack_webhookurl` - Slack webhook URL
- `slack_username` - Bot username
- `slack_channel` - Channel name
- `slack` - Enable Slack notifications

**Slack Webhook Setup:**
1. Go to https://api.slack.com/apps
2. Create new app
3. Enable "Incoming Webhooks"
4. Add webhook to workspace
5. Copy webhook URL

---

## 🚀 Deployment Recommendations

### VPS Deployment

**Recommended Platforms:**
- Digital Ocean
- AWS EC2
- Google Cloud Platform

**Why VPS?**
- ✅ Continuous uptime
- ✅ Better network performance
- ✅ Isolated environment
- ✅ Cost-effective for automation

### Docker Deployment

Our tools support Docker execution, making VPS deployment easier:

```bash
# Run Subfinder in Docker
docker run --rm projectdiscovery/subfinder:latest -d target.com

# Run Nuclei in Docker
docker run --rm projectdiscovery/nuclei:latest -u https://target.com
```

---

## 📚 Additional Resources

### ProjectDiscovery Tools
- **Subfinder:** https://github.com/projectdiscovery/subfinder
- **Nuclei:** https://github.com/projectdiscovery/nuclei
- **Httpx:** https://github.com/projectdiscovery/httpx
- **Notify:** https://github.com/projectdiscovery/notify

### Nuclei Templates
- **Repository:** https://github.com/projectdiscovery/nuclei-templates
- **Categories:** CVEs, misconfigurations, security issues

### Other Tools
- **Anew:** https://github.com/tomnomnom/anew
- **Chaos:** https://chaos.projectdiscovery.io/

---

## 🔐 Security Considerations

### API Key Management

1. **Environment Variables:** Store API keys in environment variables, not in code
2. **Secrets Management:** Use tools like HashiCorp Vault or AWS Secrets Manager
3. **Rotation:** Regularly rotate API keys
4. **Limits:** Monitor API usage to avoid rate limits

### Rate Limiting

- **Free tiers** have rate limits
- Implement backoff strategies
- Distribute requests across time
- Monitor quota usage

### Legal & Ethical

- ✅ Only scan targets you have permission to test
- ✅ Respect rate limits and ToS
- ✅ Use responsibly for authorized security assessments
- ❌ Do not use for unauthorized access or data collection

---

## 📈 Performance Metrics

### Subfinder Performance

| Configuration | Subdomains Found | Time | Notes |
|---------------|------------------|------|-------|
| No API Keys | ~50,246 | Fast | Limited sources |
| With API Keys | ~165,063 | Slower | Comprehensive |

### Automation Benefits

- **Deduplication:** Focus on new findings only
- **Speed:** Immediate notification of new assets
- **Coverage:** Continuous monitoring vs. one-time scans
- **Efficiency:** Automated pipeline vs. manual steps

---

## 🎓 Lessons Learned

1. **API Keys Are Critical:** 2-3x more subdomains with API keys
2. **Automation Wins:** Continuous monitoring catches new assets first
3. **Deduplication Matters:** Focus on new findings, not duplicates
4. **Speed Counts:** Fast notification = competitive advantage
5. **Comprehensive Coverage:** Multiple sources = better results

---

## 📖 Source Reference

**Original Article:** [Recon with Me - Dhiyanesh Geek](https://dhiyaneshgeek.github.io/bug/bounty/2020/02/06/recon-with-me/)

**Published:** February 6, 2020

**Author:** Dhiyanesh Geek

**Key Contributions:**
- Comprehensive API key setup guide
- Automation workflow documentation
- Real-world bug bounty success story
- Tool integration examples

---

## 🔄 Integration with Our OSINT Tools

### Current Implementation Status

✅ **Implemented:**
- Subfinder (LangChain & CrewAI)
- Nuclei (LangChain & CrewAI)

⚠️ **Future Enhancements:**
- Httpx integration for alive domain checking
- Notify integration for Slack/Discord alerts
- Anew integration for deduplication
- Automated workflow orchestration

### Recommended Next Steps

1. **Implement Httpx Tool** - Check if domains are alive
2. **Implement Notify Tool** - Send alerts to Slack/Discord
3. **Implement Anew Logic** - Deduplication in Python
4. **Create Workflow Orchestrator** - Automated recon pipeline
5. **Add API Key Management** - Secure storage and configuration

---

*Last Updated: 2024*
*Based on: https://dhiyaneshgeek.github.io/bug/bounty/2020/02/06/recon-with-me/*

