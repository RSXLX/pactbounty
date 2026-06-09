// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title PatchedVault
/// @notice Simple patched version used as the expected Worker Agent output.
contract PatchedVault {
    mapping(address => uint256) public balances;
    bool private locked;

    error NoBalance();
    error TransferFailed();
    error ReentrantCall();

    modifier nonReentrant() {
        if (locked) revert ReentrantCall();
        locked = true;
        _;
        locked = false;
    }

    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }

    function withdraw() external nonReentrant {
        uint256 amount = balances[msg.sender];
        if (amount == 0) revert NoBalance();

        // Checks-effects-interactions: update state before external call.
        balances[msg.sender] = 0;
        (bool ok,) = msg.sender.call{value: amount}("");
        if (!ok) revert TransferFailed();
    }
}
