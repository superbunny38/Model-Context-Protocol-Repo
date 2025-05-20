# Model-Context-Protocol-Repo

## Cheatsheet

- uv init
- uv venv
- source .venv/bin/activate
- uv add mcp [needed library 1] [needed library 2] ...

Launch inspector:
- npx @modelcontextprotocol/inspector uv run server.py

### How-to solve

- Problem:
Starting MCP inspector...
⚙️ Proxy server listening on port 6277
❌  MCP Inspector PORT IS IN USE at http://127.0.0.1:6274 ❌


- Solution:
(YourMCPCodingMaster) (base) chaeeunryu@Chaeeuns-Air YourMCPCodingMaster % sudo lsof -i :6274                                  
COMMAND   PID       USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
node    69213 chaeeunryu   14u  IPv6 0x896fb59f5da90123      0t0  TCP *:6274 (LISTEN)
(YourMCPCodingMaster) (base) chaeeunryu@Chaeeuns-Air YourMCPCodingMaster % kill -9 69213
(YourMCPCodingMaster) (base) chaeeunryu@Chaeeuns-Air YourMCPCodingMaster % sudo lsof -i :6274
(YourMCPCodingMaster) (base) chaeeunryu@Chaeeuns-Air YourMCPCodingMaster % npx @modelcontextprotocol/inspector uv run server.py

Questions
- Q. 하나의 서버 당 하나의 tool인건가?
- Q. SSE 구현도 해봐야할듯
- Q. 서버 소통할 때 await/async 실제로도 쓰이나?
