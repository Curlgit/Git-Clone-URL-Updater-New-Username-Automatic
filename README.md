Git Clone URL Updater — New Username Automatic

Developed by Curlgit

Git Clone Fix is a Python-based Termux utility designed to update clone URLs in repository README files using supported Git hosting APIs.

Features

- Supports GitHub, GitLab, Gitea, and Codeberg.
- API token validation.
- Automatic username detection from the selected platform.
- Repository selection, including all available repositories.
- Batch processing of selected repositories.
- Token and history storage in Termux private storage.
- Continues working without shared-storage permission.

Requirements

- Android with Termux
- Python
- Git
- API access token for a supported Git hosting platform

Installation

1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/git-clone-fix.git
```
2. Open the project directory
```bash
cd git-clone-fix
```
3. Run the installer
```bash
bash install.sh
```
4. Start the tool
```bash
python git clone update.py
```
Termux Private Storage

Git Clone Fix stores its token and history files in Termux's private home directory instead of requiring shared storage.

Private storage location:
```bash
/data/data/com.termux/files/home/
```
The application data directory is:
```bash
~/.git_clone_fix/
```
Access private storage

Open your Termux home directory:
```bash
cd ~
```
View hidden files and folders:
```bash
ls -la
```
Open the application's data directory:
```bash
cd ~/.git_clone_fix
```
View its contents:
```bash
ls -la
```
Check the token file:
```bash
cat ~/.git_clone_fix/token.json
```
Check the history file:
```bash
cat ~/.git_clone_fix/history.json
```
Security note: These files may contain sensitive information. Never share your API token or upload token files to a public repository.

If shared-storage access is denied, the tool can continue using its private storage. Files in Termux private storage are separate from your phone's shared "Download" folder.

Usage

1. Launch Git Clone Fix.
2. Select INPUT API ACCESS TOKEN.
3. Choose your Git hosting platform.
4. Enter your API token.
5. Select the repositories you want to process.
6. Choose the all-repositories option if needed.
7. Enter the old username.
8. Enter the new username.
9. The update process starts automatically after you submit the new username.

Review the results and verify the updated README files on the hosting platform.

Supported Platforms

- GitHub
- GitLab
- Gitea
- Codeberg

API permissions depend on the selected platform and repository. Use a token with only the permissions needed to read and update the intended files.

Security

- Keep your API token private.
- Never commit "token.json" to Git.
- Use a limited-permission token whenever possible.
- Revoke the token if it is exposed.
- Review repository changes after running batch updates.

**Disclaimer
This tool is intended for educational and personal use. Use it only with repositories you own or are authorized to modify. The developer is not responsible for damage or unintended changes caused by its use**