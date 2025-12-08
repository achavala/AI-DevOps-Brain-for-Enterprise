# 🔧 Fix AWS Credentials - Quick Fix Guide

## ❌ What Went Wrong

When you ran `aws configure`, you accidentally pasted multiple commands into the prompts. Your credentials file now has:

```
aws_access_key_id =    cd infrastructure
aws_secret_access_key =    terraform init
```

These are **commands, not AWS credentials** - that's why it's not working!

---

## ✅ How to Fix It

### Option 1: Reconfigure AWS (Recommended)

Run `aws configure` again, but this time **type or paste your actual AWS credentials**:

```bash
aws configure
```

When prompted, enter:

1. **AWS Access Key ID**: Your actual access key (starts with `AKIA...`)
2. **AWS Secret Access Key**: Your actual secret key
3. **Default region**: `us-east-1` (or your preferred region)
4. **Default output format**: `json`

**Important**: 
- Run `aws configure` **by itself** (don't paste other commands)
- Enter **one value at a time** when prompted
- Use your **real AWS credentials** (not commands)

---

### Option 2: Edit the File Directly

If you prefer to edit the file manually:

```bash
nano ~/.aws/credentials
```

Replace the content with:

```ini
[default]
aws_access_key_id = YOUR_ACTUAL_ACCESS_KEY_ID
aws_secret_access_key = YOUR_ACTUAL_SECRET_ACCESS_KEY
```

Then edit the config file:

```bash
nano ~/.aws/config
```

Make sure it has:

```ini
[default]
region = us-east-1
output = json
```

---

## 🔑 Where to Get AWS Credentials

If you don't have AWS credentials yet:

1. **Go to AWS Console**: https://console.aws.amazon.com
2. **Navigate to IAM**: 
   - Click on your username (top right)
   - Go to "Security credentials"
3. **Create Access Key**:
   - Scroll to "Access keys"
   - Click "Create access key"
   - Choose "Command Line Interface (CLI)"
   - Download or copy the keys
4. **Save them securely** - you'll need them for `aws configure`

**⚠️ Important**: 
- Keep your secret key **secret** - never share it
- If you lose it, you'll need to create a new one
- The secret key is only shown once when created

---

## ✅ Verify It's Fixed

After fixing, test your credentials:

```bash
aws sts get-caller-identity
```

**Expected Output** (if working):
```json
{
    "UserId": "AIDA...",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/your-username"
}
```

**If you see this**: ✅ Your credentials are working!

**If you see an error**: Check that you entered the correct credentials.

---

## 🚀 Next Steps

Once your credentials are fixed:

1. **Verify**:
   ```bash
   aws sts get-caller-identity
   ```

2. **Run setup script**:
   ```bash
   ./scripts/setup-aws.sh
   ```

3. **Continue with Terraform**:
   ```bash
   cd infrastructure
   terraform init
   terraform validate
   terraform plan
   ```

---

## 📋 Quick Checklist

- [ ] Have AWS Access Key ID ready
- [ ] Have AWS Secret Access Key ready
- [ ] Run `aws configure` (one command at a time)
- [ ] Enter credentials when prompted (not commands)
- [ ] Verify with `aws sts get-caller-identity`
- [ ] Run `./scripts/setup-aws.sh`

---

## 💡 Pro Tip

**Don't paste multiple commands at once!**

When running interactive commands like `aws configure`:
- ✅ Run the command **by itself**
- ✅ Wait for each prompt
- ✅ Enter **one value at a time**
- ✅ Press Enter after each value

---

**Fix your credentials now, and you'll be ready to continue!**

