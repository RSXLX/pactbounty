# PactBounty

**一句话：** CAW 驱动的 Agent-to-Agent 智能合约审计赏金市场。Client Agent 用 Cobo Agentic Wallet 创建并托管审计任务；Worker Agent 自动审计、修复、提交交付物；Evaluator Agent 验收后释放付款；越权资金操作会被 CAW Pact 拦截并留下 audit log。

> 推荐提交赛道：**Cobo 赛道｜Agentic Economy × Cobo Agentic Wallet**  
> 加分融合：GLM-5.1 驱动 Worker/Evaluator 的长程任务过程。

---

## 这个底座已经包含什么

```text
pactbounty/
  contracts/       Solidity 合约：MockUSDC、AgenticCommerce escrow、漏洞合约、修复合约
  backend/         FastAPI 后端：Client/Worker/Evaluator Agents、Mock CAW、Real CAW adapter、Z.AI adapter
  frontend/        Next.js Demo Dashboard：状态、余额、agent trace、CAW audit logs、证据面板
  docs/            架构、Demo 脚本、安全边界、真实 CAW/GLM 接入、后续开发计划
  evidence/        提交时放截图、tx hash、wallet 地址、视频素材
```

本地默认是 **Mock 模式**，不需要真实钱包或 API Key 就能跑完整闭环：

1. Client / Worker / Evaluator 三个 Agent 分别提交 scoped CAW Pact。
2. Client Agent 通过 CAW approve MockUSDC，并创建、设置预算、fund escrow job。
3. Worker Agent 审计 `VulnerableVault.sol`，生成修复版 `PatchedVault.sol`、审计报告和 deliverable hash。
4. Worker Agent 通过 CAW 调用 `submit()`。
5. Evaluator Agent 验证 patch invariant，生成 reason hash。
6. Evaluator Agent 通过 CAW 调用 `complete()`，释放 5 mUSDC 给 Worker。
7. Client Agent 尝试转出 20 mUSDC，超过 Pact 限额，被 CAW 拒绝并记录 audit log。

---

## 快速启动

### 1. 后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.scripts.run_demo
uvicorn app.main:app --reload --port 8000
```

API：`http://localhost:8000`

关键接口：

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/demo/run
curl http://localhost:8000/state
curl http://localhost:8000/audit-logs
```

### 2. 前端

```bash
cd frontend
npm install
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

打开：`http://localhost:3000`，点击 **Run Full Demo**。

### 3. 合约

```bash
cd contracts
forge install foundry-rs/forge-std --no-commit
forge build
forge test
```

部署测试网：

```bash
cp ../.env.example ../.env
# 填 RPC_URL、PRIVATE_KEY、CLIENT_AGENT_WALLET、WORKER_AGENT_WALLET
source ../.env
forge script script/Deploy.s.sol:Deploy --rpc-url $RPC_URL --broadcast
```

---

## 真实 CAW / GLM-5.1 接入点

### CAW

默认：

```bash
CAW_MODE=mock
```

切换真实 CAW：

```bash
CAW_MODE=real
AGENT_WALLET_API_URL=https://api.agenticwallet.cobo.com
AGENT_WALLET_API_KEY=...
AGENT_WALLET_WALLET_ID=...
```

需要重点改的文件只有一个：

```text
backend/app/services/caw/real_caw_client.py
```

这个 adapter 已经按 Cobo Python SDK 的 `WalletAPIClient` / `submit_pact` / `get_pact` / `transfer_tokens` / `list_audit_logs` 模式组织，`contract_call` 的参数需要按你实际安装的 SDK 版本微调。

### GLM-5.1 / Z.AI

默认：

```bash
LLM_MODE=mock
```

切换真实 GLM-5.1：

```bash
LLM_MODE=real
ZAI_API_KEY=...
ZAI_BASE_URL=https://api.z.ai/api/paas/v4/
ZAI_MODEL=glm-5.1
```

接入文件：

```text
backend/app/services/llm/zai_client.py
```

---

## 评委视角的亮点

| 评分点 | 项目如何命中 |
|---|---|
| Agentic Commerce | Agent 发包、托管、交付、验收、收款，形成经济闭环。 |
| CAW 关键性 | 每个资金相关动作都经过 CAW Pact；越权动作会被拒绝。 |
| 资金流程完整度 | approve → createJob → setBudget → fund → submit → complete → payment released。 |
| 可演示性 | 本地 Mock 稳定跑通；测试网接入路径明确。 |
| 安全边界 | 单笔限额、合约白名单、函数白名单、有效期、测试资产、人工审批边界。 |
| Long-Horizon Task | Worker 展示计划、审计、修复、验证、提交；Evaluator 展示结构化验收。 |

---

## 交付前必须替换的证据

提交前把 `evidence/` 补齐：

```text
evidence/
  txs.json                     测试网 tx hash
  wallet-addresses.md          Client / Worker / Evaluator Agent Wallet 地址
  screenshots/
    caw-pact-approved.png
    caw-denial.png
    dashboard-final.png
    explorer-job-funded.png
```

README 里也要补：

- 测试网名称
- MockUSDC 地址
- AgenticCommerce 地址
- Job ID
- Client Agent Wallet
- Worker Agent Wallet
- Evaluator Agent Wallet
- `approve/createJob/fund/submit/complete/denial` 对应证据

---

## 后续计划

完整计划见：[`docs/DEVELOPMENT_PLAN.md`](docs/DEVELOPMENT_PLAN.md)。

最关键的开发顺序：

1. 先用 Mock 模式录一版完整 Demo，确保故事线没有断点。
2. 部署合约到 Sepolia/Base Sepolia。
3. 接真实 CAW：先跑官方 hello world，再接 `contract_call`。
4. 接真实 GLM-5.1：让 Worker/Evaluator 真实输出 trace。
5. 录 3–5 分钟 Demo 视频，不要展示太多代码，重点展示资金闭环和 CAW denial。
