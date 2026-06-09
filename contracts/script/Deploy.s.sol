// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Script.sol";
import "../src/MockUSDC.sol";
import "../src/AgenticCommerce.sol";
import "../src/VulnerableVault.sol";
import "../src/PatchedVault.sol";

contract Deploy is Script {
    function run() external returns (MockUSDC mockUsdc, AgenticCommerce commerce, VulnerableVault vulnerable, PatchedVault patched) {
        address client = vm.envOr("CLIENT_AGENT_WALLET", msg.sender);
        address worker = vm.envOr("WORKER_AGENT_WALLET", msg.sender);
        uint256 deployerKey = vm.envUint("PRIVATE_KEY");

        vm.startBroadcast(deployerKey);
        mockUsdc = new MockUSDC();
        commerce = new AgenticCommerce();
        vulnerable = new VulnerableVault();
        patched = new PatchedVault();

        mockUsdc.mint(client, 100_000_000); // 100 mUSDC, 6 decimals
        mockUsdc.mint(worker, 10_000_000);  // 10 mUSDC for follow-on agent spending demos
        vm.stopBroadcast();

        console2.log("MockUSDC", address(mockUsdc));
        console2.log("AgenticCommerce", address(commerce));
        console2.log("VulnerableVault", address(vulnerable));
        console2.log("PatchedVault", address(patched));
        console2.log("Client funded", client);
        console2.log("Worker funded", worker);
    }
}
