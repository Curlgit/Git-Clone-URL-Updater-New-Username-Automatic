
#!/usr/bin/env python3
# Git Clone Fix
# Developed by Curlgit

import sys
import os
import re
import json
import base64
import shutil
import subprocess
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from datetime import datetime
from getpass import getpass

# ---------- YELLOW INTERFACE ----------

YELLOW = "\033[93m"
RESET = "\033[0m"

def say(text=""):
    print(f"{YELLOW}{text}{RESET}")

def title(text):
    say("\n𝗚𝗜𝗧 𝗖𝗟𝗢𝗡𝗘 𝗙𝗜𝗫")
    say(f"𝗖𝘂𝗿𝗹𝗴𝗶𝘁 | {text}\n")

# ---------- STORAGE ----------

APP_DIR = Path.home() / ".git_clone_fix"
TOKEN_FILE = APP_DIR / "token.json"
HISTORY_FILE = APP_DIR / "history.json"

SHARED_DIR = (
    Path.home() / "storage" / "shared" /
    "Download" / "GitCloneFix"
)

def ensure_files():
    APP_DIR.mkdir(parents=True, exist_ok=True)

    if not TOKEN_FILE.exists():
        TOKEN_FILE.write_text("{}", encoding="utf-8")

    if not HISTORY_FILE.exists():
        HISTORY_FILE.write_text("[]", encoding="utf-8")

    try:
        TOKEN_FILE.chmod(0o600)
    except OSError:
        pass

