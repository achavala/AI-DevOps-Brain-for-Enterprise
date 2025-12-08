# 🔐 AWS Setup Guide - Step by Step

## What Went Wrong

You tried to run multiple commands at once. The `aws configure` command is **interactive** and needs to be run separately, one step at a time.

---

## ✅ Correct Way to Setup AWS

### Step 1: Check if AWS CLI is Installed

```bash
aws --version
```

**Expected**: Should show AWS CLI version (e.g., `aws-cli/2.x.x`)

**If not installed**: Run `./scripts/install-prerequisites.sh` first

---

### Step 2: Configure AWS Credentials (Interactive)

Run this command **by itself**:

```bash
aws configure
```

You will be prompted **one at a time** for:

1. **AWS Access Key ID**: 
   - Get this from AWS Console → IAM → Users → Your User → Security Credentials
   - Or from your AWS administrator
   - Example: `AKIAIOSFODNN7EXAMPLE`

2. **AWS Secret Access Key**:
   - Get this when you create the access key
   - Example: `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`
   - ⚠️ **Keep this secret!**

3. **Default region name**:
   - Type: `us-east-1` (or your preferred region)
   - Examples: `us-east-1`, `us-west-2`, `eu-west-1`

4. **Default output format**:
   - Type: `json`
   - (This is the standard format)

**Example Session**:
```
$ aws configure
AWS Access Key ID [None]: AKIAIOSFODNN7EXAMPLE
AWS Secret Access Key [None]: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
Default region name [None]: us-east-1
Default output format [None]: json
```

---

### Step 3: Verify AWS Configuration

After configuring, verify it works:

```bash
aws sts get-caller-identity
```

**Expected Output**:
```json
{
    "UserId": "AIDA...",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/your-username"
}
```

**If this works**: ✅ Your AWS credentials are configured correctly!

**If this fails**: Check your credentials and try again.

---

### Step 4: Run AWS Setup Script

**Only after** `aws configure` is complete and verified:

```bash
./scripts/setup-aws.sh
```

This script will:
- Verify your credentials
- Create S3 bucket for Terraform state
- Enable versioning and encryption
- Show you the bucket name

---

## 🚨 Common Issues

### Issue 1: "AWS CLI not found"
**Solution**: Install it first
```bash
./scripts/install-prerequisites.sh
```

### Issue 2: "Invalid credentials"
**Solution**: 
- Double-check your Access Key ID and Secret Access Key
- Make sure there are no extra spaces
- Verify the keys are active in AWS Console

### Issue 3: "Access Denied"
**Solution**:
- Your IAM user needs permissions to create S3 buckets
- Contact your AWS administrator to add permissions

### Issue 4: "Region not found"
**Solution**:
- Use a valid AWS region name
- Common regions: `us-east-1`, `us-west-2`, `eu-west-1`

---

## 📋 Quick Checklist

- [ ] AWS CLI installed (`aws --version` works)
- [ ] AWS credentials obtained (Access Key ID + Secret)
- [ ] `aws configure` completed successfully
- [ ] `aws sts get-caller-identity` returns account info
- [ ] `./scripts/setup-aws.sh` runs without errors

---

## 🔄 If You Need to Start Over

If you made mistakes during `aws configure`, you can reconfigure:

```bash
aws configure
```

Or manually edit the credentials file:

```bash
# View current config
cat ~/.aws/credentials
cat ~/.aws/config

# Edit if needed
nano ~/.aws/credentials
nano ~/.aws/config
```

---

## ⚠️ Important Notes

1. **Never share your AWS credentials** - Keep them secret!
2. **Use IAM users with least privilege** - Don't use root account
3. **Rotate credentials regularly** - Security best practice
4. **Set up MFA** - Multi-factor authentication for extra security

---

## 🎯 Next Steps After AWS Setup

Once AWS is configured:

1. **Verify setup**:
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

**Remember**: `terraform plan` is safe - it doesn't create anything, just shows what would be created.

---

## 📞 Need Help?

If you're stuck:
1. Check that AWS CLI is installed: `aws --version`
2. Verify credentials: `aws sts get-caller-identity`
3. Review this guide step by step
4. Make sure you're running commands one at a time

---

**Follow these steps one at a time, and you'll be set up correctly!**

