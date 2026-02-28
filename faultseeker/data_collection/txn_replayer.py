import os
import subprocess



class TransactionReplayer:

    def __init__(self, cache_path='./data/cache/replay'):
        """Initialize TransactionReplayer with cache directory."""
        self.cache_path = cache_path
        os.makedirs(cache_path, exist_ok=True)

    @staticmethod
    def transaction_replay(txn_hash, chain):
        """Execute transaction replay using cast command."""
        command = ["cast", "run", "--quick", txn_hash, '--rpc-url', chain]
        
        print(' '.join(command))
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=7200)
            return result.stdout
        except Exception:
            import traceback
            traceback.print_exc()
            return None

    def get_replay_cache(self, txn_hash):
        """Check if replay result exists in cache."""
        cache_file = os.path.join(self.cache_path, txn_hash.lower() + '.txt')
        if os.path.exists(cache_file):
            return open(cache_file, 'r', encoding='utf-8').read()
        return None

    def cache_replay(self, txn_hash, invocation_flow):
        """Cache replay result to disk."""
        with open(os.path.join(self.cache_path, txn_hash.lower() + '.txt'), 'w') as f:
            f.write(invocation_flow)

    def run(self, txn_hash: str, chain: str) -> str:
        """
        Run transaction replay for given transaction hash and chain.

        Args:
            txn_hash: Transaction hash
            chain: Chain identifier (eth, bsc, poly, etc.)

        Returns:
            Transaction replay trace text
        """
        # Check cache first
        invocation_flow = self.get_replay_cache(txn_hash)
        if invocation_flow:
            return invocation_flow

        # Run replay and cache result
        invocation_flow = self.transaction_replay(txn_hash, chain)
        if invocation_flow:
            self.cache_replay(txn_hash, invocation_flow)

        return invocation_flow



