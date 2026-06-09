# PactBounty 后续开发计划

目标：把当前底座从“本地稳定演示”推进到“黑客松可提交、可复现、有链上证据、有 CAW 关键性”的项目。

## 阶段 0：当前底座验收

完成标准：

- `python -m app.scripts.run_demo` 能跑完。
- Dashboard 点击 **Run Full Demo** 能看到：
  - 3 个 Pact
  - Job `Completed`
  - Worker 收到 5 mUSDC
  - CAW denial log
  - deliverable hash / reason hash

不做：

- 不急着美化 UI。
- 不急着做复杂 reputation / marketplace。
- 不急着接交易策略或真实资产。

## 阶段 1：合约部署和链上证据

任务：

1. 选择测试网：优先 Sepolia 或 Base Sepolia。
2. 部署：
   - `MockUSDC`
   - `AgenticCommerce`
   - `VulnerableVault`
   - `PatchedVault`
3. Mint MockUSDC 给 Client Agent Wallet。
4. 用普通脚本先跑通：
   - approve
   - createJob
   - setBudget
   - fund
   - submit
   - complete
5. 记录：
   - 合约地址
   - Job ID
   - tx hash
   - explorer 链接

完成标准：

- 不依赖 CAW，也能确认合约闭环正确。
- `AgenticCommerce.getJob(jobId)` 返回 `Completed`。
- Worker wallet token balance 增加。

## 阶段 2：真实 CAW 接入

任务：

1. 跑通 Cobo 官方 quickstart：
   - install CLI
   - onboard
   - pair wallet
   - get API key
   - submit pact
   - allowed action
   - denied action
   - audit logs
2. 把 `CAW_MODE=real` 打开。
3. 修改 `backend/app/services/caw/real_caw_client.py` 的 `contract_call` 参数，使其匹配你安装的 SDK 版本。
4. 先只接 `MockUSDC.approve`。
5. 再接 `createJob / setBudget / fund`。
6. 最后接 `submit / complete`。

完成标准：

- 至少一个真实 CAW pact approval。
- 至少一个真实 CAW contract call。
- 至少一个真实 CAW policy denial。
- 后端 `/audit-logs` 能返回真实 CAW log 或你能截图展示 CAW app/log。

## 阶段 3：真实 GLM-5.1 长程任务

任务：

1. 设置 Z.AI：
   - `LLM_MODE=real`
   - `ZAI_API_KEY`
   - `ZAI_BASE_URL`
   - `ZAI_MODEL=glm-5.1`
2. 让 Worker Agent 输出结构化 JSON：
   - plan
   - finding
   - patch diff
   - tests to run
   - retry notes
3. 添加真实命令工具：
   - `forge test`
   - 可选：`slither .`
4. 如果测试失败，让 Worker Agent 读取错误并重试一次。

完成标准：

- Trace 里能看到“计划 → 修改 → 测试失败/成功 → 修复 → 复测 → 交付”。
- 即使模型失败，也能 fallback，不影响最终演示。

## 阶段 4：前端打磨

任务：

1. 把 Mock 地址替换为真实测试网地址。
2. 增加 explorer link。
3. 增加 CAW Pact 状态卡片。
4. 增加 Demo 模式开关：Mock / Real。
5. 增加一键导出 evidence JSON。

完成标准：

- 评委不用看终端，也能理解：谁发包、谁托管、谁交付、谁验收、谁收款、谁被拒绝。

## 阶段 5：提交材料

必须提交：

- GitHub Repo
- README
- Demo 视频 3–5 分钟
- 项目说明文档
- 测试网合约地址
- tx hash
- Agent Wallet 地址
- CAW 使用说明和关键代码位置
- CAW denial 截图或 log

README 里要显眼列出：

```text
Where CAW is used:
- submit_pact
- get_pact
- contract_call: approve
- contract_call: createJob
- contract_call: setBudget
- contract_call: fund
- contract_call: submit
- contract_call: complete
- transfer denied by policy
- audit logs
```

## Demo Day 问答准备

### Q: 为什么一定需要 CAW？

答：因为 Agent 不应该拿私钥，也不能靠 prompt 自律。CAW 让 Agent 只能在 owner 审批的 Pact 边界内操作，越界自动拒绝。

### Q: 这和普通 escrow 有什么区别？

答：普通 escrow 假设人类操作。PactBounty 的核心是 Agent 自主触发资金流程：发包、托管、提交、验收、付款，同时每步都受钱包权限控制。

### Q: Worker Agent 作恶怎么办？

答：Worker 不能碰托管资金，只能提交 deliverable hash。Evaluator 验收失败会 reject/refund。Worker 的权限面只有 `submit()`。

### Q: Evaluator 作恶怎么办？

答：MVP 中 evaluator 是被 client 指定的可信角色。下一步会加入多 evaluator、stake/reputation、DAO arbitration。

### Q: 为什么不是做 trading agent？

答：交易收益不稳定，风险边界难讲。PactBounty 的资金闭环稳定、可复现，而且更直接命中 Agentic Commerce。

## 加分路线

1. **x402 Resource Procurement**  
   Worker 收款后，用 CAW 支付一个 x402 API 获取漏洞情报/checklist，展示“赚钱 → 花钱 → 更好交付”。

2. **Reputation**  
   完成 job 后给 Worker 记录 score / completed jobs。

3. **Multi-agent Auction**  
   多个 Worker Agent bid，Client Agent 选择最高性价比。

4. **DAO Treasury Mode**  
   DAO Treasury 作为 Client，Agent 自动发包给审计/研究/运营 Worker。
