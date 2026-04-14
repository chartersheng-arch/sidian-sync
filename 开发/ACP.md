github：[https://github.com/xiwan/acp-bridge](https://github.com/xiwan/acp-bridge)
**在 Windows 上跑 acp-bridge**（Linux 子系统装 uv 比较麻烦）：

**第一步：Windows 上安装 uv**

Copy

```
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**第二步：在 Windows 上 clone 并配置 acp-bridge**

Copy

```
git clone https://github.com/xiwan/acp-bridge.git
cd acp-bridge
uv sync
```

**第三步：配置 token 并启动**

Copy

```
$env:ACP_BRIDGE_TOKEN="acpbridges"
$env:OPENCLAW_TOKEN="dBjHqPyX6fEoOyY8iJuV6hItV7jLxZCp"
uv run main.py --ui
```



E:/AIopen/acp-bridge
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 
ACP_BRIDGE_TOKEN="acpbridges"
OPENCLAW_TOKEN="dBjHqPyX6fEoOyY8iJuV6hItV7jLxZCp“