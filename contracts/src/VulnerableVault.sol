// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title VulnerableVault
/// @notice Intentionally vulnerable contract for the PactBounty demo.
contract VulnerableVault {
    mapping(address => uint256) public balances;

    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }

    function withdraw() external {
        uint256 amount = balances[msg.sender];
        require(amount > 0, "no balance");

        // VULNERABILITY: external call before state update enables reentrancy.
        (bool ok,) = msg.sender.call{value: amount}("");
        require(ok, "send failed");

        balances[msg.sender] = 0;
    }
}
