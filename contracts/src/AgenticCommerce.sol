// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IERC20Like {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}

/// @title AgenticCommerce
/// @notice ERC-8183-inspired escrow primitive for agent-to-agent work agreements.
/// @dev This is a hackathon-grade reference implementation, not a production audit target.
contract AgenticCommerce {
    enum JobState {
        Open,
        Funded,
        Submitted,
        Completed,
        Rejected,
        Refunded
    }

    struct Job {
        address client;
        address provider;
        address evaluator;
        address token;
        uint256 budget;
        uint256 escrowed;
        uint64 expiredAt;
        bytes32 descriptionHash;
        bytes32 deliverableHash;
        bytes32 reasonHash;
        JobState state;
    }

    uint256 public nextJobId = 1;
    mapping(uint256 => Job) public jobs;

    event JobCreated(
        uint256 indexed jobId,
        address indexed client,
        address indexed provider,
        address evaluator,
        address token,
        uint64 expiredAt,
        bytes32 descriptionHash
    );
    event BudgetSet(uint256 indexed jobId, uint256 budget);
    event JobFunded(uint256 indexed jobId, uint256 amount);
    event WorkSubmitted(uint256 indexed jobId, bytes32 deliverableHash);
    event JobCompleted(uint256 indexed jobId, bytes32 reasonHash, uint256 paidAmount);
    event JobRejected(uint256 indexed jobId, bytes32 reasonHash, uint256 refundedAmount);
    event JobRefunded(uint256 indexed jobId, uint256 refundedAmount);

    error InvalidAddress();
    error InvalidState(JobState expected, JobState actual);
    error NotClient();
    error NotProvider();
    error NotEvaluator();
    error NotClientOrProvider();
    error Expired();
    error NotExpired();
    error BudgetMismatch();
    error TransferFailed();

    function createJob(
        address provider,
        address evaluator,
        address token,
        uint64 expiredAt,
        bytes32 descriptionHash
    ) external returns (uint256 jobId) {
        if (provider == address(0) || evaluator == address(0) || token == address(0)) revert InvalidAddress();
        if (expiredAt <= block.timestamp) revert Expired();

        jobId = nextJobId++;
        jobs[jobId] = Job({
            client: msg.sender,
            provider: provider,
            evaluator: evaluator,
            token: token,
            budget: 0,
            escrowed: 0,
            expiredAt: expiredAt,
            descriptionHash: descriptionHash,
            deliverableHash: bytes32(0),
            reasonHash: bytes32(0),
            state: JobState.Open
        });

        emit JobCreated(jobId, msg.sender, provider, evaluator, token, expiredAt, descriptionHash);
    }

    function setBudget(uint256 jobId, uint256 amount) external {
        Job storage job = jobs[jobId];
        _requireState(job, JobState.Open);
        if (msg.sender != job.client && msg.sender != job.provider) revert NotClientOrProvider();
        job.budget = amount;
        emit BudgetSet(jobId, amount);
    }

    function fund(uint256 jobId, uint256 expectedBudget) external {
        Job storage job = jobs[jobId];
        _requireState(job, JobState.Open);
        if (msg.sender != job.client) revert NotClient();
        if (block.timestamp >= job.expiredAt) revert Expired();
        if (job.budget == 0 || job.budget != expectedBudget) revert BudgetMismatch();

        job.escrowed = job.budget;
        job.state = JobState.Funded;
        bool ok = IERC20Like(job.token).transferFrom(msg.sender, address(this), job.budget);
        if (!ok) revert TransferFailed();

        emit JobFunded(jobId, job.budget);
    }

    function submit(uint256 jobId, bytes32 deliverableHash) external {
        Job storage job = jobs[jobId];
        _requireState(job, JobState.Funded);
        if (msg.sender != job.provider) revert NotProvider();
        if (block.timestamp >= job.expiredAt) revert Expired();
        job.deliverableHash = deliverableHash;
        job.state = JobState.Submitted;
        emit WorkSubmitted(jobId, deliverableHash);
    }

    function complete(uint256 jobId, bytes32 reasonHash) external {
        Job storage job = jobs[jobId];
        _requireState(job, JobState.Submitted);
        if (msg.sender != job.evaluator) revert NotEvaluator();
        job.reasonHash = reasonHash;
        job.state = JobState.Completed;
        uint256 amount = job.escrowed;
        job.escrowed = 0;
        bool ok = IERC20Like(job.token).transfer(job.provider, amount);
        if (!ok) revert TransferFailed();
        emit JobCompleted(jobId, reasonHash, amount);
    }

    function reject(uint256 jobId, bytes32 reasonHash) external {
        Job storage job = jobs[jobId];
        uint256 refundAmount = job.escrowed;

        if (job.state == JobState.Open) {
            if (msg.sender != job.client) revert NotClient();
        } else if (job.state == JobState.Funded || job.state == JobState.Submitted) {
            if (msg.sender != job.evaluator) revert NotEvaluator();
        } else {
            revert InvalidState(JobState.Open, job.state);
        }

        job.reasonHash = reasonHash;
        job.escrowed = 0;
        job.state = JobState.Rejected;
        if (refundAmount > 0) {
            bool ok = IERC20Like(job.token).transfer(job.client, refundAmount);
            if (!ok) revert TransferFailed();
        }
        emit JobRejected(jobId, reasonHash, refundAmount);
    }

    function claimRefund(uint256 jobId) external {
        Job storage job = jobs[jobId];
        if (job.state != JobState.Funded && job.state != JobState.Submitted) {
            revert InvalidState(JobState.Funded, job.state);
        }
        if (block.timestamp < job.expiredAt) revert NotExpired();
        uint256 refundAmount = job.escrowed;
        job.escrowed = 0;
        job.state = JobState.Refunded;
        bool ok = IERC20Like(job.token).transfer(job.client, refundAmount);
        if (!ok) revert TransferFailed();
        emit JobRefunded(jobId, refundAmount);
    }

    function getJob(uint256 jobId) external view returns (Job memory) {
        return jobs[jobId];
    }

    function _requireState(Job storage job, JobState expected) internal view {
        if (job.state != expected) revert InvalidState(expected, job.state);
    }
}
