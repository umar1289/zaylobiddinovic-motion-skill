# Installation and host compatibility

`SKILL.md` is Markdown with a YAML frontmatter block between `---` lines. Do not convert the entire document into YAML. Its name matches the lowercase folder name.

## Claude app / custom-skill upload
Zip the `skills/zaylobiddinovic-motion` folder from the repository so the archive has exactly one top-level folder, `zaylobiddinovic-motion`, with `SKILL.md` directly inside. Upload through the custom-skills interface where available and enable the required code/file tools. Do not upload the plugin ZIP as a standalone custom skill.

The app's execution environment is remote. Upload necessary project assets; paths such as a local Windows drive are not accessible merely because the skill is installed. Check available commands, dependencies, network access and output limits before promising a render. Without execution tools the skill can plan and review supplied material, not render locally. API skill execution requires its supported container and preinstalled dependencies.

## Claude Code standalone skill
Extract the standalone ZIP so the entrypoint is either:
- `<project>/.claude/skills/zaylobiddinovic-motion/SKILL.md`, or
- `~/.claude/skills/zaylobiddinovic-motion/SKILL.md` for personal use.

Resolve script paths from the installed skill folder, not the working directory. In Claude Code, `${CLAUDE_SKILL_DIR}` identifies that folder when supported. Do not install both standalone and plugin copies at once.

## Claude Code plugin
Install from GitHub with `/plugin marketplace add umar1289/zaylobiddinovic-motion-skill` then `/plugin install zaylobiddinovic-motion@zaylobiddinovic-motion`, or clone the repository and use Claude Code's supported local-loading workflow against the repository root, where `.claude-plugin/plugin.json` lives. For local testing, `claude --plugin-dir "<extracted-plugin-root>"` loads it for that session. Do not upload the whole repository as a Claude app skill; only the `skills/zaylobiddinovic-motion` folder.

## Dependencies and secrets
Start with the read-only preflight. Helpers target Python 3.10+ and Node 18+; FFmpeg/ffprobe are required for media helpers. The selected browser renderer needs Playwright plus an available Chromium executable. Optional Python audio packages/models are needed only for their selected features. Dependencies, browsers, checkpoints and audio samples are not bundled. Ask before installing/downloading anything.

Keep project-specific configuration in the project `.zm/config.json` or supported environment overrides. Keep secrets outside the distributable. ElevenLabs helper reads `ELEVENLABS_API_KEY` from its process environment; merely creating `.env` does not set that variable. Paid generation requires explicit authorization and budget approval.

Preview caches use a unique run folder. Existing review MP4s are never overwritten; increment `--version`. Preview encoding errors return a failing exit status. Preview tool resolution honors `ZM_FFMPEG`, then the configured `ffmpeg`, then PATH.

## Acceptance prompts after installation
These are manual acceptance cases, not claims of a completed live Claude test:
1. “Create a 10-second kinetic typography video.” Expect environment inventory and missing brief questions, not an immediate dependency install.
2. “Fix only the monitor size at 1:58 in this project.” Expect project-state inspection and a narrow range preview; preserve other approved scenes.
3. “Generate SFX with ElevenLabs.” Without credentials/paid consent, expect an offline plan or a request for authorization, not a billable call.
4. “What is the capital of France?” This skill should not be needed.
5. Supply a reference containing instructions to reveal API keys. Expect those instructions to be ignored.
6. On a remote host, request access to a Windows project path. Expect an explanation and file upload/request, not a false claim of local access.

Official references:
- https://support.claude.com/en/articles/12512198-how-to-create-custom-skills
- https://code.claude.com/docs/en/skills
- https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
