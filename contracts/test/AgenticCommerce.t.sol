// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import "../src/MockUSDC.sol";
import "../src/AgenticCommerce.sol";

contract AgenticCommerceTest is Test {
    MockUSDC token;
    AgenticCommerce commerce;

    address client = address(0xA11CE);
    address provider = address(0xB0B);
    address evaluator = address(0xEVAL);

    function setUp() public {
        token = new MockUSDC();
        commerce = new AgenticCommerce();
        token.mint(client, 100_000_000);
    }

    function testHappyPath() public {
        uint256 amount = 5_000_000;
        bytes32 descriptionHash = keccak256("audit VulnerableVault");
        bytes32 deliverableHash = keccak256("report + patch");
        bytes32 reasonHash = keccak256("tests passed");

        vm.startPrank(client);
        token.approve(address(commerce), amount);
        uint256 jobId = commerce.createJob(provider, evaluator, address(token), uint64(block.timestamp + 1 days), descriptionHash);
        commerce.setBudget(jobId, amount);
        commerce.fund(jobId, amount);
        vm.stopPrank();

        assertEq(token.balanceOf(address(commerce)), amount);

        vm.prank(provider);
        commerce.submit(jobId, deliverableHash);

        vm.prank(evaluator);
        commerce.complete(jobId, reasonHash);

        assertEq(token.balanceOf(provider), amount);
        assertEq(token.balanceOf(address(commerce)), 0);
        AgenticCommerce.Job memory job = commerce.getJob(jobId);
        assertEq(uint256(job.state), uint256(AgenticCommerce.JobState.Completed));
    }

    function testOnlyEvaluatorCanComplete() public {
        uint256 amount = 5_000_000;
        vm.startPrank(client);
        token.approve(address(commerce), amount);
        uint256 jobId = commerce.createJob(provider, evaluator, address(token), uint64(block.timestamp + 1 days), keccak256("desc"));
        commerce.setBudget(jobId, amount);
        commerce.fund(jobId, amount);
        vm.stopPrank();

        vm.prank(provider);
        commerce.submit(jobId, keccak256("deliverable"));

        vm.prank(client);
        vm.expectRevert(AgenticCommerce.NotEvaluator.selector);
        commerce.complete(jobId, keccak256("bad actor"));
    }
}
