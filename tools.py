from web3 import Web3
from web3.exceptions import ContractLogicError
import requests
from loguru import logger
from eth_account.messages import encode_defunct
from concurrent.futures import ThreadPoolExecutor, as_completed
from loguru import logger
import uuid
from glob import glob
import os,time
import pandas as pd
import json
namespace = uuid.NAMESPACE_DNS
url_name = 'faucet.story.foundation'

logger.add(
    "logs/Story_TestNet_Bot.log"
)

from web3 import Web3
from web3.exceptions import ContractLogicError
import requests
from eth_account.messages import encode_defunct
class Web3Tool:
    def __init__(self, rpc_url='https://rpc.ankr.com/eth/b1fc516a781c5a470a4195b770e47877bd0c976cc3f5791b0e90387b217cd866',chain_id=1,explorer=None, private_key=None):
        """
        初始化 Web3Tool 类实例
        
        :param rpc_url: 以太坊节点的 RPC URL
        :param private_key: （可选）用于发送交易的私钥
        """
        self.web3 = Web3(Web3.HTTPProvider(rpc_url))
        self.chain_id=chain_id
        self.explorer=explorer
        if not self.web3.is_connected():
            raise ConnectionError(f"无法连接到节点 {rpc_url}")
        
        self.private_key = private_key
        if private_key:
            self.account = self.web3.eth.account.from_key(private_key)
        else:
            self.account = None
        
    def get_contract_transaction_gas_limit(self,func,address):
        '''
        估算所需的 gas
        '''
        max_fee_cap = Web3.to_wei(100, 'ether')
        gas_estimate = func.estimate_gas({
        'from': address
        })
        # 获取当前 gas 价格
        gas_price = self.web3.eth.gas_price
        # 获取账户余额
        balance = self.web3.eth.get_balance(address)
        # 计算总费用
        total_cost = gas_estimate * gas_price
        # 判断 gas 或转账是否合理
        if total_cost > balance:
            ValueError('gas不足改日领水后重试')
        if total_cost > max_fee_cap:
            # 如果超出上限，调整费用为 1 ETH
            gas_estimate = max_fee_cap / gas_price
            gas_estimate = int(gas_estimate)  # 将价格转换为整数
        # 返回估算的 gas
        return gas_estimate
    def run_contract(self, func, address,private_key,value=None):
        '''
        执行合约
        '''
        try:
            checksum_address = self.web3.to_checksum_address(address)
            try:
                gas_limit = self.get_contract_transaction_gas_limit(func,checksum_address )
            except:
                gas_limit=500000
            nonce = self.web3.eth.get_transaction_count(checksum_address)
            if value:
                transaction = func.build_transaction({
                'chainId': self.chain_id,
                'gas': int(gas_limit),
                'gasPrice': int(self.web3.eth.gas_price),
                'value':self.web3.to_wei(value, 'ether'),
                'nonce': nonce
                })
            else:
                transaction = func.build_transaction({
                    'chainId': self.chain_id,
                    'gas': int(gas_limit),
                    'gasPrice': int(self.web3.eth.gas_price),
                    'nonce': nonce
                })
            signed_transaction = self.web3.eth.account.sign_transaction(transaction, private_key=private_key)
            
            # 确保网络已准备好接收
            tx_hash = self.web3.eth.send_raw_transaction(signed_transaction.rawTransaction)
            
            # 等待交易被挖矿
            try:
                status = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            except Exception as e:
                
                logger.warning(f"Error waiting for transaction receipt: {e}")
                return tx_hash, False

            return tx_hash, status.status
        except Exception as e:
            if 'nonce too low' in str(e):
                return None, True
            raise TimeoutError(f"Error in running contract function: {e}")
    
    def get_ERC20_balance(self,address,type='ERC-20'):
        '''
        获取钱包余额
        '''
        # 获取账户余额（单位是 Wei）
        balance={}
        balance_wei = self.web3.eth.get_balance(address)
        # 将余额从 Wei 转换为 Ether
        balance_ether = self.web3.from_wei(balance_wei, 'ether')
        balance['ETH']=round(float(balance_ether),5)
        if self.explorer:
            response = requests.get(f'{self.explorer}/api/v2/addresses/{address}/tokens', params={
                'type': type,
            })
            data=response.json().get('items',[])
            
            for token in data:
                balance[token['token']['symbol']]=round(int(token['value'])/(10**int(token['token']['decimals'])),5)
        return balance
    def get_conn(self):
        return self.web3
    def set_private_key(self,private_key):
        if private_key:
            self.account = self.web3.eth.account.from_key(private_key)
    def get_balance(self, address):
        """
        获取指定地址的余额
        
        :param address: 以太坊地址
        :return: 以太币为单位的余额
        """
        balance_wei = self.web3.eth.get_balance(address)
        return self.web3.from_wei(balance_wei, 'ether')
    
    def send_transaction(self, to_address, value_in_ether, gas=21000, gas_price=None):
        """
        发送以太币交易
        
        :param to_address: 接收方地址
        :param value_in_ether: 发送的以太币数量
        :param gas: 燃气上限
        :param gas_price: 燃气价格（可选）
        :return: 交易哈希
        """
        if not self.account:
            raise ValueError("私钥未设置，无法发送交易")
        
        value_wei = self.web3.to_wei(value_in_ether, 'ether')
        tx = {
            'to': to_address,
            'value': value_wei,
            'gas': gas,
            'gasPrice': gas_price or self.web3.eth.gas_price,
            'nonce': self.web3.eth.get_transaction_count(self.account.address),
        }

        signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return self.web3.to_hex(tx_hash)
    
    def deploy_contract(self, compiled_contract, constructor_args=()):
        """
        部署智能合约
        
        :param compiled_contract: 编译后的合约对象（ABI 和 Bytecode）
        :param constructor_args: 构造函数的参数
        :return: 合约地址
        """
        if not self.account:
            raise ValueError("私钥未设置，无法部署合约")
        
        contract = self.web3.eth.contract(abi=compiled_contract['abi'], bytecode=compiled_contract['bytecode'])
        tx = contract.constructor(*constructor_args).build_transaction({
            'from': self.account.address,
            'nonce': self.web3.eth.get_transaction_count(self.account.address),
            'gas': 3000000,
            'gasPrice': self.web3.eth.gas_price,
        })

        signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

        return tx_receipt.contractAddress
    
    def load_contract(self, address, abi):
        """
        加载已部署的智能合约
        
        :param address: 合约地址
        :param abi: 合约的 ABI
        :return: 合约对象
        """
        return self.web3.eth.contract(address=address, abi=abi)
    
    def call_contract_function(self, contract, function_name, *args):
        """
        调用智能合约的只读方法
        
        :param contract: 合约对象
        :param function_name: 合约方法名称
        :param args: 合约方法参数
        :return: 方法的返回值
        """
        try:
            func = contract.functions[function_name](*args)
            return func.call()
        except ContractLogicError as e:
            print(f"合约方法调用错误: {e}")
            return None
    
    def send_contract_transaction(self, contract, function_name, *args, gas=300000, gas_price=None):
        """
        调用智能合约的修改状态方法并发送交易
        
        :param contract: 合约对象
        :param function_name: 合约方法名称
        :param args: 合约方法参数
        :param gas: 燃气上限
        :param gas_price: 燃气价格（可选）
        :return: 交易哈希
        """
        if not self.account:
            raise ValueError("私钥未设置，无法发送交易")

        func = contract.functions[function_name](*args)
        tx = func.buildTransaction({
            'from': self.account.address,
            'nonce': self.web3.eth.get_transaction_count(self.account.address),
            'gas': gas,
            'gasPrice': gas_price or self.web3.eth.gas_price,
        })

        signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return self.web3.toHex(tx_hash)
    def sign_msg(self,private_key,msg):
        '''
        钱包签名
        '''
        # 使用web3.py编码消息
        message_encoded = encode_defunct(text=msg)
        # 签名消息
        signed_message = self.web3.eth.account.sign_message(message_encoded,private_key)
        # 打印签名的消息
        return signed_message.signature.hex()
    def get_NFTs(self,address):
        '''
        获取NFT列表
        '''
        # 获取账户余额（单位是 Wei）
        balance={}
        response = requests.get(f'{self.explorer}/api/v2/addresses/{address}/nft/collections', params={'type':''})
        data=response.json().get('items',[])
        for token in data:
            balance[token['token']['symbol']]={'id':int(token['token_instances'][0]['id']),'amount':int(token['amount'])}
        return balance
    def generate_wallet(self):
        '''
        生成钱包
        '''
        # 生成新账户
        account = self.web3.eth.account.create()
        # 获取地址和私钥
        address = account.address
        try:
            private_key = account.privateKey.hex()
        except:
            private_key = account._private_key.hex()
        return address,private_key
if __name__=='__main__':
    t=Web3Tool()
    print(t.get_balance('0x3da9B8Bab17df9794A859EA7f195Dc66a89888AF'))