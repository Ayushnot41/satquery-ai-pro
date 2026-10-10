# Project ownership and local tooling

This enhanced project belongs to the user, GitHub account **Ayushnot41**.
The original project is retained in the parent folder. Improvements belong in
this separate `satquery-ai-pro` repository.

## Skills and supporting tools

- Install or download task-specific skills only inside this project's `.tools/`
  directory. Keep Python packages in this project's `.venv/` and JavaScript
  dependencies in this project's `frontend/node_modules/`.
- Do not install skills globally, modify global skill configuration, or register
  project-specific tools for other projects.
- Existing read-only skill guidance may inform this work; its presence does not
  authorize modifying the user's global configuration.
- Retain upstream licenses for downloaded tooling. Record actual use accurately;
  a requested skill that is unavailable must not be described as installed or used.

## GitHub and hosting

- Create and push the new repository only under the verified **Ayushnot41**
  personal account. Do not use Sourav's GitHub account or organization.
- Do not deploy to Sourav's hosting account.
- Use free hosting plans. Do not activate paid resources or upgrades without
  separate user authorization. Explain free-tier limits in the deployment runbook.
- Preserve the original README and media. Put updated instructions and
  capability limitations in `PRO_README.md`.
