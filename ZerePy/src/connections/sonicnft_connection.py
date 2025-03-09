import os
import logging
from typing import Dict, Any, List
from web3 import Web3
from eth_account import Account
from eth_account.signers.local import LocalAccount
from src.connections.base_connection import BaseConnection, Action, ActionParameter
from src.helpers import print_h_bar
from dotenv import load_dotenv, set_key

logger = logging.getLogger("connections.sonic_connection")

# NFT Contract ABI (simplified for example)
NFT_ABI = [
    {
        "inputs": [
            {"internalType": "string", "name": "tokenURI", "type": "string"}
        ],
        "name": "mintNFT",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "tokenURI",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    }
]

class SonicConnectionError(Exception):
    """Base exception for Sonic connection errors"""
    pass

class SonicnftConnection(BaseConnection):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.w3 = None
        self.account = None
        self.contract = None
        self._initialize_connection()

    @property
    def is_llm_provider(self) -> bool:
        return False

    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Sonic configuration"""
        required_fields = ["chain_id", "rpc_url", "nft_contract"]
        missing_fields = [field for field in required_fields if field not in config]
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
            
        return config

    def _initialize_connection(self):
        """Initialize Web3 connection"""
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.config["rpc_url"]))
            if not self.w3.is_connected():
                raise SonicConnectionError("Could not connect to Sonic network")
                
            # Load private key if available
            load_dotenv()
            private_key = os.getenv("SONIC_PRIVATE_KEY")
            if private_key:
                self.account = Account.from_key(private_key)
                
            # Initialize NFT contract
            self.contract = self.w3.eth.contract(
                address=self.config["nft_contract"],
                abi=NFT_ABI
            )
        except Exception as e:
            raise SonicConnectionError(f"Failed to initialize connection: {e}")

    def register_actions(self) -> None:
        """Register available Sonic blockchain actions"""
        self.actions = {
            "mint-nft": Action(
                name="mint-nft",
                parameters=[
                    ActionParameter("token_uri", True, str, "IPFS URI of the NFT metadata"),
                    ActionParameter("name", True, str, "Name of the NFT"),
                    ActionParameter("description", True, str, "Description of the NFT")
                ],
                description="Mint a new NFT"
            ),
            "get-nft": Action(
                name="get-nft",
                parameters=[
                    ActionParameter("token_id", True, int, "Token ID of the NFT")
                ],
                description="Get NFT details"
            ),
            "upload-to-ipfs": Action(
                name="upload-to-ipfs",
                parameters=[
                    ActionParameter("file_path", True, str, "Path to the file"),
                    ActionParameter("name", True, str, "Name of the file"),
                    ActionParameter("description", True, str, "Description of the file")
                ],
                description="Upload file to IPFS"
            )
        }

    def configure(self) -> bool:
        """Configure Sonic blockchain connection"""
        logger.info("\n🔗 Sonic Blockchain Setup")
        
        if self.is_configured():
            logger.info("Sonic connection is already configured.")
            response = input("Do you want to reconfigure? (y/n): ")
            if response.lower() != "y":
                return True

        try:
            private_key = input("\nEnter your Sonic private key: ")
            
            # Validate private key
            try:
                account = Account.from_key(private_key)
                logger.info(f"\nAccount address: {account.address}")
            except Exception as e:
                raise SonicConnectionError(f"Invalid private key: {e}")

            # Save to .env
            if not os.path.exists('.env'):
                with open('.env', 'w') as f:
                    f.write('')
                    
            set_key('.env', 'SONIC_PRIVATE_KEY', private_key)
            
            self._initialize_connection()
            logger.info("\n✅ Sonic blockchain connection configured successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Configuration failed: {e}")
            return False

    def is_configured(self, verbose=False) -> bool:
        """Check if Sonic connection is configured"""
        try:
            load_dotenv()
            return bool(os.getenv("SONIC_PRIVATE_KEY"))
        except Exception as e:
            if verbose:
                logger.error(f"Configuration check failed: {e}")
            return False

    def mint_nft(self, token_uri: str, name: str, description: str) -> Dict[str, Any]:
        """Mint a new NFT"""
        if not self.account:
            raise SonicConnectionError("No account configured")
            
        try:
            # Prepare transaction
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            tx = self.contract.functions.mintNFT(token_uri).build_transaction({
                'chainId': int(self.config["chain_id"]),
                'gas': 2000000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': nonce,
            })
            
            # Sign and send transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for transaction receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return {
                'transaction_hash': receipt['transactionHash'].hex(),
                'token_id': receipt['logs'][0]['topics'][3],  # Assuming this is where token ID is
                'name': name,
                'description': description,
                'token_uri': token_uri
            }
            
        except Exception as e:
            raise SonicConnectionError(f"Failed to mint NFT: {e}")

    def get_nft(self, token_id: int) -> Dict[str, Any]:
        """Get NFT details"""
        try:
            token_uri = self.contract.functions.tokenURI(token_id).call()
            return {
                'token_id': token_id,
                'token_uri': token_uri
            }
        except Exception as e:
            raise SonicConnectionError(f"Failed to get NFT: {e}")

    def upload_to_ipfs(self, file_path: str, name: str, description: str) -> str:
        """Upload file to IPFS and return URI"""
        # Note: This is a placeholder. You'll need to implement actual IPFS upload
        # using a service like Pinata or run your own IPFS node
        raise NotImplementedError("IPFS upload not implemented yet")