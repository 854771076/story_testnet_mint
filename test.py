from tools import *
from datetime import datetime, timezone
import requests
from fake_useragent import UserAgent
web3tool=Web3Tool(rpc_url='https://testnet.storyrpc.io',chain_id=1513)
web3=web3tool.web3
# 假设这是从交易回执中获得的 revert 数据
revert_data = '0x08c379a00000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000b21434f4e444954494f4e2e000000000000000000000000000000000000000000'
web3 = Web3()
error_message = web3.codec.decode_error(revert_data)
print(error_message)