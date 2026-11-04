# Security

## Reporting a problem

Please don't report security problems in a public issue. Instead, use GitHub's private reporting: open the **Security** tab of this repository and click **Report a vulnerability**.

Include what you found, how to reproduce it, and which part of the kit it affects (the Lovable kit, the GitHub layer or the skill). You'll get a reply within a week.

## What the kit can touch

- **Lovable Lite** writes version rows to a table in your app's database. That table can be read by anyone with your app's public key, so don't use Lite for private work.
- **The GitHub layer** (Lovable Pro, Bolt, v0) runs GitHub Actions in your repository with permission to push commits and tags.
- **The skill** runs a Python script on your computer that reads and writes files in your project folder.

Read any file before you add it to your project, as you would with any code you copy from the internet.
