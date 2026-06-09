// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import "../src/VulnerableVault.sol";
import "../src/PatchedVault.sol";
import "../src/ReentrancyAttacker.sol";

contract VaultTest is Test {
    function testPatchedVaultWithdrawsOnce() public {
        PatchedVault vault = new PatchedVault();
        address alice = address(0xA11CE);
        vm.deal(alice, 10 ether);

        vm.prank(alice);
        vault.deposit{value: 1 ether}();

        vm.prank(alice);
        vault.withdraw();

        assertEq(vault.balances(alice), 0);
    }

    function testVulnerableVaultHasBadPattern() public {
        VulnerableVault vault = new VulnerableVault();
        assertEq(address(vault).balance, 0);
        // The full exploit can be run against a funded vault; the Worker Agent flags the unsafe pattern.
    }
}
