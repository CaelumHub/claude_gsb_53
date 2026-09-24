import unittest

from backend import crypto
from backend.contract import ContractEngine
from backend.state import WorldState
from backend.transaction import Transaction, TX_TRANSFER
from backend.txpool import TxPool
from backend.blockchain import Blockchain


CONTRACT_ADDRESS = "0xc" + "11" * 20
OWNER_ADDRESS = "0x" + "22" * 20
RECIPIENT_ADDRESS = "0x" + "33" * 20

PAYOUT_CONTRACT = """
def payout(to):
    transfer(to, 1)
"""


class AddressValidationTest(unittest.TestCase):
    def test_contract_transfer_rejects_invalid_recipient(self):
        state = WorldState()
        state.create_contract(CONTRACT_ADDRESS, PAYOUT_CONTRACT, OWNER_ADDRESS)
        state.set_balance(CONTRACT_ADDRESS, 5)

        result = ContractEngine({}).invoke(
            CONTRACT_ADDRESS, "payout", ["not-a-valid-address"],
            OWNER_ADDRESS, 0, state,
        )

        self.assertFalse(result["ok"])
        self.assertIn("valid address", result["error"])
        self.assertEqual(state.balance(CONTRACT_ADDRESS), 5)
        self.assertNotIn("not-a-valid-address", state.accounts)
        self.assertEqual(result["transfers"], [])

    def test_contract_transfer_allows_well_formed_recipient(self):
        state = WorldState()
        state.create_contract(CONTRACT_ADDRESS, PAYOUT_CONTRACT, OWNER_ADDRESS)
        state.set_balance(CONTRACT_ADDRESS, 5)

        result = ContractEngine({}).invoke(
            CONTRACT_ADDRESS, "payout", [RECIPIENT_ADDRESS],
            OWNER_ADDRESS, 0, state,
        )

        self.assertTrue(result["ok"], result["error"])
        self.assertEqual(state.balance(CONTRACT_ADDRESS), 4)
        self.assertEqual(state.balance(RECIPIENT_ADDRESS), 1)
        self.assertEqual(result["transfers"],
                         [{"to": RECIPIENT_ADDRESS, "amount": 1.0}])

    def test_txpool_rejects_invalid_transfer_recipient(self):
        private_key = crypto.generate_private_key()
        sender = crypto.address_from_private_key(private_key)
        state = WorldState()
        state.set_balance(sender, 10)

        tx = Transaction(sender, "not-a-valid-address", 5, 0, 0, TX_TRANSFER)
        tx.sign_with(private_key)

        ok, reason = TxPool().validate(tx, state)
        self.assertFalse(ok)
        self.assertIn("address", reason)
        self.assertNotIn("not-a-valid-address", state.accounts)

    def test_transaction_execution_rejects_invalid_recipient(self):
        private_key = crypto.generate_private_key()
        sender = crypto.address_from_private_key(private_key)
        state = WorldState()
        state.set_balance(sender, 10)

        tx = Transaction(sender, "not-a-valid-address", 5, 0, 0, TX_TRANSFER)
        tx.sign_with(private_key)

        chain = Blockchain({}, None)
        state, receipt = chain._execute_transaction(
            tx, state, "0x" + "00" * 20, 1,
        )

        self.assertFalse(receipt["ok"])
        self.assertIn("address", receipt["error"])
        self.assertEqual(state.balance(sender), 10)
        self.assertNotIn("not-a-valid-address", state.accounts)


if __name__ == "__main__":
    unittest.main()
