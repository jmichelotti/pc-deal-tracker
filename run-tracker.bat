@echo off
cd /d "%~dp0"
set ANTHROPIC_API_KEY=
claude -p "Run a deal tracking session as described in CLAUDE.md" --allowedTools "mcp__playwright__*,WebSearch,WebFetch,Bash,Read,Edit,Write" >> tracker-log.txt 2>&1