def request_storage_permission():
    say("𝗦𝗧𝗢𝗥𝗔𝗚𝗘 𝗣𝗘𝗥𝗠𝗜𝗦𝗦𝗜𝗢𝗡")

    if SHARED_DIR.exists() and os.access(SHARED_DIR, os.W_OK):
        say("Shared storage is available.")
        return True

    command = shutil.which("termux-setup-storage")

    if not command:
        say("Storage setup command unavailable.")
        say("Using private storage instead.")
        return False

    try:
        say("Requesting Android storage permission...")
        subprocess.run([command], check=False, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        say(f"Storage permission unavailable: {exc}")

    if SHARED_DIR.exists() and os.access(SHARED_DIR, os.W_OK):
        say("Shared storage permission available.")
        return True

    say("Permission denied or unavailable.")
    say("Continuing with private storage.")
    return False

# ---------- API REQUESTS ----------

def request_json(url, token, platform, method="GET", data=None):
    headers = {
        "Accept": "application/json",
        "User-Agent": "Git-Clone-Fix-Curlgit/1.0",
    }

    if platform == "gitlab":
        headers["PRIVATE-TOKEN"] = token
    elif platform == "github":
        headers["Authorization"] = f"Bearer {token}"
        headers["X-GitHub-Api-Version"] = "2022-11-28"
    else:
        headers["Authorization"] = f"token {token}"

    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(
        url, data=body, headers=headers, method=method
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read()
            return json.loads(raw.decode("utf-8")) if raw else None
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail[:300]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error: {exc.reason}") from exc

def platform_settings(platform, custom_url=""):
    if platform == "github":
        return "https://api.github.com", "github"
    if platform == "codeberg":
        return "https://codeberg.org/api/v1", "gitea"
    if platform == "gitlab":
        return "https://gitlab.com/api/v4", "gitlab"
    if platform == "gitea":
        base = custom_url.strip().rstrip("/")
        if not base.startswith(("https://", "http://")):
            raise ValueError("Enter a valid Gitea URL.")
        if not base.endswith("/api/v1"):
            base += "/api/v1"
        return base, "gitea"
    raise ValueError("Unsupported platform.")

def api_call(account, endpoint, method="GET", data=None):
    url = account["api_base"].rstrip("/") + endpoint
    return request_json(
        url, account["token"], account["platform"], method, data
    )

# ---------- TOKEN MANAGEMENT ----------

def load_account():
    try:
        data = json.loads(TOKEN_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict) and data.get("token"):
            return data
    except (OSError, json.JSONDecodeError):
        pass
    return None

def save_account(account):
    TOKEN_FILE.write_text(
        json.dumps(account, indent=2),
        encoding="utf-8"
    )
    try:
        TOKEN_FILE.chmod(0o600)
    except OSError:
        pass

def import_api_token():
    title("INPUT API ACCESS TOKEN")

    say("[1] GitHub")
    say("[2] Codeberg")
    say("[3] Gitea")
    say("[4] GitLab")

    choice = input(f"{YELLOW}Select platform: {RESET}").strip()

    platforms = {
        "1": "github",
        "2": "codeberg",
        "3": "gitea",
        "4": "gitlab",
    }

    platform = platforms.get(choice)
    if not platform:
        say("Invalid platform.")
        return

    custom_url = ""
    if platform == "gitea":
        custom_url = input(
            f"{YELLOW}Gitea server URL: {RESET}"
        ).strip()

    try:
        api_base, platform_key = platform_settings(platform, custom_url)
    except ValueError as exc:
        say(str(exc))
        return

    token = getpass("API access token: ").strip()
    if not token:
        say("Token cannot be empty.")
        return

    temporary = {
        "platform": platform_key,
        "api_base": api_base,
        "token": token,
    }

    say("Validating token...")

    try:
        user = api_call(temporary, "/user")
        username = user.get("username") or user.get("login")

        if not username:
            say("Could not identify account.")
            return

        temporary.update({
            "username": username,
            "platform_name": platform,
        })

        save_account(temporary)
        say(f"Token verified. Account: {username}")
        say(f"Saved privately: {TOKEN_FILE}")

    except Exception as exc:
        say(f"Token validation failed: {exc}")

# ---------- REPOSITORY LIST ----------

def list_repositories(account):
    repos = []
    page = 1

    while page <= 100:
        platform = account["platform"]

        if platform == "github":
            endpoint = (
                f"/user/repos?per_page=100&page={page}"
                "&sort=updated&affiliation=owner,collaborator,"
                "organization_member"
            )
            page_size = 100
        elif platform == "gitlab":
            endpoint = (
                f"/projects?membership=true&per_page=100"
                f"&page={page}&order_by=last_activity_at"
            )
            page_size = 100
        else:
            endpoint = f"/user/repos?limit=50&page={page}"
            page_size = 50

        result = api_call(account, endpoint)

        if not isinstance(result, list) or not result:
            break

        for item in result:
            if platform == "gitlab":
                full_name = item.get("path_with_namespace", "")
                repo = {
                    "id": item.get("id"),
                    "full_name": full_name,
                    "name": item.get("name", full_name),
                    "default_branch": item.get("default_branch") or "main",
                    "private": item.get("visibility") == "private",
                }
            else:
                full_name = item.get("full_name", "")
                repo = {
                    "id": item.get("id"),
                    "full_name": full_name,
                    "name": item.get("name", full_name),
                    "default_branch": item.get("default_branch") or "main",
                    "private": item.get("private", False),
                }

            if full_name:
                repos.append(repo)

        if len(result) < page_size:
            break
        page += 1

    return repos

def select_repositories(repos):
    if not repos:
        say("No repositories found.")
        return []

    say("\n𝗔𝗩𝗔𝗜𝗟𝗔𝗕𝗟𝗘 𝗥𝗘𝗣𝗢𝗦𝗜𝗧𝗢𝗥𝗜𝗘𝗦")

    for index, repo in enumerate(repos, 1):
        visibility = "Private" if repo["private"] else "Public"
        say(f"[{index}] {repo['full_name']} ({visibility})")

    all_number = len(repos) + 1
    say(f"[{all_number}] ALL REPOSITORIES")

    raw = input(
        f"{YELLOW}Select numbers separated by commas: {RESET}"
    ).strip()

    if not raw:
        return []

    try:
        choices = {int(x.strip()) for x in raw.split(",") if x.strip()}
    except ValueError:
        say("Invalid selection.")
        return []

    if all_number in choices:
        return repos

    if any(x < 1 or x > len(repos) for x in choices):
        say("Selection out of range.")
        return []

    return [repos[x - 1] for x in sorted(choices)]

# ---------- README ACCESS ----------

def repo_parts(repo):
    return repo["full_name"].split("/", 1)

def readme_path_and_content(account, repo):
    platform = account["platform"]
    branch = repo.get("default_branch") or "main"

    if platform == "gitlab":
        project = urllib.parse.quote(repo["full_name"], safe="")
        tree = api_call(
            account,
            f"/projects/{project}/repository/tree"
            f"?ref={urllib.parse.quote(branch)}&per_page=100",
        )

        if not isinstance(tree, list):
            return None

        item = next(
            (x for x in tree
             if x.get("type") == "blob"
             and x.get("name", "").lower() == "readme.md"),
            None,
        )
        if not item:
            return None

        path = item["path"]
        encoded_path = urllib.parse.quote(path, safe="")
        data = api_call(
            account,
            f"/projects/{project}/repository/files/{encoded_path}"
            f"?ref={urllib.parse.quote(branch)}",
        )
        content = base64.b64decode(data["content"]).decode(
            "utf-8", errors="replace"
        )
        return path, content, data.get("last_commit_id"), branch

    owner, name = repo_parts(repo)
    owner = urllib.parse.quote(owner, safe="")
    name = urllib.parse.quote(name, safe="")

    listing = api_call(
        account,
        f"/repos/{owner}/{name}/contents?ref="
        f"{urllib.parse.quote(branch)}",
    )

    if not isinstance(listing, list):
        return None

    item = next(
        (x for x in listing
         if x.get("type") == "file"
         and x.get("name", "").lower() == "readme.md"),
        None,
    )
    if not item:
        return None

    path = item["path"]
    encoded_path = urllib.parse.quote(path, safe="/")
    data = api_call(
        account,
        f"/repos/{owner}/{name}/contents/{encoded_path}"
        f"?ref={urllib.parse.quote(branch)}",
    )

    content = base64.b64decode(data["content"]).decode(
        "utf-8", errors="replace"
    )
    return path, content, data.get("sha"), branch

# ---------- CLONE URL REPLACEMENT ----------

def replace_clone_urls(content, old_username, new_username):
    old = re.escape(old_username)

    # Match HTTPS clone URLs and SSH-style Git URLs.
    pattern = re.compile(
        r"((?:https?://|git@)[^/\s:]+(?::\d+)?[/:])"
        + old + r"(?=/)",
        re.IGNORECASE,
    )

    return pattern.sub(
        lambda match: match.group(1) + new_username,
        content,
    )

def write_readme(account, repo, path, content, sha, branch):
    message = "Update clone URLs via Git Clone Fix"

    if account["platform"] == "gitlab":
        project = urllib.parse.quote(repo["full_name"], safe="")
        file_path = urllib.parse.quote(path, safe="")
        endpoint = f"/projects/{project}/repository/files/{file_path}"

        api_call(
            account,
            endpoint,
            method="PUT",
            data={
                "branch": branch,
                "content": content,
                "commit_message": message,
            },
        )
        return

    owner, name = repo_parts(repo)
    owner = urllib.parse.quote(owner, safe="")
    name = urllib.parse.quote(name, safe="")

    endpoint = (
        f"/repos/{owner}/{name}/contents/"
        f"{urllib.parse.quote(path, safe='/')}"
    )

    payload = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        "branch": branch,
    }

    if sha:
        payload["sha"] = sha

    api_call(account, endpoint, method="PUT", data=payload)

# ---------- HISTORY ----------

def add_history(entry):
    try:
        history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        if not isinstance(history, list):
            history = []
    except (OSError, json.JSONDecodeError):
        history = []

    history.append(entry)
    HISTORY_FILE.write_text(
        json.dumps(history, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

# ---------- UPDATE WORKFLOW ----------

def change_repository_username():
    account = load_account()

    if not account:
        say("Import a valid API token first.")
        return

    title("CHANGE REPOSITORY USERNAME")

    try:
        repos = list_repositories(account)
    except Exception as exc:
        say(f"Could not fetch repositories: {exc}")
        return

    selected = select_repositories(repos)
    if not selected:
        say("No repositories selected.")
        return

    old_username = input(
        f"{YELLOW}Old username in clone URLs: {RESET}"
    ).strip()

    new_username = input(
        f"{YELLOW}New username: {RESET}"
    ).strip()

    if not old_username or not new_username:
        say("Usernames cannot be empty.")
        return

    if old_username == new_username:
        say("Old and new usernames are identical.")
        return

    # No YES confirmation. Updates start immediately.
    say("\n𝗨𝗣𝗗𝗔𝗧𝗜𝗡𝗚 𝗥𝗘𝗣𝗢𝗦𝗜𝗧𝗢𝗥𝗜𝗘𝗦...")
    say(f"{old_username} -> {new_username}")

    for repo in selected:
        name = repo["full_name"]
        say(f"\nProcessing: {name}")

        try:
            result = readme_path_and_content(account, repo)

            if not result:
                say("README.md not found. Skipping.")
                continue

            path, content, sha, branch = result
            updated = replace_clone_urls(
                content, old_username, new_username
            )

            if updated == content:
                say("No matching clone URLs. Skipping.")
                continue

            write_readme(
                account, repo, path, updated, sha, branch
            )

            say("README.md updated successfully.")

            add_history({
                "time": datetime.now().isoformat(timespec="seconds"),
                "repository": name,
                "file": path,
                "old_username": old_username,
                "new_username": new_username,
                "status": "success",
            })

        except Exception as exc:
            say(f"Failed: {exc}")
            try:
                add_history({
                    "time": datetime.now().isoformat(timespec="seconds"),
                    "repository": name,
                    "old_username": old_username,
                    "new_username": new_username,
                    "status": "failed",
                    "error": str(exc),
                })
            except OSError:
                say("Could not write history file.")

    say("\n𝗣𝗥𝗢𝗖𝗘𝗦𝗦 𝗖𝗢𝗠𝗣𝗟𝗘𝗧𝗘")

# ---------- MAIN MENU ----------

def main():
    ensure_files()

    say(f"Token file: {TOKEN_FILE}")
    say(f"History file: {HISTORY_FILE}")

    request_storage_permission()

    while True:
        title("MAIN MENU")
        say("[1] INPUT ACCESS TOKEN")
        say("[2] GIT CLONE CHANGE  URL FOR NEW USERNAME")
        say("[3] EXIT")

        choice = input(f"{YELLOW}Select option: {RESET}").strip()

        if choice == "1":
            import_api_token()
            input(f"{YELLOW}Press Enter to continue...{RESET}")

        elif choice == "2":
            change_repository_username()
            input(f"{YELLOW}Press Enter to continue...{RESET}")

        elif choice == "3":
            say("Git Clone Fix closed.")
            break

        else:
            say("Invalid option.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        say("\nCancelled by user.")
    except Exception as exc:
        say(f"\nUnexpected error: {exc}")
