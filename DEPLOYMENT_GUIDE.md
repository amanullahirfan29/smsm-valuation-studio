# Publish SMSM Valuation Studio — GitHub + Streamlit Community Cloud

## Before you begin
You need free GitHub and Streamlit Community Cloud accounts. **No Python installation is required if you deploy in the browser.** The package is prepared with `app.py` and `requirements.txt` at the repository root. All 2026 market and forecast values remain dated reference inputs. Do not add account passwords, API tokens, or secrets to this repository.

## Upload this project to GitHub (browser-only)
1. Download `SMSM_Stage5B_Streamlit_Cloud_Ready.zip`, then extract it. Open the extracted folder named `SMSM_Valuation_Studio_Cloud_Ready`.
2. Sign into https://github.com and click the **+** icon > **New repository** (or use https://github.com/new). Name it `smsm-valuation-studio`; choose **Public** for a freely accessible presentation. Avoid uploading private data. Click **Create repository**.
3. In the empty repository, click **uploading an existing file**. Alternatively, choose **Add file > Upload files**. Drag the **CONTENTS inside** the extracted project folder into the browser upload area—not the ZIP and not the outer folder. Include the `valuation`, `data`, `tests` directories and top-level `app.py`, `requirements.txt`, `README.md` and other files. If your OS/browser does not preserve directory structure on upload, use **GitHub Desktop** or upload subfolders via the browser's file-picker where supported.
4. Scroll down, enter commit message `Initial SMSM valuation application`, and click **Commit changes**. At the repository's top level, confirm you can see `app.py`, `requirements.txt`, `valuation/`, and `data/`. Ensure `data/reference_inputs.json` and `data/SMSM_Stage_2B_Reconciled_Financial_Data.xlsx` are visible. Hidden folders `.github` and `.streamlit` are optional for first deployment but useful.
5. Open **Actions** and check **SMSM valuation checks** (if you uploaded the `.github` folder). Green means unit tests passed in GitHub's Python environment; red means read the error logs before continuing.

## Streamlit Community Cloud deployment
1. Go to https://share.streamlit.io and sign in using GitHub. Authorize access to the repository when prompted.
2. Click **Create app**, then **Yup, I have an app**.
3. Select `your-github-username/smsm-valuation-studio` (or paste the repo URL), branch `main`, main file path **`app.py`**.
4. Optional: choose an available custom subdomain such as `smsm-valuation-studio-itb`. Its availability is not guaranteed.
5. In **Advanced settings**, select **Python 3.12**. No secrets are needed. Click **Save**, then **Deploy**.
6. Watch build logs; once ready, the browser opens a real `.streamlit.app` address. **Copy the actual URL from your address bar**; never assume an address beforehand.
7. Run `LIVE_UAT_CHECKLIST.md` before sharing the URL with your lecturer.

## Make changes after deployment
Upload revised files to the SAME GitHub repository and commit the changes on the `main` branch. Streamlit Community Cloud redeploys automatically. Refresh the app when necessary. New session edits in the app are **not automatically saved to GitHub**: download **Save editable model inputs (.json)** and restore it via the Historical Financial Data page.

## Troubleshooting
- **ModuleNotFoundError: valuation**: check `valuation/__init__.py` and modules are included, and `app.py` is at repository root.
- **FileNotFoundError: reference_inputs.json**: check `data/reference_inputs.json` has been uploaded and file capitalization matches exactly.
- **Failed to install dependency**: verify `requirements.txt` exists alongside `app.py` and use Python 3.12. Use logs from the Streamlit Cloud management page.
- **Blank or error page**: use **Manage app > Logs**; verify dependency installation, then reboot from the app menu if needed.
- **Inputs reset after reload**: expected session behavior; download and re-import the saved JSON input snapshot.
- **Warning: provisional valuation / recommendation withheld**: an intentional financial control, not a deployment failure.
- **Private/unavailable app**: check your GitHub repo permissions, Streamlit GitHub authorization, and app sharing permissions.

Official docs: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
