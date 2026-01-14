# n8n Credential Types Reference

This document lists common credential types used in n8n workflows with their required fields and usage examples.

## Using Credentials

### Always Use Credential IDs

When creating workflows, **always reference credentials by ID** rather than name:

```json
// CORRECT - Use credential ID
"credentials": {
  "githubApi": {
    "id": "cred_abc123",
    "name": "My GitHub Token"
  }
}

// INCORRECT - Name only (unreliable)
"credentials": {
  "githubApi": {
    "name": "My GitHub Token"
  }
}
```

### Discovering Credential IDs

Use the `list_credentials` tool to find existing credential IDs:

```python
result = await list_credentials()
# Returns: {"data": [{"id": "cred_123", "name": "GitHub API", "type": "githubApi"}, ...]}
```

---

## Common Credential Types

### API Key Based

#### `httpHeaderAuth`
HTTP Header Authentication - Generic API key in header.

```json
{
  "name": "My API Key",
  "type": "httpHeaderAuth",
  "data": {
    "name": "X-API-Key",
    "value": "your-api-key-here"
  }
}
```

#### `httpQueryAuth`
Query Parameter Authentication - API key as URL parameter.

```json
{
  "name": "Query API Key",
  "type": "httpQueryAuth",
  "data": {
    "name": "api_key",
    "value": "your-api-key-here"
  }
}
```

---

### OAuth2

#### `oAuth2Api`
Generic OAuth2 credentials.

```json
{
  "name": "OAuth2 App",
  "type": "oAuth2Api",
  "data": {
    "clientId": "your-client-id",
    "clientSecret": "your-client-secret",
    "accessTokenUrl": "https://api.example.com/oauth/token",
    "authUrl": "https://api.example.com/oauth/authorize",
    "scope": "read write"
  }
}
```

---

### Basic Authentication

#### `httpBasicAuth`
HTTP Basic Authentication (username/password).

```json
{
  "name": "Basic Auth",
  "type": "httpBasicAuth",
  "data": {
    "user": "username",
    "password": "password"
  }
}
```

#### `httpDigestAuth`
HTTP Digest Authentication.

```json
{
  "name": "Digest Auth",
  "type": "httpDigestAuth",
  "data": {
    "user": "username",
    "password": "password"
  }
}
```

---

### SSH & Server Access

#### `sshPassword`
SSH with password authentication.

```json
{
  "name": "SSH Password",
  "type": "sshPassword",
  "data": {
    "host": "server.example.com",
    "port": 22,
    "username": "user",
    "password": "password"
  }
}
```

#### `sshPrivateKey`
SSH with private key authentication.

```json
{
  "name": "SSH Key",
  "type": "sshPrivateKey",
  "data": {
    "host": "server.example.com",
    "port": 22,
    "username": "user",
    "privateKey": "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----",
    "passphrase": "optional-passphrase"
  }
}
```

---

### Popular Services

#### `githubApi`
GitHub Personal Access Token or OAuth App.

```json
{
  "name": "GitHub",
  "type": "githubApi",
  "data": {
    "accessToken": "ghp_xxxxxxxxxxxx"
  }
}
```

#### `slackApi`
Slack Bot Token.

```json
{
  "name": "Slack Bot",
  "type": "slackApi",
  "data": {
    "accessToken": "xoxb-xxxxxxxxxxxx"
  }
}
```

#### `slackOAuth2Api`
Slack OAuth2 credentials.

```json
{
  "name": "Slack OAuth",
  "type": "slackOAuth2Api",
  "data": {
    "clientId": "your-client-id",
    "clientSecret": "your-client-secret"
  }
}
```

#### `discordApi`
Discord Bot Token.

```json
{
  "name": "Discord Bot",
  "type": "discordApi",
  "data": {
    "botToken": "your-bot-token"
  }
}
```

#### `telegramApi`
Telegram Bot Token.

```json
{
  "name": "Telegram Bot",
  "type": "telegramApi",
  "data": {
    "accessToken": "your-bot-token"
  }
}
```

---

### Email Services

#### `smtpImap`
SMTP/IMAP email server credentials.

```json
{
  "name": "Email Server",
  "type": "smtpImap",
  "data": {
    "user": "user@example.com",
    "password": "password",
    "host": "smtp.example.com",
    "port": 587,
    "secure": true
  }
}
```

#### `gmailOAuth2`
Gmail OAuth2 credentials.

```json
{
  "name": "Gmail",
  "type": "gmailOAuth2",
  "data": {
    "clientId": "your-client-id",
    "clientSecret": "your-client-secret"
  }
}
```

---

### Cloud Providers

#### `awsApi`
AWS Access Key credentials.

```json
{
  "name": "AWS",
  "type": "awsApi",
  "data": {
    "accessKeyId": "AKIAIOSFODNN7EXAMPLE",
    "secretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
    "region": "us-east-1"
  }
}
```

#### `googleApi`
Google Service Account credentials.

```json
{
  "name": "Google Service Account",
  "type": "googleApi",
  "data": {
    "email": "service-account@project.iam.gserviceaccount.com",
    "privateKey": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----"
  }
}
```

#### `azureApi`
Azure credentials.

```json
{
  "name": "Azure",
  "type": "azureApi",
  "data": {
    "clientId": "your-client-id",
    "clientSecret": "your-client-secret",
    "tenantId": "your-tenant-id"
  }
}
```

---

### Databases

#### `postgresApi`
PostgreSQL database credentials.

```json
{
  "name": "PostgreSQL",
  "type": "postgresApi",
  "data": {
    "host": "localhost",
    "port": 5432,
    "database": "mydb",
    "user": "postgres",
    "password": "password",
    "ssl": false
  }
}
```

#### `mysqlApi`
MySQL database credentials.

```json
{
  "name": "MySQL",
  "type": "mysqlApi",
  "data": {
    "host": "localhost",
    "port": 3306,
    "database": "mydb",
    "user": "root",
    "password": "password"
  }
}
```

#### `mongoDbApi`
MongoDB credentials.

```json
{
  "name": "MongoDB",
  "type": "mongoDbApi",
  "data": {
    "connectionString": "mongodb://user:pass@localhost:27017/mydb"
  }
}
```

#### `redisApi`
Redis credentials.

```json
{
  "name": "Redis",
  "type": "redisApi",
  "data": {
    "host": "localhost",
    "port": 6379,
    "password": "optional-password"
  }
}
```

---

### Webhooks & APIs

#### `webhookAuth`
Webhook authentication credentials.

```json
{
  "name": "Webhook Auth",
  "type": "webhookAuth",
  "data": {
    "httpMethod": "headerAuth",
    "headerName": "X-Webhook-Secret",
    "headerValue": "your-secret"
  }
}
```

---

## Getting Schema for a Credential Type

Use `get_credential_schema` to discover the exact fields required for any credential type:

```python
schema = await get_credential_schema("githubApi")
# Returns the JSON schema defining required and optional fields
```

This is useful when working with credential types not listed in this document.

---

## Security Notes

1. **Never store credentials in workflow definitions** - Use credential references instead
2. **Use environment variables** for sensitive data in n8n configuration
3. **Credential data is redacted** in API responses (only id, name, type returned)
4. **Rotate credentials regularly** - Update through the n8n UI or `update_credential` tool
5. **Use least-privilege tokens** - Only grant permissions the workflow needs
