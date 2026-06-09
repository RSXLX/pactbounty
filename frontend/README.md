# Frontend

Next.js dashboard for the PactBounty demo.

```bash
cd frontend
npm install
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

Open `http://localhost:3000` and click **Run Full Demo**.

The dashboard shows:

- CAW pacts
- job state
- balances for Client / Worker / Evaluator / Escrow
- agent execution trace
- CAW audit logs
- denied out-of-policy transfer proof
